from jobs.job_listings_scraper import jobs_lister
import asyncio
from utils import helper, sheet_uploader
from config import config_input



if __name__ == "__main__":
    try:
        # Prevent screen to sleep
        sb = helper.SleepBlocker()
        sb.prevent_sleep()
        
        # Create first new workbook with three sheet for saving scraper result
        helper.create_csv_files()

        # Clean the processded saved jobs file
        helper.clean_processed_jobs_file()

        # Create a debugging folder for save screenshot for debugging
        helper.create_debugging_screenshots_folder(config_input.DEBUGGING_SCREENSHOTS_PATH)
       
        # # Main function that do listing and all other stuff
        asyncio.run(jobs_lister())
        
        # # After save all result of scraper uploading to google sheet
        helper.sort_csv_files_by_column(config_input.CSV_FILES, sort_column_index=config_input.leave_blank_colls + 2)
        sheet_uploader.update_google_sheets_from_csv(config_input.CSV_FILES)
    except Exception as e:
        print(e)
    finally:
        # Reanable default sleep mode
        sb.allow_sleep()

