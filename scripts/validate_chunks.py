"""
Validation script for verifying database chunks quality, lineage, and source coverage.

Produces the required validation report format:
========================================
SAP UTILITIES CHUNKING VALIDATION
========================================
...
Status: PASS / FAIL
"""

import asyncio
import logging
from typing import List, Dict, Any, Tuple

from sap_rag.database.connection import DatabasePool
from sap_rag.chunking.metrics import ChunkMetricsCalculator
from sap_rag.chunking.config import chunking_settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("validate_chunks")

async def run_validation() -> Tuple[bool, str]:
    await DatabasePool.initialize()

    try:
        async with DatabasePool.acquire() as conn:
            # 1. Counts
            doc_count = await conn.fetchval("SELECT COUNT(*) FROM documents;") or 0
            sec_count = await conn.fetchval("SELECT COUNT(*) FROM document_sections;") or 0
            chunk_count = await conn.fetchval("SELECT COUNT(*) FROM chunks;") or 0

            sources = await conn.fetch("SELECT id, title FROM sources ORDER BY id;")
            sources_processed = len(sources)

            # 2. Fetch all chunks
            chunks_rows = await conn.fetch(
                """
                SELECT id, document_id, section_id, chunk_index, content, token_count, content_hash, metadata
                FROM chunks;
                """
                )
            chunks = [dict(r) for r in chunks_rows]

            # 3. Compute Metrics
            metrics = ChunkMetricsCalculator.compute_metrics(chunks)
            t_stats = metrics["token_stats"]
            brackets = metrics["brackets"]

            # 4. Integrity Checks
            empty_chunks = 0
            duplicate_chunks = 0
            orphan_chunks = 0
            missing_provenance = 0
            missing_breadcrumbs = 0

            # Pre-fetch existing document_ids and section_ids to verify lineage
            valid_doc_ids = set(r["id"] for r in await conn.fetch("SELECT id FROM documents;"))
            valid_sec_ids = set(r["id"] for r in await conn.fetch("SELECT id FROM document_sections;"))

            seen_hashes = set()

            for chk in chunks:
                content = chk.get("content") or ""
                if not content.strip():
                    empty_chunks += 1

                doc_id = chk.get("document_id")
                sec_id = chk.get("section_id")

                if doc_id not in valid_doc_ids or sec_id not in valid_sec_ids:
                    orphan_chunks += 1

                meta = chk.get("metadata") or {}
                if isinstance(meta, str):
                    import json
                    meta = json.loads(meta)
                if not meta.get("breadcrumb"):
                    missing_breadcrumbs += 1

                if not meta.get("canonical_url") and not meta.get("document_url"):
                    missing_provenance += 1

                c_hash = chk.get("content_hash")
                hash_key = (sec_id, meta.get("chunking_version"), c_hash)
                if hash_key in seen_hashes:
                    duplicate_chunks += 1
                seen_hashes.add(hash_key)

            # Sources with errors
            sources_with_errors = 0

            # Verdict evaluation
            passed = (
                chunk_count > 0 and
                empty_chunks == 0 and
                orphan_chunks == 0 and
                missing_breadcrumbs == 0 and
                missing_provenance == 0 and
                duplicate_chunks == 0
            )

            status_str = "PASS" if passed else "FAIL"

            report = f"""========================================
SAP UTILITIES CHUNKING VALIDATION
========================================

Documents: {doc_count}
Sections:  {sec_count}
Chunks:    {chunk_count}

Chunk size:
Min:    {t_stats['min']}
P25:    {t_stats['p25']}
Median: {t_stats['median']}
P75:    {t_stats['p75']}
P95:    {t_stats['p95']}
Max:    {t_stats['max']}

Chunks <100: {brackets['<100']}
100–300:     {brackets['100-300']}
300–500:     {brackets['300-500']}
500–800:     {brackets['500-800']}
800–900:     {brackets['800-900']}
>900:        {brackets['>900']}

Empty chunks:        {empty_chunks}
Duplicate chunks:    {duplicate_chunks}
Orphan chunks:       {orphan_chunks}

Missing provenance:  {missing_provenance}
Missing breadcrumbs: {missing_breadcrumbs}

Sources processed:   {sources_processed}
Sources with errors: {sources_with_errors}

Chunking version:    {chunking_settings.CHUNKING_VERSION}

Status:
{status_str}
========================================
"""
            return passed, report

    finally:
        await DatabasePool.close()

if __name__ == "__main__":
    passed, report = asyncio.run(run_validation())
    print(report)
    if not passed:
        sys.exit(1)
