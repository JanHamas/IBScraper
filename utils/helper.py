from config import scraper_setting
import traceback, os
from dotenv import load_dotenv
from playwright.async_api import Page
import google.generativeai as genai
import asyncio, random
import ctypes
import platform
import subprocess
import os
import csv
import os
import traceback
import shutil
import urllib.parse
from urllib.parse import urlparse, parse_qs

# first load .env file
load_dotenv 


def load_processed_jobs_id():
    try:
        jobs_id = set()
        with open(scraper_setting.PROCESSED_JOBS_FILE_PATH, 'r') as f:
            for url in f:
                parsed_url = urlparse(url.strip())
                query_params = parse_qs(parsed_url.query)
                job_id = query_params.get("jk", [None])[0]
                if job_id:
                    jobs_id.add(job_id)
        print(f"len jobs_id {len(jobs_id)}")
        return jobs_id
    
    except Exception as e:
        print(f"❌ Error loading job IDs: {e}")
        return set()


# this one function are extracting id from provided url
async def get_job_id(url):
    try:
        parsed_url = urllib.parse.urlparse(url)
        query_params = urllib.parse.parse_qs(parsed_url.query)
        job_id = query_params.get("jk", [None])[0]
        return job_id
    except Exception as e:
        print(f"Error extracting job_id: {e}")
        return None


# this one funciton update the processed jobs during scripting for avoid duplicate
async def update_processed_jobs(links):
    with open(scraper_setting.PROCESSED_JOBS_FILE_PATH, "a") as f:
        for link in links:
            f.write(f"{link}\n")
        f.flush()

# Set your Gemini API key (you can also use os.getenv("GOOGLE_API_KEY"))
genai.configure(api_key="AIzaSyAfM8-AmzjZAF_ovj5vlEKbwLUj4aWR2OA")

# Define an async wrapper (Gemini's SDK is sync, so use asyncio.to_thread)
async def get_match_percentage(prompt: str):
    try:
        model = genai.GenerativeModel("gemini-2.0-flash")

        # Run sync Gemini call in a background thread
        response = await asyncio.to_thread(model.generate_content, prompt)

        # Extract and return the cleaned response
        response_text = response.text.strip()
        return response_text

    except Exception as e:
        print("\nError:", e)
        print(traceback.format_exc())
        return None


# === Replace workbook creation with folder setup ===
def create_csv_files():
    os.makedirs("csv_data", exist_ok=True)

    headers = ["Col1", "Col2", "Col3", "Col4", "Col5", "Col6", "Col7", "Col8"]
    file_names = ["Easy_applies", "CS_applies", "Confirmation_applies"]

    for name in file_names:
        path = os.path.join("csv_data", f"{name}.csv")

        # Always overwrite the file (mode="w")
        with open(path, mode="w", newline='', encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(headers)

        print(f"✅ Created fresh file: {path}")


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
    await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
    await asyncio.sleep(random.randint(1, 3))






# # the below function are use for checking internect connection 
# async def check_internet():
#      test_sites = [
#         "https://1.1.1.1",  # Cloudflare DNS (very reliable)
#         "https://www.cloudflare.com",  # Cloudflare official site
#         "https://example.com",  # Example website (simple and lightweight)
#         "https://www.bing.com"  # Bing as an alternative to Google
#     ]
#     async with aiohttp.ClientSession() as session:
#         sa
    

class SleepBlocker:
    def __init__(self):
        self.platform = platform.system()
        self.proc = None  # For macOS and Linux

    def prevent_sleep(self):
        if self.platform == "Windows":
            ES_CONTINUOUS = 0x80000000
            ES_SYSTEM_REQUIRED = 0x00000001
            ES_DISPLAY_REQUIRED = 0x00000002
            ctypes.windll.kernel32.SetThreadExecutionState(
                ES_CONTINUOUS | ES_SYSTEM_REQUIRED | ES_DISPLAY_REQUIRED
            )
        elif self.platform == "Darwin":  # macOS
            # Starts a background caffeinate process
            self.proc = subprocess.Popen(["caffeinate"])
        elif self.platform == "Linux":
            # Dummy workaround: start a process that prevents screensaver
            self.proc = subprocess.Popen(["bash", "-c", "while true; do sleep 60; done"])
        else:
            print("Unsupported OS")

    def allow_sleep(self):
        if self.platform == "Windows":
            ES_CONTINUOUS = 0x80000000
            ctypes.windll.kernel32.SetThreadExecutionState(ES_CONTINUOUS)
        elif self.platform in ["Darwin", "Linux"]:
            if self.proc:
                self.proc.terminate()
                self.proc = None
        else:
            print("Unsupported OS")


# clean and resave last 3000 links in previews.txt file
def clean_processed_jobs_file():
    with open(scraper_setting.PROCESSED_JOBS_FILE_PATH, 'r') as f:
        urls = f.readlines()
    
    # Get the last 2300 lines
    last_urls = urls[-5000:]

    with open(scraper_setting.PROCESSED_JOBS_FILE_PATH, 'w') as f:
        f.writelines(last_urls)




def create_debugging_screenshots_folder(folder_path):
    # Delete the folder if exists
    if os.path.exists(folder_path):
        shutil.rmtree(folder_path)
    
    # Create a new folder
    os.mkdir(folder_path)
    print(f"✅ Create a new folder: {folder_path}")
