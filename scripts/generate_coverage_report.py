import asyncio
import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List

from sap_rag.database.connection import DatabasePool

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("coverage_report")

async def generate_coverage_report() -> Dict[str, Any]:
    await DatabasePool.initialize()
    reports_dir = Path("storage/reports")
    reports_dir.mkdir(parents=True, exist_ok=True)

    try:
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

            report_items = []

            for src in sources:
                source_id = src["id"]
                title = src["title"]
                source_file = src["source_file"]
                seed_url = src["seed_url"]

                pf_info = preflight_map.get(source_id, {})
                toc_nodes = pf_info.get("node_count", 0)

                # Jobs discovered (total jobs in queue for this source)
                total_jobs = await conn.fetchval(
                    "SELECT count(*) FROM crawl_jobs WHERE source_id = $1;",
                    source_id
                )
                pending_jobs = await conn.fetchval(
                    "SELECT count(*) FROM crawl_jobs WHERE source_id = $1 AND status IN ('pending', 'queued', 'crawling');",
                    source_id
                )
                crawled_docs_for_source = await conn.fetchval(
                    "SELECT count(*) FROM documents WHERE source_id = $1 AND status = 'crawled';",
                    source_id
                )

                # Also count matching canonical URLs across any source (due to cross-source deduplication)
                jobs_urls = await conn.fetch("SELECT url FROM crawl_jobs WHERE source_id = $1;", source_id)
                urls = [j["url"] for j in jobs_urls]
                matching_crawled_total = 0
                if urls:
                    matching_crawled_total = await conn.fetchval(
                        "SELECT count(*) FROM documents WHERE canonical_url = ANY($1::text[]) AND status = 'crawled';",
                        urls
                    )

                # Total documents discovered (unique URLs in jobs + root)
                docs_discovered = max(1, total_jobs)
                # Effective documents crawled (direct + shared deduplicated)
                docs_crawled_effective = max(crawled_docs_for_source, matching_crawled_total)

                coverage_pct = round((docs_crawled_effective / docs_discovered) * 100, 1) if docs_discovered > 0 else 0.0

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

                is_suspicious = pf_info.get("status") == "SUSPICIOUS" or toc_nodes > 300
                # Flag if TOC nodes > 0 AND documents crawled << documents discovered (without cross-source deduplication explanation)
                flagged = False
                flag_reason = None
                if toc_nodes > 0 and docs_crawled_effective < docs_discovered:
                    flagged = True
                    flag_reason = f"Crawled ({docs_crawled_effective}) < Discovered ({docs_discovered})"
                elif is_suspicious:
                    flagged = True
                    flag_reason = "TOC size suspicious (>300 nodes)"

                report_items.append({
                    "source_id": source_id,
                    "source_file": source_file,
                    "title": title,
                    "root_url": seed_url,
                    "toc_nodes": toc_nodes,
                    "documents_discovered": docs_discovered,
                    "documents_crawled_direct": crawled_docs_for_source,
                    "documents_crawled_effective": docs_crawled_effective,
                    "crawl_coverage_percentage": coverage_pct,
                    "sections": sections_count,
                    "links": links_count,
                    "max_depth": max_depth,
                    "pending_jobs": pending_jobs,
                    "suspicious_status": is_suspicious,
                    "flagged": flagged,
                    "flag_reason": flag_reason,
                })

        summary = {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "total_sources": len(report_items),
            "valid_sources": sum(1 for r in report_items if not r["suspicious_status"]),
            "suspicious_sources": sum(1 for r in report_items if r["suspicious_status"]),
            "total_documents_discovered": sum(r["documents_discovered"] for r in report_items),
            "total_documents_crawled_effective": sum(r["documents_crawled_effective"] for r in report_items),
            "average_coverage_percentage": round(sum(r["crawl_coverage_percentage"] for r in report_items) / len(report_items), 1),
            "sources": report_items,
        }

        # Save JSON
        json_path = reports_dir / "coverage_report.json"
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)

        # Save Markdown
        md_path = reports_dir / "coverage_report.md"
        with open(md_path, "w", encoding="utf-8") as f:
            f.write("# SAP Utilities 29 Sources Crawl Coverage Report\n\n")
            f.write(f"**Generated**: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}\n\n")
            f.write("## Executive Summary\n\n")
            f.write(f"- **Total Sources**: {summary['total_sources']}\n")
            f.write(f"- **Valid Sources**: {summary['valid_sources']}\n")
            f.write(f"- **Suspicious Sources**: {summary['suspicious_sources']}\n")
            f.write(f"- **Total Discovered Documents**: {summary['total_documents_discovered']}\n")
            f.write(f"- **Total Effective Crawled Documents**: {summary['total_documents_crawled_effective']}\n")
            f.write(f"- **Average Coverage**: {summary['average_coverage_percentage']}%\n\n")

            f.write("## Per-Source Coverage Details\n\n")
            f.write("| ID | Title | TOC Nodes | Discovered | Crawled (Direct) | Crawled (Effective) | Coverage % | Sections | Links | Depth | Pending | Suspicious | Flag |\n")
            f.write("|---|---|---|---|---|---|---|---|---|---|---|---|---|\n")
            for r in report_items:
                flag_str = f"⚠️ {r['flag_reason']}" if r["flagged"] else "OK"
                susp_str = "YES" if r["suspicious_status"] else "NO"
                f.write(f"| {r['source_id']} | {r['title'][:35]} | {r['toc_nodes']} | {r['documents_discovered']} | {r['documents_crawled_direct']} | {r['documents_crawled_effective']} | {r['crawl_coverage_percentage']}% | {r['sections']} | {r['links']} | {r['max_depth']} | {r['pending_jobs']} | {susp_str} | {flag_str} |\n")

        print("\n" + "=" * 90)
        print("SAP UTILITIES CRAWL COVERAGE REPORT GENERATED")
        print("=" * 90)
        print(f"JSON Report : {json_path}")
        print(f"MD Report   : {md_path}")
        print("=" * 90 + "\n")

        return summary

    finally:
        await DatabasePool.close()

if __name__ == "__main__":
    asyncio.run(generate_coverage_report())
