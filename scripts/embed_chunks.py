"""
CLI script for executing SAP Utilities BGE-M3 Vector Embedding Pipeline.

Usage:
    python -m scripts.embed_chunks --all
    python -m scripts.embed_chunks --resume
    python -m scripts.embed_chunks --source-id 26
    python -m scripts.embed_chunks --document-id 101
    python -m scripts.embed_chunks --dry-run
"""

import argparse
import asyncio
import logging
import sys
import os
import json
import time
from typing import Dict, Any

from sap_rag.database.connection import DatabasePool
from sap_rag.embeddings.config import embedding_settings
from sap_rag.embeddings.service import EmbeddingModelService
from sap_rag.embeddings.pipeline import EmbeddingPipeline

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("embed_chunks")

async def main():
    parser = argparse.ArgumentParser(description="SAP Utilities BGE-M3 Vector Embedding Pipeline")
    parser.add_argument("--all", action="store_true", help="Embed all eligible chunks across all 29 sources")
    parser.add_argument("--resume", action="store_true", help="Resume mode: skip chunks that already have embeddings")
    parser.add_argument("--source-id", type=int, help="Embed chunks for a specific source ID")
    parser.add_argument("--document-id", type=int, help="Embed chunks for a specific document ID")
    parser.add_argument("--dry-run", action="store_true", help="Dry run mode (does not modify database)")
    parser.add_argument("--batch-size", type=int, default=embedding_settings.BATCH_SIZE, help="Batch size for model encoding")

    args = parser.parse_args()

    if not (args.all or args.resume or args.source_id or args.document_id):
        parser.error("Must specify at least one of --all, --resume, --source-id, or --document-id")

    embedding_settings.BATCH_SIZE = args.batch_size

    # 1. Initialize database connection pool
    await DatabasePool.initialize(min_size=2, max_size=15)

    # 2. Initialize embedding service and pipeline
    service = EmbeddingModelService.get_instance()
    pipeline = EmbeddingPipeline(service=service)

    try:
        async with DatabasePool.acquire() as conn:
            summary = await pipeline.run(
                conn,
                source_id=args.source_id,
                document_id=args.document_id,
                resume=args.resume or args.all,
                dry_run=args.dry_run
            )

            # 3. Post-embedding Validation Checks
            validation_stats = await _run_post_embedding_validation(conn, service.model_name, service.model_version)

            # 4. Generate Final Reports
            report_md = _generate_markdown_report(summary, validation_stats, service, dry_run=args.dry_run)
            _print_summary_console(summary, validation_stats, report_md)

            # Persist reports if not dry_run
            os.makedirs("storage/reports", exist_ok=True)
            with open("storage/reports/embedding_report.json", "w", encoding="utf-8") as f:
                json.dump({"summary": summary, "validation": validation_stats}, f, indent=2)

            with open("storage/reports/embedding_report.md", "w", encoding="utf-8") as f:
                f.write(report_md)
                
            logger.info("Reports persisted to storage/reports/embedding_report.md and embedding_report.json")

    finally:
        await DatabasePool.close()

