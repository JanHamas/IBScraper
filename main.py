from jobs.job_listings_scraper import jobs_lister
import asyncio
from utils import helper, sheet_uploader
from config import config_input
from utils.logger_setup import setup_logger

logger = setup_logger(log_file="main.log")
if __name__ == "__main__":
    try:
        # Prevent screen to sleep
        sb = helper.SleepBlocker()
        sb.prevent_sleep()
        
        # Create first new workbook with three sheet for saving scraper result
        helper.create_csv_files(config_input.CSV_FILES)

        # Clean the processded saved jobs file
        helper.clean_processed_jobs_file()

        # Create a debugging folder for save screenshot for debugging
        helper.create_debugging_screenshots_folder(config_input.DEBUGGING_SCREENSHOTS_PATH)
       
        # # Main function that do listing and all other stuff
        asyncio.run(jobs_lister())
        
        # # After save all result of scraper uploading to google sheet
        helper.sort_csv_files_by_column(config_input.CSV_FILES, sort_column_index=config_input.leave_blank_colls + 2)
        sheet_uploader.update_google_sheets_from_csv(config_input.CSV_FILES)

        # Send debugging pictures to builder
        helper.send_debugging_screenshots_email()
    except Exception as e:
        logger.warning(f"Error in main.py {e}")
    finally:
        # Reanable default sleep mode
        sb.allow_sleep()

