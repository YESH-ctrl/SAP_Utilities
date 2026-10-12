import argparse
import asyncio
import json
import logging
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from sap_rag.crawler.config import settings
from sap_rag.crawler.fetcher import close_browser
from sap_rag.crawler.scheduler import CrawlScheduler
from sap_rag.database.connection import DatabasePool

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("crawl_all")

async def run_sql_validation(conn) -> Dict[str, Any]:
    """
    Run Section 12 Automated Database Validation SQL checks.
    """
    logger.info("Running Section 12 Automated Database Validation SQL checks...")
    
    # A. Orphans (depth > 0 with parent_id IS NULL)
    orphans = await conn.fetchval(
        "SELECT count(*) FROM documents WHERE parent_id IS NULL AND depth > 0;"
    )

    # B. Invalid depth (c.depth != p.depth + 1)
    invalid_depth = await conn.fetchval(
        """
        SELECT count(*)
        FROM documents c
        JOIN documents p ON c.parent_id = p.id
        WHERE c.depth <> p.depth + 1;
        """
    )

    # C. Duplicate canonical URLs per source
    duplicates = await conn.fetchval(
        """
        SELECT count(*) FROM (
            SELECT source_id, canonical_url, count(*)
            FROM documents
            GROUP BY source_id, canonical_url
            HAVING count(*) > 1
        ) sub;
        """
    )

    # D. Missing root_document_id
    missing_root = await conn.fetchval(
        "SELECT count(*) FROM documents WHERE root_document_id IS NULL;"
    )

    # E. Child assigned to wrong root
    wrong_root = await conn.fetchval(
        """
        SELECT count(*)
        FROM documents c
        JOIN documents p ON c.parent_id = p.id
        WHERE c.root_document_id <> p.root_document_id;
        """
    )

    # F. Crawled document without content
    empty_crawled = await conn.fetchval(
        "SELECT count(*) FROM documents WHERE status = 'crawled' AND (content IS NULL OR length(trim(content)) = 0);"
    )

    # G. Active crawl jobs
    job_statuses_rows = await conn.fetch(
        "SELECT status, count(*) as count FROM crawl_jobs GROUP BY status;"
    )
    job_statuses = {r["status"]: r["count"] for r in job_statuses_rows}

    return {
        "orphans_count": orphans,
        "invalid_depth_count": invalid_depth,
        "duplicate_urls_count": duplicates,
        "missing_root_id_count": missing_root,
        "wrong_root_id_count": wrong_root,
        "empty_crawled_doc_count": empty_crawled,
        "active_crawl_jobs": job_statuses,
        "is_valid": (
            orphans == 0 and
            invalid_depth == 0 and
            duplicates == 0 and
            missing_root == 0 and
            wrong_root == 0 and
            empty_crawled == 0
        )
    }