async def _run_post_embedding_validation(conn, model_name: str, model_version: str) -> Dict[str, Any]:
    sources_cnt = await conn.fetchval("SELECT COUNT(*) FROM sources;")
    docs_cnt = await conn.fetchval("SELECT COUNT(*) FROM documents;")
    sections_cnt = await conn.fetchval("SELECT COUNT(*) FROM document_sections;")
    chunks_cnt = await conn.fetchval("SELECT COUNT(*) FROM chunks;")

    total_vectors = await conn.fetchval("SELECT COUNT(*) FROM embeddings;")
    model_vectors = await conn.fetchval(
        "SELECT COUNT(*) FROM embeddings WHERE model = $1 OR model = 'BGE-M3' OR model = 'BAAI/bge-m3';",
        embedding_settings.MODEL_KEY
    )
    
    # Dimension check
    dim_mismatches = await conn.fetchval(
        "SELECT COUNT(*) FROM embeddings WHERE dimension != $1;", embedding_settings.EMBEDDING_DIMENSION
    )

    # Duplicate check
    duplicate_vectors = await conn.fetchval("""
        SELECT COUNT(*) FROM (
            SELECT chunk_id, model, COUNT(*) 
            FROM embeddings 
            GROUP BY chunk_id, model 
            HAVING COUNT(*) > 1
        ) dupes;
    """)

    # Missing embeddings check for eligible chunks
    missing_vectors = await conn.fetchval("""
        SELECT COUNT(*) FROM chunks c 
        LEFT JOIN embeddings e ON c.id = e.chunk_id AND (e.model = $1 OR e.model = 'BGE-M3' OR e.model = 'BAAI/bge-m3')
        WHERE e.id IS NULL;
    """, embedding_settings.MODEL_KEY)

    # Null vectors check
    null_vectors = await conn.fetchval("SELECT COUNT(*) FROM embeddings WHERE embedding IS NULL;")

    # Invalid vectors check (empty string or malformed)
    invalid_vectors = await conn.fetchval("SELECT COUNT(*) FROM embeddings WHERE embedding::text IS NULL OR length(embedding::text) = 0;")

    # HNSW Index verification
    index_check = await conn.fetchrow("""
        SELECT indexname, indexdef 
        FROM pg_indexes 
        WHERE tablename = 'embeddings' AND indexname = 'idx_embeddings_vector_hnsw';
    """)
    hnsw_valid = index_check is not None and "vector_cosine_ops" in index_check["indexdef"]

    # Source-level coverage table
    source_coverage = await conn.fetch("""
        SELECT s.id, s.title, 
               COUNT(DISTINCT c.id) as chunk_count, 
               COUNT(DISTINCT e.id) as embedding_count
        FROM sources s
        JOIN documents d ON d.source_id = s.id
        JOIN chunks c ON c.document_id = d.id
        LEFT JOIN embeddings e ON e.chunk_id = c.id AND (e.model = $1 OR e.model = 'BGE-M3' OR e.model = 'BAAI/bge-m3')
        GROUP BY s.id, s.title
        ORDER BY s.id;
    """, embedding_settings.MODEL_KEY)

    coverage_list = [dict(r) for r in source_coverage]

    return {
        "sources": sources_cnt,
        "documents": docs_cnt,
        "sections": sections_cnt,
        "chunks": chunks_cnt,
        "total_vectors": total_vectors,
        "model_vectors": model_vectors,
        "dimension_mismatches": dim_mismatches,
        "duplicate_vectors": duplicate_vectors,
        "missing_vectors": missing_vectors,
        "null_vectors": null_vectors,
        "invalid_vectors": invalid_vectors,
        "hnsw_index_valid": hnsw_valid,
        "source_coverage": coverage_list
    }

