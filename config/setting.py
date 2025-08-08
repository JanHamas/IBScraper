
# ON/OFF Headless mode
headless = True

# File path which jobs processed 
PROCESSED_JOBS_FILE_PATH =r'input\\processed_jobs.txt'

# after extract jobs from list page size of batche should be process and saving excel file
process_batch = 15

# Wait until pagination appears before rasing not found error
wait_pg_present = 6

# Excel file path
EXCEL_FILE_PATH = r'output\\jobs.xlsx'


DEBUGGING_SCREENSHOTS_PATH = "debugging_screenshots"

#
leave_blink_cols = 2

# These file are append with scraping data during scraping
CSV_FILES = ["Easy_applies.csv", "CS_applies.csv", "Confirmation_applies.csv"]