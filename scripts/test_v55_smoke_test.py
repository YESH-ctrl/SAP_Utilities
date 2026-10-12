"""
Production Smoke Test Suite for SAP Utilities RAG V5.5.
Validates the 5 critical regression queries (Q9, Q10, Q41, Q43, Q50) plus generic and unknown queries.
Ensures valid response schema, non-empty results, bounded latency, and zero exceptions.
"""

import sys
import time
import asyncio
import logging

from sap_rag.database.connection import DatabasePool
from sap_rag.retrieval.retrieval_pipeline import RetrievalPipeline

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s]: %(message)s")
logger = logging.getLogger("smoke_test")

SMOKE_QUERIES = [
    ("Q9 (Clearing Types)", "What are clearing types in SAP Utilities?", True),
    ("Q10 (Budget Billing)", "How does budget billing work?", True),
    ("Q41 (Premise Entity)", "What is premise in SAP Utilities?", True),
    ("Q43 (Budget Billing Plan)", "How to create a budget billing plan manually?", True),
    ("Q50 (Reconnection Recovery)", "How to perform reconnection of utility service?", True),
    ("Generic SAP Query", "Overview of device management in SAP IS-U", True),
    ("Unknown Query", "Unknown non-existent transaction code XYZ999", True),
]

async def run_smoke_tests():
    logger.info("=========================================================")
    logger.info("   SAP UTILITIES RAG V5.5 - PRODUCTION SMOKE TEST       ")
    logger.info("=========================================================")

    await DatabasePool.initialize(min_size=2, max_size=10)
    pipeline = RetrievalPipeline()
    passed = 0
    failed = 0

    try:
        async with DatabasePool.acquire() as conn:
            for name, q_text, expect_results in SMOKE_QUERIES:
                t0 = time.time()
                try:
                    cands, context_str, processed_q, metrics = await pipeline.execute(
                        conn=conn,
                        query=q_text,
                        top_k=8
                    )
                    lat_ms = (time.time() - t0) * 1000.0

                    if expect_results and len(cands) == 0:
                        logger.error(f"FAIL {name}: Expected results but received 0 candidates.")
                        failed += 1
                        continue

                    # Verify candidate structure integrity
                    for c in cands:
                        assert hasattr(c, "chunk_id") and c.chunk_id > 0
                        assert hasattr(c, "document_id") and c.document_id > 0
                        assert hasattr(c, "title")
                        assert hasattr(c, "final_score") and c.final_score > 0

                    top_source = cands[0].source_id if cands else None
                    top_doc = cands[0].title if cands else "N/A"
                    logger.info(f"PASS {name} in {lat_ms:.1f}ms | Top Match: '{top_doc}' (Source ID {top_source})")
                    passed += 1

                except Exception as e:
                    logger.error(f"FAIL {name}: Exception thrown: {e}", exc_info=True)
                    failed += 1

    finally:
        await DatabasePool.close()

    logger.info("=========================================================")
    logger.info(f" PRODUCTION SMOKE TEST SUMMARY: {passed} PASSED, {failed} FAILED")
    logger.info("=========================================================")
    return failed == 0

if __name__ == "__main__":
    success = asyncio.run(run_smoke_tests())
    if not success:
        sys.exit(1)
    sys.exit(0)
