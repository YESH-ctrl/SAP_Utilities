import asyncio
import logging

from sap_rag.database.connection import DatabasePool
from sap_rag.database.repositories.crawl_job_repository import CrawlJobRepository

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("retry_failed")

async def main():
    logger.info("Connecting to Supabase to requeue failed crawl jobs...")
    await DatabasePool.initialize(min_size=1, max_size=2)
    try:
        async with DatabasePool.acquire() as conn:
            requeued_count = await CrawlJobRepository.requeue_failed_jobs(conn)
            print(f"\nSuccessfully requeued {requeued_count} failed crawl job(s) back to 'pending' status.\n")
    finally:
        await DatabasePool.close()

if __name__ == "__main__":
    asyncio.run(main())
