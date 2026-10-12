import asyncio
import logging
import time
from typing import Optional, Dict, Any

from sap_rag.crawler.config import settings
from sap_rag.crawler.crawler import CrawlProcessor
from sap_rag.database.connection import DatabasePool
from sap_rag.database.repositories.crawl_job_repository import CrawlJobRepository

logger = logging.getLogger(__name__)

class CrawlWorkerMetrics:
    """
    Tracks worker execution metrics and stats.
    """
    def __init__(self):
        self.pages_attempted = 0
        self.pages_successful = 0
        self.pages_failed = 0
        self.pages_skipped = 0
        self.child_jobs_created = 0
        self.start_time = time.time()

    def summary(self) -> Dict[str, Any]:
        elapsed = max(1.0, time.time() - self.start_time)
        return {
            "pages_attempted": self.pages_attempted,
            "pages_successful": self.pages_successful,
            "pages_failed": self.pages_failed,
            "pages_skipped": self.pages_skipped,
            "child_jobs_created": self.child_jobs_created,
            "elapsed_seconds": round(elapsed, 2),
            "pages_per_second": round(self.pages_successful / elapsed, 2),
        }

class CrawlWorker:
    """
    Worker task claiming pending crawl jobs from Supabase and running CrawlProcessor.
    """
    def __init__(self, worker_id: int = 1, source_id_filter: Optional[int] = None, dry_run: bool = False):
        self.worker_id = worker_id
        self.source_id_filter = source_id_filter
        self.dry_run = dry_run
        self.processor = CrawlProcessor()
        self.metrics = CrawlWorkerMetrics()

    async def run_once(self) -> Optional[Dict[str, Any]]:
        """
        Claim and process a single pending crawl job. Returns result dict or None if queue empty.
        """
        async with DatabasePool.acquire() as conn:
            job = await CrawlJobRepository.claim_pending_job(conn, source_id_filter=self.source_id_filter)
            if not job:
                return None

            self.metrics.pages_attempted += 1
            try:
                result = await self.processor.process_job(conn, job, dry_run=self.dry_run)
                self.metrics.pages_successful += 1
                self.metrics.child_jobs_created += result.get("child_jobs_created", 0)
                return result
            except Exception as e:
                self.metrics.pages_failed += 1
                logger.error(f"Worker #{self.worker_id} job #{job['id']} failed: {e}")
                return None

    async def run_until_empty(self, delay: float = None):
        """
        Continuously process jobs until no pending or active jobs remain for this source.
        """
        request_delay = delay if delay is not None else settings.CRAWLER_REQUEST_DELAY
        logger.info(f"Worker #{self.worker_id} starting crawl loop (source_filter={self.source_id_filter}, dry_run={self.dry_run})...")

        idle_attempts = 0
        max_idle_attempts = 5

        while True:
            result = await self.run_once()
            if result is None:
                # Check if there are active jobs currently being processed or scheduled
                async with DatabasePool.acquire() as conn:
                    if self.source_id_filter:
                        active_count = await conn.fetchval(
                            "SELECT count(*) FROM crawl_jobs WHERE status IN ('pending', 'crawling') AND source_id = $1;",
                            self.source_id_filter
                        )
                    else:
                        active_count = await conn.fetchval(
                            "SELECT count(*) FROM crawl_jobs WHERE status IN ('pending', 'crawling');"
                        )

                if active_count > 0 and idle_attempts < max_idle_attempts:
                    idle_attempts += 1
                    logger.info(f"Worker #{self.worker_id}: Queue temporarily idle ({active_count} active jobs remaining). Waiting 2s (attempt {idle_attempts}/{max_idle_attempts})...")
                    await asyncio.sleep(2.0)
                    continue

                logger.info(f"Worker #{self.worker_id}: No more pending or active jobs found.")
                break

            idle_attempts = 0
            if request_delay > 0:
                await asyncio.sleep(request_delay)