async def process_source_worker(
    semaphore: asyncio.Semaphore,
    source: Dict[str, Any],
    preflight_info: Dict[str, Any],
    page_concurrency: int,
    resume: bool
) -> Dict[str, Any]:
    source_id = source["id"]
    title = source.get("title", f"Source #{source_id}")
    source_file = source.get("source_file", f"Source_{source_id}.pdf")
    preflight_status = preflight_info.get("status", "VALID")
    start_time = time.time()

    async with semaphore:
        logger.info(f"Worker started for Source #{source_id}: {title} [Pre-flight: {preflight_status}]")

        if preflight_status == "SUSPICIOUS":
            logger.warning(f"ROOT_TOC_SUSPICIOUS for Source #{source_id}: Skipped live crawl to protect DB queue.")
            return {
                "source_id": source_id,
                "source_file": source_file,
                "title": title,
                "root_url": source.get("seed_url"),
                "status": "SUSPICIOUS",
                "toc_node_count": preflight_info.get("node_count", 0),
                "unique_urls": preflight_info.get("unique_urls", 0),
                "duplicate_urls": preflight_info.get("duplicate_urls_removed", 0),
                "documents_discovered": 0,
                "documents_crawled": 0,
                "documents_failed": 0,
                "pending_jobs": 0,
                "maximum_depth": 0,
                "sections": 0,
                "document_links": 0,
                "crawl_duration_sec": round(time.time() - start_time, 2),
                "suspicious_flag": True,
                "error_count": 0,
                "error": "TOC size exceeds safety threshold (> 300 nodes)",
            }

        try:
            scheduler = CrawlScheduler(concurrency=page_concurrency, source_id_filter=source_id, dry_run=False)
            crawl_summary = await scheduler.run(cleanup=False)

            async with DatabasePool.acquire() as conn:
                root_doc = await conn.fetchrow(
                    "SELECT id, title, canonical_url FROM documents WHERE source_id = $1 AND depth = 0 LIMIT 1;",
                    source_id
                )
                crawled_docs = await conn.fetchval(
                    "SELECT count(*) FROM documents WHERE source_id = $1 AND status = 'crawled';",
                    source_id
                )
                discovered_docs = await conn.fetchval(
                    "SELECT count(*) FROM documents WHERE source_id = $1;",
                    source_id
                )
                max_depth = await conn.fetchval(
                    "SELECT COALESCE(MAX(depth), 0) FROM documents WHERE source_id = $1;",
                    source_id
                )
                sections_count = await conn.fetchval(
                    "SELECT count(*) FROM document_sections WHERE document_id IN (SELECT id FROM documents WHERE source_id = $1);",
                    source_id
                )
                links_count = await conn.fetchval(
                    "SELECT count(*) FROM document_links WHERE source_document_id IN (SELECT id FROM documents WHERE source_id = $1);",
                    source_id
                )
                failed_jobs = await conn.fetchval(
                    "SELECT count(*) FROM crawl_jobs WHERE source_id = $1 AND status = 'failed';",
                    source_id
                )
                pending_jobs = await conn.fetchval(
                    "SELECT count(*) FROM crawl_jobs WHERE source_id = $1 AND status IN ('pending', 'queued', 'crawling');",
                    source_id
                )

            final_status = "SUCCESS" if failed_jobs == 0 else "PARTIAL_SUCCESS"

            return {
                "source_id": source_id,
                "source_file": source_file,
                "title": root_doc["title"] if root_doc else title,
                "root_url": root_doc["canonical_url"] if root_doc else source.get("seed_url"),
                "status": final_status,
                "toc_node_count": preflight_info.get("node_count", 0),
                "unique_urls": preflight_info.get("unique_urls", 0),
                "duplicate_urls": preflight_info.get("duplicate_urls_removed", 0),
                "documents_discovered": discovered_docs,
                "documents_crawled": crawled_docs,
                "documents_failed": failed_jobs,
                "pending_jobs": pending_jobs,
                "maximum_depth": max_depth,
                "sections": sections_count,
                "document_links": links_count,
                "crawl_duration_sec": round(time.time() - start_time, 2),
                "suspicious_flag": False,
                "error_count": failed_jobs,
                "error": None,
            }

        except Exception as e:
            logger.error(f"Source #{source_id} worker failed: {e}")
            return {
                "source_id": source_id,
                "source_file": source_file,
                "title": title,
                "root_url": source.get("seed_url"),
                "status": "FAILED",
                "toc_node_count": preflight_info.get("node_count", 0),
                "unique_urls": preflight_info.get("unique_urls", 0),
                "duplicate_urls": preflight_info.get("duplicate_urls_removed", 0),
                "documents_discovered": 0,
                "documents_crawled": 0,
                "documents_failed": 1,
                "pending_jobs": 0,
                "maximum_depth": 0,
                "sections": 0,
                "document_links": 0,
                "crawl_duration_sec": round(time.time() - start_time, 2),
                "suspicious_flag": False,
                "error_count": 1,
                "error": str(e),
            }

