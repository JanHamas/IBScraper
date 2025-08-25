from scrapers.job_listings_scraper import jobs_lister
import asyncio
from utils import helper, sheet_uploader
from config import config_input
from utils.logger_setup import setup_logger   # ← add this

if __name__ == "__main__":
    logger = setup_logger()  # ← first thing: set up logging

    try:
        logger.info("🚀 Scraper started")

        # Prevent screen to sleep
        sb = helper.SleepBlocker()
        sb.prevent_sleep()
        
        # Create first new workbook with three sheet for saving scraper result
        helper.create_csv_files(config_input.CSV_FILES)
        logger.info("✅ Fresh CSV files created")

        # Clean the processed saved jobs file
        helper.clean_processed_jobs_file()
        logger.info("🧹 Processed jobs file cleaned")

        # Create a debugging folder
        folder_path = "debugging_screenshots"
        helper.create_debugging_screenshots_folder(folder_path)
        logger.info("📁 Debugging folder ready")

        # Main function that do listing and all other stuff
        asyncio.run(jobs_lister())
        logger.info("🧭 jobs_lister() finished")

        # After save all result of scraper uploading to google sheet
        helper.sort_csv_files_by_column(config_input.CSV_FILES, sort_column_index=config_input.LEAVE_BLANK_COLLS + 2)
        sheet_uploader.update_google_sheets_from_csv(config_input.CSV_FILES)
        logger.info("📊 Google Sheets updated")

        # Send debugging pictures to builder
        helper.send_debugging_screenshots_and_spider_log_email()
        logger.info("📤 Debugging screenshots and spider.logs email sent")

    except Exception:
        logger.exception("❌ Error in main.py")
    finally:
        sb.allow_sleep()
        logger.info("🛑 Scraper finished, sleep mode re-enabled")
