from scrapers.job_listings_scraper import jobs_lister
import asyncio
from utils import helper, sheet_uploader
from config import config_input
from utils.logger_setup import setup_logger   # ← add this

if __name__ == "__main__":
    logger = setup_logger()  # ← first thing: set up logging

    try:
        logger.info("🚀 Project Acquirer AI started")

        # Prevent screen to sleep
        sb = helper.SleepBlocker()
        sb.prevent_sleep()
        
        # Create first new workbook with three sheets for saving scraper result
        helper.create_csv_files(config_input.CSV_FILES)
        logger.info("✅ Fresh CSV files created")

        # Clean the processed saved jobs file
        helper.clean_processed_jobs_file()
        logger.info("🧹 Processed jobs file cleaned")

        # Create a debugging folder
        folder_path = "debugging_screenshots"
        helper.create_debugging_screenshots_folder(folder_path)
        logger.info("📁 Debugging folder ready")

        # Split URLs into chunks
        chunk_size = config_input.chunk_urls_size
        urls_chunks = [
            config_input.jobs_listed_pages_urls[i:i + chunk_size]
            for i in range(0, len(config_input.jobs_listed_pages_urls), chunk_size)
        ]

        logger.info(f"Processing {len(config_input.jobs_listed_pages_urls)} URLs in {len(urls_chunks)} chunks")

        for i, chunk in enumerate(urls_chunks):
            logger.info(f"Processing chunk {i+1}/{len(urls_chunks)}")
            asyncio.run(jobs_lister(chunk))   # ← process one chunk at a time
        
        logger.info("🧭 jobs_lister() finished")

        # After saving all scraper results, upload to Google Sheets
        helper.sort_csv_files_by_column(
            config_input.CSV_FILES,
            sort_column_index=config_input.LEAVE_BLANK_COLLS + 2
        )
        sheet_uploader.update_google_sheets_from_csv(config_input.CSV_FILES)
        logger.info("📊 Google Sheets updated")

        # Send debugging pictures + logs
        helper.send_debugging_screenshots_and_spider_log_email()
        logger.info("📤 Debugging screenshots and spider.logs email sent")

    except Exception:
        logger.exception("❌ Error in main.py")
    finally:
        sb.allow_sleep()
        logger.info("🛑 Scraper finished, sleep mode re-enabled")