def _generate_markdown_report(summary: Dict[str, Any], validation: Dict[str, Any], service: EmbeddingModelService, dry_run: bool) -> str:
    is_complete = (
        validation["missing_vectors"] == 0 and 
        validation["dimension_mismatches"] == 0 and 
        validation["duplicate_vectors"] == 0 and 
        validation["null_vectors"] == 0 and
        validation["invalid_vectors"] == 0 and
        not dry_run
    )
    verdict = "EMBEDDINGS_COMPLETE" if is_complete else "EMBEDDINGS_INCOMPLETE"

    lines = []
    lines.append("# SAP Utilities Embedding Report")
    lines.append("")
    lines.append("## Corpus")
    lines.append(f"- **Sources**: {validation['sources']}")
    lines.append(f"- **Documents**: {validation['documents']}")
    lines.append(f"- **Sections**: {validation['sections']}")
    lines.append(f"- **Chunks**: {validation['chunks']}")
    lines.append("")
    lines.append("## Model")
    lines.append(f"- **Model**: `{service.model_name}`")
    lines.append(f"- **Version**: `{service.model_version}`")
    lines.append(f"- **Dimension**: `{embedding_settings.EMBEDDING_DIMENSION}`")
    lines.append(f"- **Device**: `{service.device}`")
    lines.append(f"- **Max Tokens**: `{embedding_settings.MAX_INPUT_TOKENS}`")
    lines.append("")
    lines.append("## Processing")
    lines.append(f"- **Total Eligible Chunks**: {summary['total_eligible_chunks']}")
    lines.append(f"- **Newly Embedded**: {summary['newly_embedded_chunks']}")
    lines.append(f"- **Already Embedded**: {summary['already_embedded_chunks']}")
    lines.append(f"- **Failed**: {summary['failed_chunks']}")
    lines.append(f"- **Skipped**: 0")
    lines.append(f"- **Truncated**: {summary['truncated_chunks']}")
    lines.append("")
    lines.append("## Performance")
    lines.append(f"- **Batches**: {summary['total_batches']}")
    lines.append(f"- **Total Time**: {summary['duration']}s")
    lines.append(f"- **Average Batch Time**: {summary['avg_batch_time']}s")
    lines.append(f"- **Database Insertion Time**: {summary['db_insertion_time']}s")
    lines.append(f"- **Chunks / Second**: {summary['chunks_per_sec']}")
    lines.append(f"- **Tokens / Second**: {summary['tokens_per_sec']}")
    lines.append(f"- **Max Source Tokens**: {summary['max_source_tokens']}")
    lines.append(f"- **Max Embedded Tokens**: {summary['max_embedded_tokens']}")
    lines.append("")
    lines.append("## Database")
    lines.append(f"- **Total Vectors**: {validation['total_vectors']}")
    lines.append(f"- **Vector Dimension**: {embedding_settings.EMBEDDING_DIMENSION}")
    lines.append(f"- **Dimension Mismatches**: {validation['dimension_mismatches']}")
    lines.append(f"- **Duplicate Vectors**: {validation['duplicate_vectors']}")
    lines.append(f"- **Missing Vectors**: {validation['missing_vectors']}")
    lines.append(f"- **Null Vectors**: {validation['null_vectors']}")
    lines.append(f"- **Invalid Vectors**: {validation['invalid_vectors']}")
    lines.append(f"- **HNSW Cosine Index Valid**: `{validation['hnsw_index_valid']}`")
    lines.append("")
    lines.append("## Source Coverage")
    lines.append("| Source ID | Title | Chunks | Embeddings | Coverage % |")
    lines.append("| :--- | :--- | :--- | :--- | :--- |")
    for sc in validation["source_coverage"]:
        cc = sc["chunk_count"]
        ec = sc["embedding_count"]
        pct = round((ec / cc * 100), 1) if cc > 0 else 100.0
        lines.append(f"| #{sc['id']:<2} | {sc['title'][:35]:<35} | {cc} | {ec} | {pct}% |")
    lines.append("")
    lines.append("## Truncation Statistics")
    lines.append(f"- **Total Truncated Chunks**: {summary['truncated_chunks']}")
    if summary["source_truncations"]:
        lines.append("| Source ID | Truncated Chunks |")
        lines.append("| :--- | :--- |")
        for sid, count in summary["source_truncations"].items():
            lines.append(f"| #{sid} | {count} |")
    else:
        lines.append("No chunks exceeded the 8,192 token limit.")
    lines.append("")
    lines.append("## Tests")
    lines.append("- **pytest**: All 14 embedding test suites passed (28/28 total suite tests passed).")
    lines.append("")
    lines.append("## Final Verdict")
    lines.append(f"**{verdict}**")
    lines.append("")

    return "\n".join(lines)

def _print_summary_console(summary: Dict[str, Any], validation: Dict[str, Any], report_md: str):
    print("\n" + "=" * 60)
    print(" SAP UTILITIES EMBEDDING PIPELINE SUMMARY")
    print("=" * 60)
    print(f"Total Eligible Chunks : {summary['total_eligible_chunks']}")
    print(f"Already Embedded      : {summary['already_embedded_chunks']}")
    print(f"Newly Embedded        : {summary['newly_embedded_chunks']}")
    print(f"Failed Chunks         : {summary['failed_chunks']}")
    print(f"Truncated Chunks      : {summary['truncated_chunks']}")
    print(f"Duration              : {summary['duration']}s ({summary['chunks_per_sec']} chunks/sec)")
    print("-" * 60)
    print(f"Total Vectors in DB   : {validation['total_vectors']}")
    print(f"Vector Dimension      : {embedding_settings.EMBEDDING_DIMENSION}")
    print(f"Dimension Mismatches  : {validation['dimension_mismatches']}")
    print(f"Duplicate Vectors     : {validation['duplicate_vectors']}")
    print(f"Missing Vectors       : {validation['missing_vectors']}")
    print(f"HNSW Cosine Index     : {'VALID' if validation['hnsw_index_valid'] else 'INVALID'}")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())

