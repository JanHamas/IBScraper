import asyncio, json, random
from aioconsole import ainput
from playwright_stealth import Stealth
from playwright.async_api import async_playwright

from config import config_input, scraper_setting
from utils.bypass.cloudflare import CloudflareBypasser
from utils import accounts_loader, fingerprint_loader, proxies_loader, helper

# for avoid duplicate let's create a set that store all links uniqe id and create a method that load id from previews saved jobs
processed_jobs_id = helper.load_processed_jobs_id()
processed_new_company_jobs = [] # this are appending with c_name which are now processd and for avoiding store multiples per company jobs


async def _listing(context, job_page_url):
    try:
        # Open job page
        page = await context.new_page()
        await page.goto(job_page_url, wait_until="load")
        
        # Try to bypass cloudflare if present
        try:
            cf_bypasser = CloudflareBypasser(page)
            await cf_bypasser.detect_and_bypass()
            # await page.wait_for_load_state("networkidle")
        except Exception as e:
            print(f"❌ Error to handle captcha: \n {e}")
        
        # 
        list_of_processed_jobs = []   # Temp saving for update processed jobs file
        list_of_company = [] # Temp saving for batching process
        list_of_titles = [] # Temp saving for batching process
        list_of_links = [] # Temp saving for batching process
        pagination_number = 1
        
        # Loop go throuhg the end of pagination btn break when further pg not found
        while True:
            # Scroll to bottom
            await page.wait_for_timeout(random.randint(3000,6000))
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            
            try:
                # Getting in list form all jobs Titles, links, Companies per each page
                titles = await page.query_selector_all(".jobTitle")
                companies = await page.query_selector_all("[data-testid='company-name']")   
                links = await page.query_selector_all(".jcs-JobTitle")
            except Exception as e:
                print(f"❌ Error in selectors: \n {e}")

            for title, company, link in zip(titles, companies, links):
                link = await link.get_attribute("href")

                # Count company jobs that are saved
                company = (await company.inner_text()).strip()
                count = processed_new_company_jobs.count(company)

                # Skip if job don't matching with three condition
                if count > config_input.per_company_jobs or await helper.get_job_id(link) in processed_jobs_id or company in config_input.ignore_companies:
                    continue

                # update job id and company
                processed_jobs_id.add(await helper.get_job_id(link))
                processed_new_company_jobs.append(company)

                # update list
                list_of_titles.append((await title.inner_text()).strip())
                list_of_company.append(company)
                list_of_links.append(link.strip())

                # Limit to 10 jobs before process
                print(f"len of titles: {len(list_of_titles)}")
                if len(list_of_titles) >= scraper_setting.process_batch:
                    print(f" \n Wait for model matches response...")
                    await process_batch(list_of_titles, list_of_company, list_of_links)
                    # clear all list for new append after process
                    list_of_titles.clear()
                    list_of_company.clear()
                    list_of_links.clear()
                    await helper.update_processed_jobs(list_of_processed_jobs)
                    list_of_processed_jobs.clear()

            # Click on pagination btn
            try:
                button_locator = page.locator(f"[data-testid='pagination-page-{pagination_number + 1}']")
                if await button_locator.is_visible():
                    await button_locator.click()
                    pagination_number+=1
            except Exception as e:
                print(f"❌ Falied to click button {pagination_number+1} \n {e}")
                await process_batch(list_of_titles, list_of_company, list_of_links)
                # clear all the lists for new filling
                list_of_titles.clear()
                list_of_company.clear()
                list_of_links.clear()
                await helper.update_processed_jobs(list_of_processed_jobs)
                list_of_processed_jobs.clear()
                break
    except Exception as e:
        print(e)

async def process_batch(list_of_titles, list_of_company, list_of_links):
    # Create first complete prompt
    prompt =f""" 
{config_input.AI_PROMPT}\n
{config_input.RESUME}\n
Jobs Titles:
{list_of_titles}
    """
    print(f"PROMPT ARE : \n{prompt}")
    # Call model function for providing matching %
    model_response = await helper.get_match_percentage(prompt)
    print(model_response)


async def jobs_lister():
    """"
    This one function will be open all jobs listed pages on indeed.com from the provided keyword or provide urls and will be extract each and everything about jobs.
    """
    try:
        # load proxies in diction format
        proxies = await proxies_loader.load_proxies()
        # load indeed login accounts cookies
        account = await accounts_loader.load_accounts()

    except Exception as e:
        print(f"❌Error to load context stuff: \n {e}")

    # launch borwser 
    async with Stealth().use_async(async_playwright()) as p:
        browser = await p.chromium.launch(headless=scraper_setting.headless)
        tasks = []
        
        for index, job_page_url in enumerate(config_input.jobs_listed_pages_urls):
            try:                
                context = await browser.new_context(
                proxy=proxies[index])   
                                    
                
                # Inject fingerprint to every context before loading jobs pages
                script = await fingerprint_loader.load_fingerprint() # return js
                await context.add_init_script(script=script)
                # Jnject account into context
                await context.add_cookies(account)
                    
                tasks.append(_listing(context, job_page_url))

            except Exception as e:
                print(f"❌ Error \n {e}")

        await asyncio.gather(*tasks)


