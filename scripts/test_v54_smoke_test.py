"""
V5.4 Standalone Smoke Test Suite for Production Rollback Verification.
Operates strictly against V5.4 baseline configuration without depending on V5.5 features.
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
logger = logging.getLogger("v54_smoke_test")

V54_SMOKE_QUERIES = [
    ("Q9 (Clearing Types)", "What are clearing types in SAP Utilities?"),
    ("Q10 (Budget Billing)", "How does budget billing work?"),
    ("Q41 (Premise Entity)", "What is premise in SAP Utilities?"),
    ("Q43 (Budget Billing Plan)", "How to create a budget billing plan manually?"),
    ("Q50 (Reconnection)", "How to perform reconnection of utility service?")
]

async def run_v54_smoke_tests():
    logger.info("=========================================================")
    logger.info("   SAP UTILITIES RAG V5.4 - STANDALONE ROLLBACK SMOKE   ")
    logger.info("=========================================================")

    await DatabasePool.initialize(min_size=2, max_size=10)
    pipeline = RetrievalPipeline()
    passed = 0
    failed = 0

    try:
        async with DatabasePool.acquire() as conn:
            for name, q_text in V54_SMOKE_QUERIES:
                t0 = time.time()
                try:
                    cands, context_str, processed_q, metrics = await pipeline.execute(
                        conn=conn,
                        query=q_text,
                        top_k=5,
                        config_name="V5_FINAL",
                        relevance_weight=0.0015,
                        enable_top1_protection=True,
                        max_per_doc=10,
                        hierarchy_recovery_mode="H1"
                    )
                    lat_ms = (time.time() - t0) * 1000.0

                    if len(cands) == 0:
                        logger.error(f"FAIL {name}: Received 0 candidates in V5.4 baseline mode.")
                        failed += 1
                        continue

                    top_doc = cands[0].title if cands else "N/A"
                    logger.info(f"PASS {name} (V5.4 Baseline) in {lat_ms:.1f}ms | Top Match: '{top_doc}'")
                    passed += 1

                except Exception as e:
                    logger.error(f"FAIL {name}: V5.4 Exception thrown: {e}", exc_info=True)
                    failed += 1

    finally:
        await DatabasePool.close()

    logger.info("=========================================================")
    logger.info(f" V5.4 ROLLBACK SMOKE SUMMARY: {passed} PASSED, {failed} FAILED")
    logger.info("=========================================================")
    return failed == 0

if __name__ == "__main__":
    success = asyncio.run(run_v54_smoke_tests())
    if not success:
        sys.exit(1)
    sys.exit(0)
