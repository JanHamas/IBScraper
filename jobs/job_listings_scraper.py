import asyncio, random, re, os
from playwright_stealth import Stealth
from playwright.async_api import async_playwright

from config import config_input
from utils.bypass.cloudflare import CloudflareBypasser
from utils import accounts_loader, fingerprint_loader, proxies_loader, helper
from .job_details_scraper import extract_full_details
from utils.logger_setup import setup_logger


logger = setup_logger(log_file="jobs_lister.log")

# Avoid Duplicate
processed_jobs_id = helper.load_processed_jobs_id()
processed_new_company_jobs = []


async def _listing(context, job_page_url):
    page = None
    
    try:
        # Open job page
        page = await context.new_page()
        # Try to load page twice
        try:
            await page.goto(job_page_url, wait_until="load")
        except Exception:
            logger.warning(f"Retry loading page: {job_page_url}")
            await page.goto(job_page_url, wait_until="load")

        # Cloudflare bypass
        try:
            cf_bypasser = CloudflareBypasser(page)
            await cf_bypasser.detect_and_bypass()
        except Exception as e:
            logger.error(f"Error handling captch: {e}")

        # Setup data holders
        list_of_processed_jobs = []
        list_of_company = []
        list_of_titles = []
        list_of_links = []
        pagination_number = 1

        while True:
            await page.wait_for_timeout(random.randint(3000, 10000))
            await asyncio.sleep(random.randint(1, 3))
            await helper.simulate_human_behavior(page)

            try:
                titles_task = page.query_selector_all(".jobTitle")
                companies_task = page.query_selector_all("[data-testid='company-name']")
                links_task = page.query_selector_all("tr td a")
                titles, companies, links = await asyncio.gather(titles_task, companies_task, links_task)
            except Exception as e:
                logger.error("Error in selectors: {e}")
                break

            for title, company, link in zip(titles, companies, links):
                link = await link.get_attribute("href")
                if not link:
                    continue

                list_of_processed_jobs.append(link)
                job_id = await helper.get_job_id(link)
                if not job_id:
                    continue
                title_text = await title.inner_text()
                company = await company.inner_text()
                count = processed_new_company_jobs.count(company)

                if (
                    count > config_input.PER_COMPANY_JOBS
                    or job_id in processed_jobs_id
                    or company in config_input.ignore_companies
                ):
                    continue

                processed_jobs_id.add(job_id)
                processed_new_company_jobs.append(company)
                list_of_titles.append(title_text)
                list_of_company.append(company)
                list_of_links.append(link)

                if len(list_of_titles) % 5 == 0:
                    logger.info(f"Collected {len(list_of_titles)} job so far...")

                if len(list_of_titles) >= config_input.PROCESS_BATCH_SIZE:
                    logger.info("Processing batch...")
                    await process_batch(context, list_of_titles, list_of_links)
                    list_of_titles.clear()
                    list_of_company.clear()
                    list_of_links.clear()
                    await helper.update_processed_jobs(list_of_processed_jobs)
                    list_of_processed_jobs.clear()

            # Try to click next page
            try:
                button_locator = page.locator(f"[data-testid='pagination-page-{pagination_number + 1}']")
                if await button_locator.is_visible(timeout=10000):
                    await button_locator.click(timeout=10000)
                    pagination_number += 1
                else:
                    filename = f"screenshot_{pagination_number}.png"
                    file_path = os.path.join(config_input.DEBUGGING_SCREENSHOTS_PATH, filename)
                    await page.screenshot(path=file_path, full_page=True)
                    logger.info(f"No more pages. Saved screenshot: {file_path}")
                    break
            except Exception as e:
                logger.warning(f"Failed to click  page {pagination_number + 1}: {e}")
                break

        # Final cleanup if any jobs are remaining in buffer
        if list_of_titles:
            await process_batch(context, list_of_titles, list_of_links)
            await helper.update_processed_jobs(list_of_processed_jobs)

    except Exception as e:
        print(f"❌ Unexpected error in _listing: {e}")
        logger.critical(f" Unexpected error in _listing: {e}")
    finally:
        try:
            if page: await page.close()
            await context.close()
            logger.debug("Context closed successfully")
        except Exception as e:
            logger.error(f"Error during context/pages close: {e}")

async def process_batch(context, list_of_titles, list_of_links):
    # Create first complete prompt
    prompt =f""" 
{config_input.AI_PROMPT}\n
{config_input.RESUME}\n
Jobs Titles:
{list_of_titles}
    """
    logger.debug(f"Prompt sent to model: {prompt}")
    # Call model function for providing matching %
    try:
        model_response = await helper.get_match_percentage(prompt)
        logger.info(f"Modle response: {model_response}")

        matching_percentages = re.findall(r'\b\d+\b', model_response)  # Extracts all numbers
        matching_percentages = list(map(int, matching_percentages))

        links_list = []
        percentages = []
        for percentage, link in zip(matching_percentages, list_of_links):
            if percentage >= config_input.MATCHING_PERCENTAGE:
                links_list.append(link)
                percentages.append(percentage)
        # this one function will be scrap detail about each job 
        if len(links_list) >= 1:
            await extract_full_details(context, links_list, percentages)

    except Exception as e:
        logger.error(f"Error in process_batch: {e}")
        await context.close()
    
async def jobs_lister():
    """"
    This one function will be open all jobs listed pages on indeed.com from the provided keyword or provide urls and will be extract each and everything about jobs.
    """
    try:
        # load proxies in diction format
        proxies = await proxies_loader.load_proxies()
        # load indeed login accounts cookies
        accounts = await accounts_loader.load_accounts()
    except Exception as e:
        logger.critical(f"Error loading context stuff: {e}")
    

    # launch borwser 
    async with Stealth().use_async(async_playwright()) as p:
        browser = await p.chromium.launch(headless=config_input.headless)
        tasks = []
        
        for index, job_page_url in enumerate(config_input.jobs_listed_pages_urls):
            try:                
                context = await browser.new_context(
                viewport={"width": 600, "height": 720},
                proxy=proxies[index])   
                
                
                # Inject fingerprint to every context before loading jobs pages
                script = await fingerprint_loader.load_fingerprint(index) # return js
                await context.add_init_script(script=script)
                if index==0:
                    print(f"✔ Total {len(config_input.jobs_listed_pages_urls)} context are launched.")
                    logger.info(f"Total {len(config_input.jobs_listed_pages_urls)} contexts launched.")
                
                # Jnject account into context
                try:
                    await context.add_cookies(accounts[index])
                except Exception as e:
                    await context.add_cookies(random.choice(accounts))

                tasks.append(_listing(context, job_page_url))

            except Exception as e:
                logger.critical("Context creation failed: {e}")

        await asyncio.gather(*tasks)

