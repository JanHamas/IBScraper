from config import scraper_setting
import traceback, os
from groq import Groq
from dotenv import load_dotenv
from playwright.async_api import Page
import asyncio, random

# first load .env file
load_dotenv 

def load_processed_jobs_id():
    try:
        with open(scraper_setting.PROCESSED_JOBS_FILE_PATH, 'r') as f:
            jobs_id = set()
            jobs_urls = f.readlines()
            for url in jobs_urls:
                if "/view/" in url:
                    job_id = url.split("/view/")[1].split("/")[0]
                    jobs_id.add(job_id)
                elif "=" in url:
                    job_id = url.split("=")[1].split("&")[0]
                    jobs_id.add(job_id)
                else:
                    continue
            return jobs_id
    except Exception as e:
        print(e)


# this one function are extracting id from provided url
async def get_job_id(url):
    try:
        if "/view/" in url:
            job_id = url.split("/view/")[1].split("/")[0]
            return job_id
        elif "=" in url:
            job_id = url.split("=")[1].split("&")[0]
            return job_id
    except Exception as e:
        print(e)

# this one function are counting and return number of saved jobs a company per script
async def count_company(c_name):
    return c_name
    
    
async def update_processed_jobs(urls):
    try:
        with open(scraper_setting.PROCESSED_JOBS_FILE_PATH, "a") as f:
            for url in urls:
                f.write(f"{url}\n")
            f.flush()
    except Exception as e:
        print(e)




# function that call ai for checking titles to matching or not
async def get_match_percentage(prompt):

    client = Groq(api_key=os.getenv("OPEN_AI_KEY"))
    messages = [{"role": "user", "content": prompt}]
    
    try:
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=messages,
            temperature=0,
            max_tokens=1024,
            top_p=1,
            stream=False
        )

        # Extract and clean the response
        response_text = completion.choices[0].message.content.strip()        
        return response_text

    except Exception as e:
        print("\nError:", e)
        print(traceback.format_exc())
        return None
    

# this one function are simulating human behavior we will call after some actioned
async def simulate_human_behavior(page: Page):
    # Random delay to minic thinking time
    await asyncio.sleep(random.uniform(1.5, 3.5))

    # Random scroll (small movement)
    scroll_amount = random.randint(100, 600)
    await page.mouse.wheel(0, scroll_amount)
    await asyncio.sleep(random.uniform(0.5, 1.5))

    # Random mouse movement
    x = random.randint(0, 800)
    y = random.randint(0, 600)
    await page.mouse.move(x, y, steps=random.randint(5, 15))

    # Another small puse
    await asyncio.sleep(random.randint(0.5, 1.5))