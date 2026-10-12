"""
Independent V5.4 Rollback Verification Script.
Validates database connectivity, chunk count (6689), vector count (6689), embedding dimension (1024),
and executes V5.4 standalone smoke tests post-rollback.
Exits 0 on PASS, non-zero on FAIL.
"""

import sys
import asyncio
import logging
import subprocess

from sap_rag.database.connection import DatabasePool

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s]: %(message)s")
logger = logging.getLogger("verify_v54_rollback")

EXPECTED_CHUNK_COUNT = 6689
EXPECTED_EMBEDDING_COUNT = 6689
EXPECTED_DIMENSION = 1024

async def verify_v54_state() -> bool:
    logger.info("=========================================================")
    logger.info("   SAP UTILITIES RAG V5.4 - INDEPENDENT ROLLBACK VERIFY  ")
    logger.info("=========================================================")
    errors = []

    logger.info("1. Verifying Database Connectivity & Corpus State...")
    await DatabasePool.initialize(min_size=1, max_size=3)
    try:
        async with DatabasePool.acquire() as conn:
            chunk_cnt = await conn.fetchval("SELECT COUNT(*) FROM chunks;")
            emb_cnt = await conn.fetchval("SELECT COUNT(*) FROM embeddings WHERE model = 'BAAI/bge-m3' OR model = 'BGE-M3';")
            emb_dim = await conn.fetchval("SELECT vector_dims(embedding) FROM embeddings LIMIT 1;")

            logger.info(f" -> Chunks Count     : {chunk_cnt} (Expected: {EXPECTED_CHUNK_COUNT})")
            logger.info(f" -> Embeddings Count : {emb_cnt} (Expected: {EXPECTED_EMBEDDING_COUNT})")
            logger.info(f" -> Embedding Dim    : {emb_dim} (Expected: {EXPECTED_DIMENSION})")

            if chunk_cnt != EXPECTED_CHUNK_COUNT:
                errors.append(f"Chunk count mismatch: {chunk_cnt} != {EXPECTED_CHUNK_COUNT}")
            if emb_cnt != EXPECTED_EMBEDDING_COUNT:
                errors.append(f"Embedding count mismatch: {emb_cnt} != {EXPECTED_EMBEDDING_COUNT}")
            if emb_dim != EXPECTED_DIMENSION:
                errors.append(f"Embedding dimension mismatch: {emb_dim} != {EXPECTED_DIMENSION}")

    finally:
        await DatabasePool.close()

    if errors:
        logger.error("V5.4 ROLLBACK STATE VERIFICATION FAILED!")
        for err in errors:
            logger.error(f" - {err}")
        return False

    # 2. Execute V5.4 Smoke Test
    logger.info("2. Executing V5.4 Standalone Smoke Test Suite...")
    python_exe = sys.executable
    res = subprocess.run([python_exe, "scripts/test_v54_smoke_test.py"], capture_output=True, text=True)
    print(res.stdout)

    if res.returncode != 0:
        logger.error(f"V5.4 Smoke test failed with exit code {res.returncode}")
        print(res.stderr)
        return False

    logger.info("=========================================================")
    logger.info(" SUCCESS: V5.4 Rollback Verification Passed 100%")
    logger.info("=========================================================")
    return True

if __name__ == "__main__":
    success = asyncio.run(verify_v54_state())
    if not success:
        sys.exit(1)
    sys.exit(0)
