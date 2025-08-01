from jobs.job_listings_scraper import jobs_lister
import asyncio


if __name__ == "__main__":
    try:
        asyncio.run(jobs_lister())
    except Exception as e:
        print(e)