import asyncio
import logging
from typing import Optional, Dict, Any

from sap_rag.crawler.config import settings
from sap_rag.crawler.worker import CrawlWorker, CrawlWorkerMetrics
from sap_rag.crawler.fetcher import close_browser
from sap_rag.database.connection import DatabasePool

logger = logging.getLogger(__name__)

class CrawlScheduler:
    """
    Orchestrates multiple worker tasks concurrently.
    """
    def __init__(self, concurrency: int = None, source_id_filter: Optional[int] = None, dry_run: bool = False):
        self.concurrency = concurrency or settings.CRAWLER_MAX_CONCURRENCY
        self.source_id_filter = source_id_filter
        self.dry_run = dry_run

    async def run(self, cleanup: bool = True) -> Dict[str, Any]:
        """
        Initialize database pool, launch worker tasks, aggregate metrics, and shutdown cleanly.
        """
        if cleanup:
            await DatabasePool.initialize(min_size=1, max_size=self.concurrency + 2)

        try:
            workers = [
                CrawlWorker(worker_id=i + 1, source_id_filter=self.source_id_filter, dry_run=self.dry_run)
                for i in range(self.concurrency)
            ]

            logger.info(f"Launching {self.concurrency} concurrent worker task(s)...")
            await asyncio.gather(*[w.run_until_empty() for w in workers])

            # Aggregate metrics across all workers
            total_attempted = sum(w.metrics.pages_attempted for w in workers)
            total_successful = sum(w.metrics.pages_successful for w in workers)
            total_failed = sum(w.metrics.pages_failed for w in workers)
            total_children = sum(w.metrics.child_jobs_created for w in workers)

            summary = {
                "concurrency": self.concurrency,
                "source_id_filter": self.source_id_filter,
                "dry_run": self.dry_run,
                "pages_attempted": total_attempted,
                "pages_successful": total_successful,
                "pages_failed": total_failed,
                "child_jobs_created": total_children,
            }

            logger.info(f"Crawl finished summary: {summary}")
            return summary

        finally:
            if cleanup:
                await close_browser()
                await DatabasePool.close()