async def prepare_database_before_crawl(conn):
    logger.info("Pre-crawl DB prep: Re-queuing stuck jobs and fixing document metadata...")
    await conn.execute("UPDATE crawl_jobs SET status = 'pending' WHERE status IN ('crawling', 'queued');")
    await conn.execute("UPDATE documents SET root_document_id = id WHERE root_document_id IS NULL AND depth = 0;")
    await conn.execute("""
        UPDATE documents c
        SET root_document_id = p.root_document_id
        FROM documents p
        WHERE c.parent_id = p.id AND c.root_document_id IS NULL AND p.root_document_id IS NOT NULL;
    """)
    await conn.execute("""
        UPDATE documents c
        SET parent_id = r.id, depth = 1, root_document_id = r.id
        FROM documents r
        WHERE c.source_id = r.source_id AND r.depth = 0
          AND c.parent_id IS NOT NULL
          AND c.parent_id IN (SELECT id FROM documents WHERE source_id <> c.source_id);
    """)
    await conn.execute("""
        UPDATE documents c
        SET depth = p.depth + 1
        FROM documents p
        WHERE c.parent_id = p.id AND c.depth <> p.depth + 1;
    """)
    await conn.execute("""
        UPDATE documents
        SET status = 'failed'
        WHERE status = 'crawled' AND (content IS NULL OR length(trim(content)) = 0);
    """)

