"""
Dense vector retrieval component using BAAI/bge-m3 query embeddings and pgvector HNSW cosine similarity.
"""

import json
import logging
from typing import List, Optional
import asyncpg

from sap_rag.database.connection import DatabasePool
from sap_rag.embeddings.service import EmbeddingModelService
from sap_rag.embeddings.config import embedding_settings
from sap_rag.retrieval.config import retrieval_settings
from sap_rag.retrieval.models import RetrievalCandidate

logger = logging.getLogger(__name__)

class DenseRetriever:
    """
    Dense vector search engine utilizing Supabase pgvector HNSW cosine distance search.
    """

    def __init__(self, service: Optional[EmbeddingModelService] = None):
        self.service = service or EmbeddingModelService.get_instance()
        self.model_key = embedding_settings.MODEL_KEY

    async def search(
        self,
        conn: asyncpg.Connection,
        query: str,
        top_k: int = retrieval_settings.DENSE_TOP_K,
        source_ids: Optional[List[int]] = None,
        document_ids: Optional[List[int]] = None
    ) -> List[RetrievalCandidate]:
        """
        Encode query and perform pgvector HNSW cosine similarity search.
        """
        if not query or not query.strip():
            return []

        # 1. Generate query vector (1024 dims)
        query_vec = self.service.encode_query(query)
        vec_str = json.dumps(query_vec)

        # 2. Construct pgvector search query
        # pgvector cosine distance: e.embedding <=> query_vec
        # Cosine similarity: 1 - (e.embedding <=> query_vec)
        query_sql = """
            SELECT 
                c.id AS chunk_id,
                c.document_id,
                c.section_id,
                d.source_id,
                d.title AS doc_title,
                d.url AS doc_url,
                COALESCE(c.metadata->>'breadcrumb', d.metadata->>'breadcrumb', '') AS breadcrumb,
                c.content,
                c.token_count,
                c.content_hash,
                c.metadata AS chunk_metadata,
                (1.0 - (e.embedding <=> $1::vector)) AS dense_score
            FROM embeddings e
            JOIN chunks c ON e.chunk_id = c.id
            JOIN documents d ON c.document_id = d.id
            WHERE (e.model = $2 OR e.model = 'BGE-M3' OR e.model = 'BAAI/bge-m3')
              AND ($3::bigint[] IS NULL OR d.source_id = ANY($3::bigint[]))
              AND ($4::bigint[] IS NULL OR c.document_id = ANY($4::bigint[]))
            ORDER BY e.embedding <=> $1::vector ASC
            LIMIT $5;
        """

        rows = await conn.fetch(
            query_sql,
            vec_str,
            self.model_key,
            source_ids if source_ids else None,
            document_ids if document_ids else None,
            top_k
        )

        candidates = []
        for r in rows:
            dense_score = max(0.0, float(r["dense_score"]))
            c_meta = json.loads(r["chunk_metadata"]) if isinstance(r["chunk_metadata"], str) else (r["chunk_metadata"] or {})

            cand = RetrievalCandidate(
                chunk_id=r["chunk_id"],
                document_id=r["document_id"],
                section_id=r["section_id"],
                source_id=r["source_id"],
                title=r["doc_title"] or "",
                url=r["doc_url"] or "",
                breadcrumb=r["breadcrumb"] or "",
                content=r["content"],
                token_count=r["token_count"],
                content_hash=r["content_hash"],
                dense_score=dense_score,
                metadata=c_meta,
                retrieval_method="dense"
            )
            candidates.append(cand)

        logger.debug(f"DenseRetriever retrieved {len(candidates)} candidates for query '{query[:40]}...'")
        return candidates
