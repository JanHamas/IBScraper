import urllib.parse
import traceback, os, shutil, csv
from dotenv import load_dotenv
from playwright.async_api import Page
import google.generativeai as genai
import asyncio, random
import platform, subprocess, ctypes
from urllib.parse import urlparse, parse_qs
import smtplib
from email.message import EmailMessage
import mimetypes
from config import config_input
import gspread
from google.oauth2.service_account import Credentials

# Load environment variables
load_dotenv()

# load jobs id from previews processed jobs that are saved processed_jobs.txt
def load_processed_jobs_id(filename=config_input.PROCESSED_JOBS_FILE_PATH):
    try:
        jobs_id = set()
        with open(filename, 'r') as f:
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
    with open(config_input.PROCESSED_JOBS_FILE_PATH, "a") as f:
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
def create_csv_files(file_names):
    os.makedirs("output", exist_ok=True)
    for name in file_names:
        path = os.path.join("output", f"{name}")

        # Always overwrite the file (mode="w")
        with open(path, mode="w", newline='', encoding="utf-8") as f:
            continue

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

# Prevent different system to sleep
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
    with open(config_input.PROCESSED_JOBS_FILE_PATH, 'r') as f:
        urls = f.readlines()
    
    # Get the last 2300 lines
    last_urls = urls[-8000:]

    with open(config_input.PROCESSED_JOBS_FILE_PATH, 'w') as f:
        f.writelines(last_urls)

# Create a new folder for saveing debugging screenshots during scriping
def create_debugging_screenshots_folder(folder_path):
    # Delete the folder if exists
    if os.path.exists(folder_path):
        shutil.rmtree(folder_path)
    
    # Create a new folder
    os.mkdir(folder_path)
    print(f"✅ Create a new folder: {folder_path}")

# After complete scraping sort row descending base matching % column and overwrite save files
def sort_csv_files_by_column(filenames = config_input.CSV_FILES, sort_column_index=4):
    
    encodings_to_try = ['utf-8', 'latin1', 'cp1252', 'utf-8-sig']

    for filename in filenames:
        filename = f"output/{filename}"
        rows, chosen_encoding = None, None

        # Try reading file with different encodings
        for encoding in encodings_to_try:
            try:
                with open(filename, 'r', newline='', encoding=encoding) as f:
                    reader = csv.reader(f)
                    rows = list(reader)
                chosen_encoding = encoding
                print(f"📘 Read {filename} successfully with {encoding} encoding")
                break
            except UnicodeDecodeError:
                continue
            except Exception as e:
                print(f"⚠️ Error reading {filename} with {encoding}: {str(e)}")

        if not rows:
            print(f"⚠️ Could not read or file is empty: {filename}. Skipping.")
            continue

        # Detect header
        try:
            int(rows[0][sort_column_index])
            has_header = False
        except (ValueError, IndexError):
            has_header = True

        header = rows[0] if has_header else None
        data = rows[1:] if has_header else rows

        # Try to sort data by specified column
        try:
            data.sort(key=lambda row: int(row[sort_column_index]), reverse=True)
        except (IndexError, ValueError) as e:
            print(f"⚠️ Sorting failed for {filename}: {str(e)}. Saving unsorted.")

        # Write back sorted data
        try:
            with open(filename, 'w', newline='', encoding=chosen_encoding) as f:
                writer = csv.writer(f)
                if header:
                    writer.writerow(header)
                writer.writerows(data)
            print(f"✅ Sorted and saved {filename} successfully.\n")
        except Exception as e:
            print(f"⚠️ Failed to write {filename}: {str(e)}")

# Send the debugging screenshots to scraper builder 
def send_debugging_screenshots_email(folder_path="debugging_screenshots"):
    sender = os.getenv("EMAIL_SENDER")
    password = os.getenv("EMAIL_PASSWORD")
    recipient = os.getenv("EMAIL_RECIPIENT")
    smtp_server = os.getenv("SMTP_SERVER")
    smtp_port = int(os.getenv("SMTP_PORT", 587))

    if not all([sender, password, recipient, smtp_server]):
        print("❌ Missing one or more required .env values.")
        return

    # Create the email message
    msg = EmailMessage()
    msg["Subject"] = "🪲 Debugging Screenshots"
    msg["From"] = sender
    msg["To"] = recipient
    msg.set_content("Attached are the latest debugging screenshots.")

    # Attach image files from the folder
    if not os.path.exists(folder_path):
        print(f"❌ Folder '{folder_path}' not found.")
        return

    attached = 0
    for filename in os.listdir(folder_path):
        filepath = os.path.join(folder_path, filename)
        if os.path.isfile(filepath) and filename.lower().endswith(('.png', '.jpg', '.jpeg')):
            ctype, encoding = mimetypes.guess_type(filepath)
            if ctype is None or encoding is not None:
                ctype = 'application/octet-stream'
            maintype, subtype = ctype.split('/', 1)

            with open(filepath, 'rb') as f:
                msg.add_attachment(f.read(),
                                   maintype=maintype,
                                   subtype=subtype,
                                   filename=filename)
                attached += 1

    if attached == 0:
        print("⚠️ No screenshots found to attach.")
        return

    # Send the email
    try:
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(sender, password)
            server.send_message(msg)
        print(f"✅ Email sent to {recipient} with {attached} attachments.")
    except Exception as e:
        print(f"❌ Failed to send email: {e}")