async def main():
    parser = argparse.ArgumentParser(description="Parallel multi-source crawler orchestrator for all 29 SAP Utilities sources.")
    parser.add_argument("--source-concurrency", type=int, default=settings.CRAWL_SOURCE_CONCURRENCY, help="Maximum concurrent source pipelines (default: 5)")
    parser.add_argument("--page-concurrency", type=int, default=settings.CRAWL_PAGE_CONCURRENCY, help="Maximum page request concurrency per source (default: 3)")
    parser.add_argument("--resume", action="store_true", help="Resume from existing database state without wiping pending queue")

    args = parser.parse_args()

    logger.info(f"Starting crawl_all (source_concurrency={args.source_concurrency}, page_concurrency={args.page_concurrency}, resume={args.resume})...")

    reports_dir = Path("storage/reports")
    reports_dir.mkdir(parents=True, exist_ok=True)

    await DatabasePool.initialize(min_size=2, max_size=30)

    try:
        async with DatabasePool.acquire() as conn:
            await prepare_database_before_crawl(conn)

        # Load Pre-flight Root Validation Report
        preflight_path = reports_dir / "root_validation.json"
        preflight_map = {}
        if preflight_path.exists():
            with open(preflight_path, "r", encoding="utf-8") as f:
                pf_data = json.load(f)
                preflight_map = {item["source_id"]: item for item in pf_data}

        async with DatabasePool.acquire() as conn:
            sources_rows = await conn.fetch("SELECT id, source_file, title, seed_url FROM sources ORDER BY id ASC;")
            sources = [dict(s) for s in sources_rows]

        semaphore = asyncio.Semaphore(args.source_concurrency)
        tasks = [
            process_source_worker(
                semaphore=semaphore,
                source=src,
                preflight_info=preflight_map.get(src["id"], {}),
                page_concurrency=args.page_concurrency,
                resume=args.resume
            )
            for src in sources
        ]

        logger.info(f"Launching parallel crawling across {len(sources)} sources with max {args.source_concurrency} active workers...")
        results = await asyncio.gather(*tasks)

        # Run SQL Validation
        async with DatabasePool.acquire() as conn:
            sql_validation = await run_sql_validation(conn)

        total_sources = len(results)
        successful_sources = sum(1 for r in results if r["status"] in ("SUCCESS", "PARTIAL_SUCCESS"))
        suspicious_sources = sum(1 for r in results if r["status"] == "SUSPICIOUS")
        failed_sources = sum(1 for r in results if r["status"] == "FAILED")

        total_discovered = sum(r["documents_discovered"] for r in results)
        total_crawled = sum(r["documents_crawled"] for r in results)
        total_sections = sum(r["sections"] for r in results)
        total_links = sum(r["document_links"] for r in results)
        total_errors = sum(r["error_count"] for r in results)
        total_pending = sum(r["pending_jobs"] for r in results)

        final_summary = {
            "orchestrator_summary": {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "source_concurrency": args.source_concurrency,
                "page_concurrency": args.page_concurrency,
                "total_sources": total_sources,
                "successful_sources": successful_sources,
                "suspicious_sources": suspicious_sources,
                "failed_sources": failed_sources,
                "total_documents_discovered": total_discovered,
                "total_documents_crawled": total_crawled,
                "total_sections": total_sections,
                "total_document_links": total_links,
                "total_errors": total_errors,
                "total_pending_jobs": total_pending,
            },
            "sql_validation": sql_validation,
            "sources_detail": results,
        }

        # Save JSON Report
        json_report_path = reports_dir / "crawl_report.json"
        with open(json_report_path, "w", encoding="utf-8") as f:
            json.dump(final_summary, f, indent=2, ensure_ascii=False)

        # Save Markdown Report
        md_report_path = reports_dir / "crawl_report.md"
        with open(md_report_path, "w", encoding="utf-8") as f:
            f.write("# SAP Utilities 29 Sources Crawl & Ingestion Report\n\n")
            f.write(f"**Generated**: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}\n\n")
            f.write("## Executive Summary\n\n")
            f.write(f"- **Total Sources**: {total_sources}\n")
            f.write(f"- **Successful Sources**: {successful_sources}\n")
            f.write(f"- **Suspicious Sources**: {suspicious_sources}\n")
            f.write(f"- **Failed Sources**: {failed_sources}\n")
            f.write(f"- **Total Documents Ingested**: {total_crawled}\n")
            f.write(f"- **Total Sections Saved**: {total_sections}\n")
            f.write(f"- **Total Document Links Stored**: {total_links}\n")
            f.write(f"- **SQL Integrity Checks Passed**: `{'YES' if sql_validation['is_valid'] else 'NO'}`\n\n")

            f.write("## SQL Validation Summary\n\n")
            f.write(f"- **Orphans (`parent_id IS NULL AND depth > 0`)**: {sql_validation['orphans_count']}\n")
            f.write(f"- **Invalid Depth Hierarchy**: {sql_validation['invalid_depth_count']}\n")
            f.write(f"- **Duplicate Canonical URLs**: {sql_validation['duplicate_urls_count']}\n")
            f.write(f"- **Missing Root Document ID**: {sql_validation['missing_root_id_count']}\n")
            f.write(f"- **Wrong Root Document ID**: {sql_validation['wrong_root_id_count']}\n")
            f.write(f"- **Empty Crawled Documents**: {sql_validation['empty_crawled_doc_count']}\n")
            f.write(f"- **Active Job Queue Breakdown**: `{json.dumps(sql_validation['active_crawl_jobs'])}`\n\n")

            f.write("## Per-Source Execution Details\n\n")
            f.write("| ID | PDF Source File | Status | Nodes | Crawled | Sections | Links | Duration (s) |\n")
            f.write("|---|---|---|---|---|---|---|---|\n")
            for r in results:
                f.write(f"| {r['source_id']} | {r['source_file']} | {r['status']} | {r['toc_node_count']} | {r['documents_crawled']} | {r['sections']} | {r['document_links']} | {r['crawl_duration_sec']} |\n")

        print("\n" + "=" * 90)
        print("SAP UTILITIES CRAWL ORCHESTRATION COMPLETE")
        print("=" * 90)
        print(f"Sources Processed : {total_sources} (SUCCESS: {successful_sources} | SUSPICIOUS: {suspicious_sources} | FAILED: {failed_sources})")
        print(f"Total Documents   : {total_crawled} ingested into Supabase")
        print(f"Total Sections    : {total_sections} saved")
        print(f"Total Links       : {total_links} stored")
        print(f"SQL Validation    : {'PASSED CLEAN' if sql_validation['is_valid'] else 'WARNINGS FOUND'}")
        print(f"JSON Report       : {json_report_path}")
        print(f"Markdown Report   : {md_report_path}")
        print("=" * 90 + "\n")

    finally:
        await close_browser()
        await DatabasePool.close()

if __name__ == "__main__":
    asyncio.run(main())
