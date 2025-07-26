from config import config_input, scraper_setting
from playwright.async_api import async_playwright
from utils import credential_loader,fingersprint_loader,proxies_loader
from playwright_stealth import Stealth
import asyncio
from aioconsole import ainput


async def _listing(context, job_page_url):
    page = await context.new_page()
    await page.goto(job_page_url)
    await ainput("Press enter if working")


async def jobs_lister():
    """"
    This one function will be open all jobs keywords or provide urls and will be extract each and everything about jobs.
    """
    async with Stealth().use_async(async_playwright()) as p:
        browser = await p.chromium.launch(headless=scraper_setting.headless)
        
        # load proxies in diction format
        proxies = proxies_loader.load_proxies

        # load credential
        # credential = credential_loader.load_credential

        tasks = []

        for index, job_page_url in enumerate(config_input.jobs_listed_pages_urls):
            context = await browser.new_context(
                proxy=proxies[index],
                # storege_state=credential[index],
            )
            tasks.append(_listing(context,job_page_url))

        await asyncio.gather(*tasks)


asyncio.run(jobs_lister())