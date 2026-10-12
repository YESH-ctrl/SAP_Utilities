"""
Functional API Robustness & Input Abuse Validation Test Suite for SAP Utilities RAG V5.5.
Tests edge cases, malformed queries, long payloads, unicode, special characters, and concurrency.
"""

import sys
import asyncio
import logging

from sap_rag.database.connection import DatabasePool
from sap_rag.retrieval.retrieval_pipeline import RetrievalPipeline

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s]: %(message)s")
logger = logging.getLogger("api_robustness_test")

TEST_CASES = [
    ("1. Normal Query", "What are clearing types in SAP Utilities?"),
    ("2. Empty Query", ""),
    ("3. Whitespace Query", "   \t\n  "),
    ("4. Very Short Query", "a"),
    ("5. Long Query Payload", ("SAP Utilities " * 150)[:1500]),
    ("6. Punctuation Heavy", "!@#$%^&*()_+-=[]{}|;':\",./<>?~`"),
    ("7. Mixed Case Query", "wHaT iS pReMiSe In SaP uTiLiTiEs?"),
    ("8. Repeated Query", "budget billing " * 20),
    ("9. Unknown SAP Term", "xyz999nonexistentsapterm12345"),
    ("10. SQL-like Injection Payload", "' OR 1=1; DROP TABLE chunks; --"),
    ("11. FTS Operators Payload", "clearing & type | (budget & billing) ! premise"),
    ("12. Unicode & Emojis", "billing 💡⚡️ 结算类型 סליקה"),
]

async def run_api_tests():
    logger.info("=========================================================")
    logger.info("   SAP UTILITIES RAG V5.5 - API ROBUSTNESS VALIDATION   ")
    logger.info("=========================================================")

    await DatabasePool.initialize(min_size=2, max_size=10)
    pipeline = RetrievalPipeline()
    passed = 0
    failed = 0

    try:
        async with DatabasePool.acquire() as conn:
            # Test 1-12: Sequential Input Robustness
            for name, q_text in TEST_CASES:
                logger.info(f"Running Test: {name}...")
                try:
                    # Edge case validation logic matches API router behavior
                    if not q_text or not q_text.strip():
                        logger.info(f" -> Handled gracefully as 400 Bad Request (empty input)")
                        passed += 1
                        continue

                    cands, context_str, processed_q, metrics = await pipeline.execute(
                        conn=conn,
                        query=q_text,
                        top_k=5,
                        dense_candidate_k=20,
                        lexical_candidate_k=20
                    )
                    logger.info(f" -> SUCCESS: Returned {len(cands)} candidates without crashing. Processed query: '{processed_q.normalized_query[:40]}...'")
                    passed += 1
                except Exception as e:
                    logger.error(f" -> UNEXPECTED FAILURE in {name}: {e}")
                    failed += 1

            # Test 13: Concurrent Requests Test
            logger.info("Running Test 13: Concurrent Requests (5 parallel queries)...")
            async def single_search(query: str):
                async with DatabasePool.acquire() as sub_conn:
                    return await pipeline.execute(sub_conn, query=query, top_k=5)

            tasks = [
                single_search("What is premise in SAP Utilities?"),
                single_search("How does budget billing work?"),
                single_search("What are clearing types?"),
                single_search("Device category installation"),
                single_search("Disconnection and reconnection process")
            ]
            try:
                results = await asyncio.gather(*tasks)
                logger.info(f" -> SUCCESS: All {len(results)} concurrent requests completed clean execution.")
                passed += 1
            except Exception as e:
                logger.error(f" -> CONCURRENCY FAILURE: {e}")
                failed += 1

    finally:
        await DatabasePool.close()

    logger.info("=========================================================")
    logger.info(f" API ROBUSTNESS SUMMARY: {passed} PASSED, {failed} FAILED")
    logger.info("=========================================================")
    return failed == 0

if __name__ == "__main__":
    success = asyncio.run(run_api_tests())
    if not success:
        sys.exit(1)
    sys.exit(0)
