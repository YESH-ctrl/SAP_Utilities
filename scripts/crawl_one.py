import argparse
import asyncio
import logging
import sys
import json

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from sap_rag.crawler.config import settings
from sap_rag.crawler.scheduler import CrawlScheduler
from sap_rag.crawler.worker import CrawlWorker
from sap_rag.database.connection import DatabasePool
from sap_rag.database.repositories.crawl_job_repository import CrawlJobRepository
from sap_rag.crawler.fetcher import close_browser
from sap_rag.crawler.models import ParsedTOC

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("crawl_one")

async def main():
    parser = argparse.ArgumentParser(description="Crawl a single SAP reference source root.")
    parser.add_argument("--source-id", type=int, default=1, help="Source ID to crawl (default: 1)")
    parser.add_argument("--dry-run", action="store_true", help="Perform fetch & TOC parsing without database writes")

    args = parser.parse_args()

    logger.info(f"Starting crawl_one (source_id={args.source_id}, dry_run={args.dry_run})...")

    if args.dry_run:
        await DatabasePool.initialize(min_size=1, max_size=2)
        try:
            async with DatabasePool.acquire() as conn:
                job = await CrawlJobRepository.get_pending_job_read_only(conn, source_id_filter=args.source_id)
                if not job:
                    logger.warning(f"No pending crawl job found for source_id={args.source_id}")
                    return

                worker = CrawlWorker(source_id_filter=args.source_id, dry_run=True)
                result = await worker.processor.process_job(conn, job, dry_run=True)
                parsed_toc: ParsedTOC = result["parsed_toc"]

                print("\n" + "=" * 70)
                print("ROOT:")
                print(f"  {parsed_toc.root_title}")
                print("URL:")
                print(f"  {parsed_toc.root_canonical_url}")
                print("\nDOCUMENTATION TOC:")

                current_level = 0
                for node in parsed_toc.nodes:
                    if node.level != current_level:
                        print(f"\n[LEVEL {node.level}]")
                        current_level = node.level

                    indent = "  " * node.level
                    print(f"{indent}|-- {node.title}")
                    print(f"{indent}    URL: {node.url}")

                print("\n" + "-" * 70)
                print("SUMMARY METRICS:")
                print(f"  Total TOC nodes        : {parsed_toc.total_nodes}")
                print(f"  Unique URLs            : {parsed_toc.unique_urls}")
                print(f"  Duplicate URLs removed : {parsed_toc.duplicate_urls_removed}")
                print(f"  Ignored nav links      : {parsed_toc.ignored_navigation_links}")
                print(f"  External links         : {parsed_toc.external_links}")
                print(f"  Unknown links          : {parsed_toc.unknown_links}")
                print("=" * 70)
                print("No database writes performed.\n")
        finally:
            await close_browser()
            await DatabasePool.close()
    else:
        scheduler = CrawlScheduler(concurrency=1, source_id_filter=args.source_id, dry_run=False)
        summary = await scheduler.run()

        # Check final metrics from DB for Phase 12 validation reporting
        await DatabasePool.initialize(min_size=1, max_size=2)
        try:
            async with DatabasePool.acquire() as conn:
                root_doc = await conn.fetchrow(
                    "SELECT id, title, canonical_url FROM documents WHERE source_id = $1 AND depth = 0 LIMIT 1;",
                    args.source_id
                )
                child_count = await conn.fetchval(
                    "SELECT count(*) FROM documents WHERE source_id = $1 AND depth > 0;",
                    args.source_id
                )
                max_depth = await conn.fetchval(
                    "SELECT COALESCE(MAX(depth), 0) FROM documents WHERE source_id = $1;",
                    args.source_id
                )
                unique_canonical = await conn.fetchval(
                    "SELECT count(DISTINCT canonical_url) FROM documents WHERE source_id = $1;",
                    args.source_id
                )
                links_count = await conn.fetchval(
                    "SELECT count(*) FROM document_links WHERE source_document_id IN (SELECT id FROM documents WHERE source_id = $1);",
                    args.source_id
                )
                top_level_nodes = await conn.fetch(
                    "SELECT id, title, canonical_url FROM documents WHERE source_id = $1 AND depth = 1 ORDER BY id ASC;",
                    args.source_id
                )

                print("\n" + "=" * 70)
                print(f"VALIDATION METRICS FOR SOURCE #{args.source_id} ({root_doc['title'] if root_doc else 'Root'})")
                print("=" * 70)
                print(f"  Root document          : {root_doc['title'] if root_doc else 'N/A'}")
                print(f"  Child documents        : {child_count}")
                print(f"  Maximum depth          : {max_depth}")
                print(f"  Unique canonical URLs  : {unique_canonical}")
                print(f"  Document links stored  : {links_count}")
                print("\nTop-level documentation nodes (depth=1):")
                for idx, node in enumerate(top_level_nodes, 1):
                    print(f"  {idx}. {node['title']} -> {node['canonical_url']}")
                print("=" * 70 + "\n")
        finally:
            await DatabasePool.close()

if __name__ == "__main__":
    asyncio.run(main())
