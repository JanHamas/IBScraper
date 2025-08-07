import os
import csv
import asyncio
import pandas as pd
import gspread
from gspread_dataframe import set_with_dataframe
from google.oauth2.service_account import Credentials
from config import config_input, scraper_setting
from config import config_input


# === 1. Replace workbook creation with folder and empty CSVs ===
def create_csv_files():
    os.makedirs("csv_data", exist_ok=True)
    sheet_names = ["Easy_applies", "CS_applies", "Confirmation_applies"]
    for sheet in sheet_names:
        path = os.path.join("csv_data", f"{sheet}.csv")
        if not os.path.exists(path):
            with open(path, mode="w", newline='', encoding="utf-8") as f:
                writer = csv.writer(f)
                # Use actual column headers here
                writer.writerow(["Col1", "Col2", "Col3", "Col4", "Col5", "Col6", "Col7", "Col8"])
    print("✔ CSV files initialized.")


# === 2. Append new job entries to corresponding CSVs ===
def _append_jobs(easy_applies, cs_applies, c_applies):
    def append_to_csv(file_name, rows):
        if not rows:
            return
        path = os.path.join("csv_data", file_name)
        with open(path, mode="a", newline='', encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerows(rows)

    append_to_csv("Easy_applies.csv", easy_applies)
    append_to_csv("CS_applies.csv", cs_applies)
    append_to_csv("Confirmation_applies.csv", c_applies)
    print("✔ Saved in CSV files.")


# === 3. Async wrapper ===
async def jobs_append_to_csv(easy_applies, cs_applies, c_applies):
    print(f"\nEasy: {len(easy_applies)}, CS: {len(cs_applies)}, C: {len(c_applies)}")
    loop = asyncio.get_event_loop()
    try:
        await loop.run_in_executor(None, lambda: _append_jobs(easy_applies, cs_applies, c_applies))
    except Exception as e:
        print(f"❌ Error saving to CSV: {e}")


# === 4. Replace update_google_sheets_from_excel with CSV logic ===
def update_google_sheets_from_csv():
    import pandas as pd
    import gspread
    from gspread_dataframe import set_with_dataframe
    from google.oauth2.service_account import Credentials
    import os

    # 🔐 Google Sheets credentials
    base_dir = os.path.dirname(__file__)
    creds_path = os.path.join(base_dir, "gs_credentials.json")
    workbook_id = "1wgGWS5xvxJgOuf2rx3TLQNDYSNStttQa7L8fFSWxs30"
    scopes = ["https://www.googleapis.com/auth/spreadsheets"]

    # ✅ Auth & connect
    creds = Credentials.from_service_account_file(creds_path, scopes=scopes)
    client = gspread.authorize(creds)
    workbook = client.open_by_key(workbook_id)

    # 📄 Sheet list
    sheet_names = ["Easy_applies", "CS_applies", "Confirmation_applies"]

    for sheet_name in sheet_names:
        csv_path = os.path.join("csv_data", f"{sheet_name}.csv")

        if not os.path.exists(csv_path):
            print(f"❌ CSV not found: {csv_path}")
            continue

        try:
            df = pd.read_csv(csv_path)
        except Exception as e:
            print(f"❌ Failed to read CSV '{csv_path}': {e}")
            continue

        if df.empty:
            print(f"⚠ CSV '{sheet_name}' is empty. Skipping.")
            continue

        # ✅ Sort by column index 4 (Column 5)
        try:
            sort_column = df.columns[config_input.config_leave_colls + 2]  
            df = df.sort_values(by=sort_column, ascending=False)
        except Exception as e:
            print(f"❌ Sorting failed for '{sheet_name}': {e}")
            continue

        # ✅ Get or create worksheet
        try:
            worksheet = workbook.worksheet(sheet_name)
        except gspread.exceptions.WorksheetNotFound:
            worksheet = workbook.add_worksheet(title=sheet_name, rows="1000", cols="20")
            print(f"📄 Created new worksheet: '{sheet_name}'")

        # ✅ Find the next empty row (always start at column A)
        existing_data = worksheet.get_all_values()
        next_row = len(existing_data) + 1

        # ✅ Write starting at first column (A)
        try:
            set_with_dataframe(
                worksheet,
                df,
                row=next_row,
                col=1,  # ✅ force write from Column A
                include_column_header=False
            )
            print(f"✅ Appended sorted data to Google Sheet: '{sheet_name}' from Column A")
        except Exception as e:
            print(f"❌ Failed to write to Google Sheet '{sheet_name}': {e}")
