import json
import asyncio
from playwright.async_api import async_playwright
from bypass.cloudflare import CloudflareBypasser  # Ensure this is properly implemented



async def main():    
    async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False)
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
            )

            page = await context.new_page()

            
            # First, go to a page on the domain
            await page.goto("https://www.indeed.com", wait_until="load")
            # Refresh to apply cookies
            await page.reload()            
           
            # 4. Bypass Cloudflare FIRST
            try:
                cf_bypasser = CloudflareBypasser(page)
                await cf_bypasser.detect_and_bypass()
            except Exception as e:
                print(f"⚠️ Cloudflare bypass: {e}")
            
            # Inject cookies
            await context.add_cookies(cookies)
            # Refresh to apply cookies
            await page.reload()

            await page.wait_for_timeout(30000)
            await browser.close()

asyncio.run(main())

