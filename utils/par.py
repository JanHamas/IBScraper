import os
import gspread
from google.oauth2.service_account import Credentials

def load_scraper_config_from_sheet(sheet_name="ScraperConfig", creds_path="utils/gs_credentials.json"):
    # Build full path to the credentials file
    base_dir = os.path.dirname(os.path.abspath(__file__))
    full_creds_path = os.path.join(base_dir, creds_path)

    # Google Sheets API scope
    scopes = ["https://www.googleapis.com/auth/spreadsheets"]
    creds = Credentials.from_service_account_file(full_creds_path, scopes=scopes)
    client = gspread.authorize(creds)

    # Open the spreadsheet
    spreadsheet = client.open(sheet_name)

    # Load Settings sheet
    settings_sheet = spreadsheet.worksheet("Settings")
    settings_data = settings_sheet.get_all_values()
    settings_dict = {row[0]: row[1] for row in settings_data if row and len(row) > 1}

    # Load a column of values from a given sheet
    def load_column(sheet_name):
        try:
            sheet = spreadsheet.worksheet(sheet_name)
            return [row[0].strip() for row in sheet.get_all_values() if row and row[0].strip()]
        except gspread.exceptions.WorksheetNotFound:
            return []

    # Construct final config dictionary
    config = {
        "MATCHING_PERCENTAGE": int(settings_dict.get("MATCHING_PERCENTAGE", 50)),
        "leave_blank_colls": int(settings_dict.get("leave_blank_colls", 2)),
        "AI_PROMPT": settings_dict.get("AI_PROMPT", ""),
        "RESUME": settings_dict.get("RESUME", ""),
        "per_company_jobs": int(settings_dict.get("per_company_jobs", 2)),
        "headless": settings_dict.get("headless", "TRUE").strip().upper() == "TRUE",
        "process_batch": int(settings_dict.get("process_batch", 15)),
        "wait_pg_present": int(settings_dict.get("wait_pg_present", 6)),
        "PROCESSED_JOBS_FILE_PATH": settings_dict.get("PROCESSED_JOBS_FILE_PATH", ""),
        "EXCEL_FILE_PATH": settings_dict.get("EXCEL_FILE_PATH", ""),
        "DEBUGGING_SCREENSHOTS_PATH": settings_dict.get("DEBUGGING_SCREENSHOTS_PATH", ""),
        "CSV_FILES": [f.strip() for f in settings_dict.get("CSV_FILES", "").split(",") if f.strip()],
        "workbook_id": settings_dict.get("workbook_id", ""),
        "jobs_listed_pages_urls": load_column("JobURLs"),
        "confirmation_companies": load_column("ConfirmationCompanies"),
        "ignore_companies": load_column("IgnoreCompanies"),
    }

    return config

config = load_scraper_config_from_sheet()

jobs_listed_pages_urls = config["jobs_listed_pages_urls"]
confirmation_companies = config["confirmation_companies"]
ignore_companies = config["ignore_companies"]
AI_PROMPT = config["AI_PROMPT"]
RESUME = config["RESUME"]
MATCHING_PERCENTAGE = config["MATCHING_PERCENTAGE"]
leave_blank_colls = config["leave_blank_colls"]
headless = config["headless"]


print(jobs_listed_pages_urls)