"""
Embedding pipeline orchestrating chunk loading, truncation accounting, batch vector encoding, transactional database persistence, and performance logging.
"""

import asyncio
import time
import logging
import json
from typing import List, Dict, Any, Optional, Set
import asyncpg
import numpy as np

from sap_rag.embeddings.config import embedding_settings
from sap_rag.embeddings.service import EmbeddingModelService
from sap_rag.database.repositories.embedding_repository import EmbeddingRepository

logger = logging.getLogger(__name__)

class EmbeddingPipeline:
    """
    Production-grade batch pipeline for generating and persisting BAAI/bge-m3 vector embeddings into Supabase pgvector.
    """

    def __init__(self, service: Optional[EmbeddingModelService] = None):
        self.service = service or EmbeddingModelService.get_instance()
        self.batch_size = embedding_settings.BATCH_SIZE
        self.model_key = embedding_settings.MODEL_KEY

    async def run(
        self,
        conn: asyncpg.Connection,
        source_id: Optional[int] = None,
        document_id: Optional[int] = None,
        resume: bool = False,
        dry_run: bool = False
    ) -> Dict[str, Any]:
        """
        Execute embedding generation pipeline.
        """
        start_time = time.time()
        logger.info(
            f"Starting Embedding Pipeline (source_id={source_id}, document_id={document_id}, "
            f"resume={resume}, dry_run={dry_run}, batch_size={self.batch_size})..."
        )

        # 1. Fetch eligible chunks from database
        query = """
            SELECT c.id, c.document_id, c.section_id, c.content, c.token_count, d.source_id
            FROM chunks c
            JOIN documents d ON c.document_id = d.id
        """
        where_clauses = []
        params = []
        param_idx = 1

        if source_id is not None:
            where_clauses.append(f"d.source_id = ${param_idx}")
            params.append(source_id)
            param_idx += 1

        if document_id is not None:
            where_clauses.append(f"c.document_id = ${param_idx}")
            params.append(document_id)
            param_idx += 1

        if where_clauses:
            query += " WHERE " + " AND ".join(where_clauses)

        query += " ORDER BY c.id;"

        chunk_rows = await conn.fetch(query, *params)
        total_eligible = len(chunk_rows)

        if not chunk_rows:
            logger.info("No eligible chunks found matching the filter criteria.")
            return self._build_summary_report([], 0, 0, 0, 0, 0, 0, 0, 0, 0.0, {})

        # 2. If resume flag is set, filter out already embedded chunk IDs
        already_embedded_ids: Set[int] = set()
        if resume:
            already_embedded_ids = await EmbeddingRepository.fetch_existing_chunk_ids(conn, self.model_key)
            filtered_rows = [r for r in chunk_rows if r["id"] not in already_embedded_ids]
            logger.info(f"Resume mode: {len(already_embedded_ids)} already embedded, {len(filtered_rows)} remaining to process.")
        else:
            filtered_rows = list(chunk_rows)

        # Sort remaining chunks by token_count to optimize padding in batch encoding
        filtered_rows.sort(key=lambda r: r["token_count"])

        already_embedded_count = total_eligible - len(filtered_rows)
        newly_embedded_count = 0
        failed_count = 0
        truncated_count = 0
        source_truncations: Dict[int, int] = {}

        max_source_tokens = 0
        max_embedded_tokens = 0
        total_embedded_tokens = 0
        db_insertion_time = 0.0
        batch_times: List[float] = []

        # 3. Stream batch processing
        total_to_process = len(filtered_rows)
        total_batches = (total_to_process + self.batch_size - 1) // self.batch_size if total_to_process > 0 else 0

        for i in range(0, total_to_process, self.batch_size):
            batch_rows = filtered_rows[i : i + self.batch_size]
            batch_start = time.time()

            batch_texts = []
            batch_chunk_ids = []
            batch_meta_list = []

            for r in batch_rows:
                cid = r["id"]
                raw_text = r["content"]
                sid = r["source_id"]

                try:
                    prep = self.service.prepare_chunk(raw_text)
                except Exception as e:
                    logger.error(f"Error preparing chunk ID {cid}: {e}")
                    failed_count += 1
                    continue

                batch_texts.append(prep["content"])
                batch_chunk_ids.append(cid)

                s_tok = prep["source_tokens"]
                e_tok = prep["embedded_tokens"]
                total_embedded_tokens += e_tok

                if s_tok > max_source_tokens:
                    max_source_tokens = s_tok
                if e_tok > max_embedded_tokens:
                    max_embedded_tokens = e_tok

                if prep["truncated"]:
                    truncated_count += 1
                    source_truncations[sid] = source_truncations.get(sid, 0) + 1

                batch_meta_list.append(prep)

            if not batch_texts:
                continue

            # Generate embeddings for batch offloaded to threadpool
            try:
                vectors = await asyncio.to_thread(self.service.encode_batch, batch_texts)
            except Exception as e:
                logger.error(f"Batch encoding failure at index {i}: {e}")
                failed_count += len(batch_rows)
                continue

            # Validate dimensions
            if vectors.shape[1] != embedding_settings.EMBEDDING_DIMENSION:
                err = f"Dimension mismatch during batch encoding! Got {vectors.shape[1]}, expected {embedding_settings.EMBEDDING_DIMENSION}."
                logger.critical(err)
                raise ValueError(err)

            # Persist batch to DB transactional block
            if not dry_run:
                records = [
                    {"chunk_id": cid, "vector": vec}
                    for cid, vec in zip(batch_chunk_ids, vectors)
                ]

                db_start = time.time()
                try:
                    async with conn.transaction():
                        await EmbeddingRepository.upsert_embeddings_batch(
                            conn, records, model_key=self.model_key, dimension=embedding_settings.EMBEDDING_DIMENSION
                        )
                    db_insertion_time += (time.time() - db_start)
                    newly_embedded_count += len(records)
                except Exception as e:
                    logger.error(f"Database transaction failure persisting batch {i}: {e}")
                    failed_count += len(records)
                    continue
            else:
                newly_embedded_count += len(batch_texts)

            batch_duration = time.time() - batch_start
            batch_times.append(batch_duration)

            import sys
            logger.info(
                f"Batch {i//self.batch_size + 1}/{total_batches}: "
                f"Processed {len(batch_texts)} chunks in {batch_duration:.2f}s."
            )
            sys.stdout.flush()
            sys.stderr.flush()

        duration = time.time() - start_time

        summary = self._build_summary_report(
            chunk_rows,
            total_eligible,
            already_embedded_count,
            newly_embedded_count,
            failed_count,
            truncated_count,
            max_source_tokens,
            max_embedded_tokens,
            total_embedded_tokens,
            duration,
            batch_times,
            db_insertion_time,
            total_batches,
            source_truncations
        )
        return summary

    def _build_summary_report(
        self,
        chunk_rows: List[Any],
        total_eligible: int,
        already_embedded: int,
        newly_embedded: int,
        failed: int,
        truncated: int,
        max_source_tok: int,
        max_embed_tok: int,
        total_embedded_tok: int,
        duration: float,
        batch_times: List[float],
        db_insertion_time: float,
        total_batches: int,
        source_truncations: Dict[int, int]
    ) -> Dict[str, Any]:
        
        avg_batch_time = float(np.mean(batch_times)) if batch_times else 0.0
        cps = float(newly_embedded / duration) if duration > 0 else 0.0
        tps = float(total_embedded_tok / duration) if duration > 0 else 0.0

        return {
            "total_eligible_chunks": total_eligible,
            "already_embedded_chunks": already_embedded,
            "newly_embedded_chunks": newly_embedded,
            "failed_chunks": failed,
            "truncated_chunks": truncated,
            "max_source_tokens": max_source_tok,
            "max_embedded_tokens": max_embed_tok,
            "total_embedded_tokens": total_embedded_tok,
            "duration": round(duration, 3),
            "avg_batch_time": round(avg_batch_time, 3),
            "db_insertion_time": round(db_insertion_time, 3),
            "chunks_per_sec": round(cps, 2),
            "tokens_per_sec": round(tps, 2),
            "total_batches": total_batches,
            "source_truncations": source_truncations,
            "model_key": self.model_key,
            "dimension": embedding_settings.EMBEDDING_DIMENSION
        }

