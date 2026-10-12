"""
Database repository for pgvector embedding vectors persistence.
"""

import logging
import json
from typing import List, Dict, Any, Set
import asyncpg
import numpy as np

from sap_rag.embeddings.config import embedding_settings

logger = logging.getLogger(__name__)

class EmbeddingRepository:
    """
    Repository for managing vector embeddings in Supabase PostgreSQL (pgvector).
    Provides idempotent batch insertion via PostgreSQL UNNEST and ON CONFLICT DO UPDATE.
    """

    @staticmethod
    async def fetch_existing_chunk_ids(conn: asyncpg.Connection, model_key: str = embedding_settings.MODEL_KEY) -> Set[int]:
        """
        Fetch set of chunk_ids that already have embeddings generated for a given model_key.
        """
        rows = await conn.fetch(
            "SELECT chunk_id FROM embeddings WHERE model = $1 OR model = 'BGE-M3' OR model = 'BAAI/bge-m3';",
            model_key
        )
        return {r["chunk_id"] for r in rows}

    @staticmethod
    async def upsert_embeddings_batch(
        conn: asyncpg.Connection,
        records: List[Dict[str, Any]],
        model_key: str = embedding_settings.MODEL_KEY,
        dimension: int = embedding_settings.EMBEDDING_DIMENSION
    ) -> int:
        """
        Idempotent batch insert/update of vector embeddings using PostgreSQL UNNEST.
        Each record dict contains: 'chunk_id', 'vector' (numpy float32 array or float list).
        """
        if not records:
            return 0

        chunk_ids = [r["chunk_id"] for r in records]
        models = [model_key] * len(records)
        dimensions = [dimension] * len(records)
        
        # Convert numpy array / float list to pgvector string format: "[0.01, 0.02, ...]"
        vec_strings = []
        for r in records:
            vec = r["vector"]
            if isinstance(vec, np.ndarray):
                vec_list = vec.tolist()
            else:
                vec_list = float(vec) if isinstance(vec, (int, float)) else list(vec)
            vec_strings.append(json.dumps(vec_list))

        await conn.execute(
            """
            INSERT INTO embeddings (chunk_id, model, dimension, embedding)
            SELECT c_id, m, dim, emb::vector
            FROM unnest(
                $1::bigint[], $2::text[], $3::int[], $4::text[]
            ) AS t(c_id, m, dim, emb)
            ON CONFLICT (chunk_id, model)
            DO UPDATE SET 
                embedding = EXCLUDED.embedding,
                dimension = EXCLUDED.dimension,
                updated_at = NOW();
            """,
            chunk_ids, models, dimensions, vec_strings
        )
        return len(records)
