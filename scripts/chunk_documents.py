"""
CLI script for executing SAP Utilities Semantic Chunking Engine.

Usage:
    python -m scripts.chunk_documents --dry-run --source-id 1
    python -m scripts.chunk_documents --document-id 101
    python -m scripts.chunk_documents --source-id 11
    python -m scripts.chunk_documents --all
"""

import argparse
import asyncio
import logging
import sys
from typing import List, Dict, Any

from sap_rag.database.connection import DatabasePool
from sap_rag.chunking.service import ChunkingService
from sap_rag.chunking.breadcrumb import BreadcrumbBuilder
from sap_rag.chunking.metrics import ChunkMetricsCalculator
from sap_rag.chunking.config import chunking_settings

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("chunk_documents")

async def main():
    parser = argparse.ArgumentParser(description="SAP Utilities Semantic Chunking Engine")
    parser.add_argument("--document-id", type=int, help="Chunk a single document by ID")
    parser.add_argument("--source-id", type=int, help="Chunk all documents in a source by source ID")
    parser.add_argument("--all", action="store_true", help="Chunk all documents across all 29 sources")
    parser.add_argument("--dry-run", action="store_true", help="Dry run mode (does not modify database)")
    parser.add_argument("--version", type=str, default=chunking_settings.CHUNKING_VERSION, help="Chunking version string")

    args = parser.parse_args()

    if not (args.document_id or args.source_id or args.all):
        parser.error("Must specify one of --document-id, --source-id, or --all")

    chunking_settings.CHUNKING_VERSION = args.version
    service = ChunkingService()

    await DatabasePool.initialize(min_size=2, max_size=15)

    try:
        async with DatabasePool.acquire() as conn:
            if args.document_id:
                logger.info(f"Processing single document ID: {args.document_id} (dry_run={args.dry_run})")
                res = await service.process_document(conn, doc_id=args.document_id, dry_run=args.dry_run)
                _print_dry_run_summary([res], dry_run=args.dry_run)

            elif args.source_id:
                logger.info(f"Processing source ID: {args.source_id} (dry_run={args.dry_run})")
                res = await service.process_source(conn, source_id=args.source_id, dry_run=args.dry_run)
                _print_dry_run_summary(res["doc_summaries"], dry_run=args.dry_run)

            elif args.all:
                logger.info(f"Processing all sources across database (dry_run={args.dry_run})")
                sources = await conn.fetch("SELECT id, title FROM sources ORDER BY id;")
                all_doc_summaries = []

                for s in sources:
                    logger.info(f"--- Processing Source #{s['id']}: {s['title']} ---")
                    s_res = await service.process_source(conn, source_id=s["id"], dry_run=args.dry_run)
                    all_doc_summaries.extend(s_res["doc_summaries"])

                _print_dry_run_summary(all_doc_summaries, dry_run=args.dry_run)

    finally:
        await DatabasePool.close()

def _print_dry_run_summary(doc_summaries: List[Dict[str, Any]], dry_run: bool):
    total_docs = len(doc_summaries)
    total_sections_proc = sum(d["sections_processed"] for d in doc_summaries)
    total_sections_skip = sum(d["sections_skipped"] for d in doc_summaries)

    all_chunks = []
    for d in doc_summaries:
        all_chunks.extend(d["chunks"])

    metrics = ChunkMetricsCalculator.compute_metrics(all_chunks)
    t_stats = metrics["token_stats"]
    brackets = metrics["brackets"]

    mode_label = "DRY RUN SUMMARY (No DB changes)" if dry_run else "LIVE CHUNKING EXECUTION SUMMARY"

    print("\n" + "=" * 60)
    print(f" {mode_label}")
    print("=" * 60)
    print(f"Documents selected     : {total_docs}")
    print(f"Sections processed     : {total_sections_proc}")
    print(f"Sections skipped       : {total_sections_skip}")
    print(f"Total chunks generated : {len(all_chunks)}")
    print("-" * 60)
    print("Token Statistics:")
    print(f"  Min tokens           : {t_stats['min']}")
    print(f"  P25 tokens           : {t_stats['p25']}")
    print(f"  Median tokens        : {t_stats['median']}")
    print(f"  P75 tokens           : {t_stats['p75']}")
    print(f"  P95 tokens           : {t_stats['p95']}")
    print(f"  Max tokens           : {t_stats['max']}")
    print(f"  Average tokens       : {t_stats['mean']}")
    print("-" * 60)
    print("Token Size Brackets:")
    for b_name, b_count in brackets.items():
        print(f"  {b_name:<10} : {b_count}")
    print("=" * 60)

    if all_chunks:
        print("\n--- SAMPLE CHUNKS (First 3) ---")
        for idx, chk in enumerate(all_chunks[:3]):
            print(f"\n[CHUNK #{idx+1} | Document ID: {chk['document_id']} | Section ID: {chk['section_id']} | Tokens: {chk['token_count']}]")
            print("-" * 50)
            preview = chk["content"][:350] + ("..." if len(chk["content"]) > 350 else "")
            safe_preview = preview.encode(sys.stdout.encoding or "utf-8", errors="replace").decode(sys.stdout.encoding or "utf-8")
            print(safe_preview)
        print("\n" + "=" * 60)

if __name__ == "__main__":
    asyncio.run(main())
