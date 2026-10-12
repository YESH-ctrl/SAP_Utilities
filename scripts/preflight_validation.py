import asyncio
import json
import logging
import os
import sys
from pathlib import Path
from typing import Dict, Any, List

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from sap_rag.crawler.config import settings
from sap_rag.crawler.fetcher import HTTPFetcher, close_browser
from sap_rag.crawler.toc_parser import TOCParser
from sap_rag.crawler.content_parser import ContentParser
from sap_rag.database.connection import DatabasePool

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("preflight_validation")

async def validate_source_root(fetcher: HTTPFetcher, source: Dict[str, Any]) -> Dict[str, Any]:
    source_id = source["id"]
    source_file = source.get("source_file", f"Source #{source_id}")
    url = source.get("seed_url")
    title = source.get("title", f"Source #{source_id}")

    logger.info(f"Pre-flight validating Source #{source_id}: {title} ({url})")

    try:
        raw_html, final_url, used_playwright = await fetcher.fetch(url)
        parsed_doc = ContentParser.parse_document(raw_html, final_url or url)
        parsed_toc = TOCParser.parse_toc(raw_html, final_url or url)

        node_count = len(parsed_toc.nodes)
        max_depth = max([n.level for n in parsed_toc.nodes], default=0)
        top_level = [n.title for n in parsed_toc.nodes if n.level == 1]

        if node_count > settings.CRAWLER_MAX_ROOT_TOC_NODES:
            status = "SUSPICIOUS"
            logger.warning(f"ROOT_TOC_SUSPICIOUS for Source #{source_id}: {node_count} nodes > threshold {settings.CRAWLER_MAX_ROOT_TOC_NODES}")
        elif node_count == 0:
            status = "SUSPICIOUS"
            logger.warning(f"ROOT_TOC_SUSPICIOUS for Source #{source_id}: 0 nodes extracted")
        else:
            status = "VALID"

        return {
            "source_id": source_id,
            "source_file": source_file,
            "title": parsed_doc.title or title,
            "root_url": final_url or url,
            "status": status,
            "node_count": node_count,
            "unique_urls": parsed_toc.unique_urls,
            "duplicate_urls_removed": parsed_toc.duplicate_urls_removed,
            "ignored_navigation": parsed_toc.ignored_navigation_links,
            "external_links": parsed_toc.external_links,
            "max_depth": max_depth,
            "top_level_nodes_count": len(top_level),
            "top_level_sample": top_level[:10],
            "used_playwright": used_playwright,
            "error": None,
        }
    except Exception as e:
        logger.error(f"Pre-flight failed for Source #{source_id} ({url}): {e}")
        return {
            "source_id": source_id,
            "source_file": source_file,
            "title": title,
            "root_url": url,
            "status": "FAILED",
            "node_count": 0,
            "unique_urls": 0,
            "duplicate_urls_removed": 0,
            "ignored_navigation": 0,
            "external_links": 0,
            "max_depth": 0,
            "top_level_nodes_count": 0,
            "top_level_sample": [],
            "used_playwright": False,
            "error": str(e),
        }

async def main():
    logger.info("Starting Pre-Flight Root Validation Pass for all 29 sources...")
    reports_dir = Path("storage/reports")
    reports_dir.mkdir(parents=True, exist_ok=True)

    await DatabasePool.initialize()
    fetcher = HTTPFetcher()

    try:
        async with DatabasePool.acquire() as conn:
            sources = await conn.fetch("SELECT id, source_file, title, seed_url FROM sources ORDER BY id ASC;")
            sources_list = [dict(s) for s in sources]

        results = []
        for src in sources_list:
            res = await validate_source_root(fetcher, src)
            results.append(res)

        report_path = reports_dir / "root_validation.json"
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2, ensure_ascii=False)

        valid_count = sum(1 for r in results if r["status"] == "VALID")
        suspicious_count = sum(1 for r in results if r["status"] == "SUSPICIOUS")
        failed_count = sum(1 for r in results if r["status"] == "FAILED")

        print("\n" + "=" * 90)
        print(f"PRE-FLIGHT ROOT VALIDATION REPORT ({len(results)} SOURCES)")
        print("=" * 90)
        print(f"{'ID':<4} | {'STATUS':<11} | {'NODES':<6} | {'UNIQUE':<6} | {'TITLE':<45}")
        print("-" * 90)
        for r in results:
            title_trunc = (r["title"][:42] + "...") if len(r["title"]) > 45 else r["title"]
            print(f"{r['source_id']:<4} | {r['status']:<11} | {r['node_count']:<6} | {r['unique_urls']:<6} | {title_trunc:<45}")
        print("=" * 90)
        print(f"SUMMARY: VALID={valid_count} | SUSPICIOUS={suspicious_count} | FAILED={failed_count}")
        print(f"Full report written to: {report_path}\n")

    finally:
        await close_browser()
        await DatabasePool.close()

if __name__ == "__main__":
    asyncio.run(main())
