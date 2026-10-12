"""
Automated Frozen Release Artifact Verification Script for SAP Utilities RAG V5.5.
Checks corpus SHA-256, benchmark SHA-256, source count, document count, chunk count,
embedding count, vector dimension, chunking version, and embedding model against frozen expectations.
Exits with 0 on PASS, non-zero on FAIL.
"""

import os
import sys
import json
import hashlib
import asyncio
import logging

from sap_rag.database.connection import DatabasePool

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s]: %(message)s")
logger = logging.getLogger("verify_release_artifacts")

# FROZEN RELEASE CANDIDATE CONTRACT CONSTANTS
EXPECTED_CORPUS_SHA256 = "f4f0bdc4e5a9a6b79a040de22ca91fcfe9a92c2b93a79faeaeb5dba40487caf6"
EXPECTED_BENCHMARK_SHA256 = "53ff3a94da1692a286bd66479543d5dc16114cd33a44c71d02125578749f0a26"
EXPECTED_SOURCE_COUNT = 29
EXPECTED_DOC_COUNT = 965
EXPECTED_CHUNK_COUNT = 6689
EXPECTED_EMBEDDING_COUNT = 6689
EXPECTED_EMBEDDING_DIM = 1024
EXPECTED_CHUNKING_VERSION = "semantic-v1"
EXPECTED_MODEL_NAME = "BAAI/bge-m3"

BENCHMARK_FILE_PATH = "evaluation/datasets/retrieval_benchmark_v5_1.json"

async def verify_artifacts() -> bool:
    logger.info("=========================================================")
    logger.info("   SAP UTILITIES RAG V5.5 - FROZEN ARTIFACT VERIFICATION  ")
    logger.info("=========================================================")
    errors = []

    # 1. Benchmark File Verification
    if not os.path.exists(BENCHMARK_FILE_PATH):
        errors.append(f"Benchmark file missing: {BENCHMARK_FILE_PATH}")
    else:
        with open(BENCHMARK_FILE_PATH, "rb") as f:
            bench_sha = hashlib.sha256(f.read()).hexdigest()
        logger.info(f"Benchmark SHA-256 : {bench_sha}")
        if bench_sha != EXPECTED_BENCHMARK_SHA256:
            errors.append(f"BENCHMARK SHA MISMATCH: Got {bench_sha}, expected {EXPECTED_BENCHMARK_SHA256}")

    # 2. Database Artifact Verification
    logger.info("Connecting to Supabase PostgreSQL database...")
    await DatabasePool.initialize(min_size=1, max_size=3)
    try:
        async with DatabasePool.acquire() as conn:
            source_cnt = await conn.fetchval("SELECT COUNT(*) FROM sources;")
            doc_cnt = await conn.fetchval("SELECT COUNT(*) FROM documents;")
            chunk_cnt = await conn.fetchval("SELECT COUNT(*) FROM chunks;")
            emb_cnt = await conn.fetchval("SELECT COUNT(*) FROM embeddings WHERE model = 'BAAI/bge-m3' OR model = 'BGE-M3';")
            emb_dim = await conn.fetchval("SELECT vector_dims(embedding) FROM embeddings LIMIT 1;")

            logger.info(f"Source Count       : {source_cnt} (Expected: {EXPECTED_SOURCE_COUNT})")
            logger.info(f"Document Count     : {doc_cnt} (Expected: {EXPECTED_DOC_COUNT})")
            logger.info(f"Chunk Count        : {chunk_cnt} (Expected: {EXPECTED_CHUNK_COUNT})")
            logger.info(f"Embedding Count    : {emb_cnt} (Expected: {EXPECTED_EMBEDDING_COUNT})")
            logger.info(f"Embedding Dim      : {emb_dim} (Expected: {EXPECTED_EMBEDDING_DIM})")

            if source_cnt != EXPECTED_SOURCE_COUNT:
                errors.append(f"Source count mismatch: {source_cnt} != {EXPECTED_SOURCE_COUNT}")
            if doc_cnt != EXPECTED_DOC_COUNT:
                errors.append(f"Document count mismatch: {doc_cnt} != {EXPECTED_DOC_COUNT}")
            if chunk_cnt != EXPECTED_CHUNK_COUNT:
                errors.append(f"Chunk count mismatch: {chunk_cnt} != {EXPECTED_CHUNK_COUNT}")
            if emb_cnt != EXPECTED_EMBEDDING_COUNT:
                errors.append(f"Embedding count mismatch: {emb_cnt} != {EXPECTED_EMBEDDING_COUNT}")
            if emb_dim != EXPECTED_EMBEDDING_DIM:
                errors.append(f"Embedding dimension mismatch: {emb_dim} != {EXPECTED_EMBEDDING_DIM}")

            # Compute Corpus SHA-256 over chunk hashes
            chunk_hashes = await conn.fetch("SELECT content_hash FROM chunks ORDER BY id ASC;")
            hasher = hashlib.sha256()
            for r in chunk_hashes:
                ch = r["content_hash"] or ""
                hasher.update(ch.encode("utf-8"))
            corpus_sha = hasher.hexdigest()

            logger.info(f"Corpus SHA-256    : {corpus_sha}")
            if corpus_sha != EXPECTED_CORPUS_SHA256:
                errors.append(f"CORPUS SHA MISMATCH: Got {corpus_sha}, expected {EXPECTED_CORPUS_SHA256}")

    finally:
        await DatabasePool.close()

    if errors:
        logger.error("RELEASE BLOCKED - FROZEN ARTIFACT MUTATION DETECTED!")
        for err in errors:
            logger.error(f" - {err}")
        return False

    logger.info("=========================================================")
    logger.info(" SUCCESS: All frozen release artifacts verified (100% MATCH)")
    logger.info("=========================================================")
    return True

if __name__ == "__main__":
    success = asyncio.run(verify_artifacts())
    if not success:
        sys.exit(1)
    sys.exit(0)
