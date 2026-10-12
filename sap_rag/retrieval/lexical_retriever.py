"""
Lexical full-text search retrieval component using PostgreSQL tsvector, websearch_to_tsquery, plainto_tsquery, and ts_rank_cd.
"""

import re
import json
import logging
from typing import List, Optional
import asyncpg

from sap_rag.retrieval.config import retrieval_settings
from sap_rag.retrieval.models import RetrievalCandidate, ProcessedQuery

logger = logging.getLogger(__name__)

class LexicalRetriever:
    """
    Lexical full-text retrieval engine using PostgreSQL tsvector indexing with fallback miss recovery.
    """

    async def search(
        self,
        conn: asyncpg.Connection,
        processed_query: ProcessedQuery,
        top_k: int = retrieval_settings.LEXICAL_TOP_K,
        source_ids: Optional[List[int]] = None,
        document_ids: Optional[List[int]] = None,
        use_expanded: bool = False
    ) -> List[RetrievalCandidate]:
        """
        Perform PostgreSQL full-text search across chunks content and document titles/breadcrumbs.
        """
        query_text = processed_query.expanded_query if (use_expanded and processed_query.expanded_query) else (processed_query.normalized_query or processed_query.original_query)
        if not query_text:
            return []

        # Strip generic corpus noise words that degrade websearch AND matching
        clean_words = [w for w in query_text.split() if w.lower() not in {"sap", "utilities", "utility", "isu"}]
        fts_query_text = " ".join(clean_words) if clean_words else query_text

        # Construct PostgreSQL full text query using websearch_to_tsquery
        sql = """
            WITH q AS (
                SELECT websearch_to_tsquery('english', $1) AS ts_q
            )
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
                ts_rank_cd(c.fts, q.ts_q) AS raw_rank
            FROM chunks c
            JOIN documents d ON c.document_id = d.id, q
            WHERE c.fts @@ q.ts_q
              AND ($2::bigint[] IS NULL OR d.source_id = ANY($2::bigint[]))
              AND ($3::bigint[] IS NULL OR c.document_id = ANY($3::bigint[]))
            ORDER BY raw_rank DESC
            LIMIT $4;
        """

        rows = await conn.fetch(
            sql,
            fts_query_text,
            source_ids if source_ids else None,
            document_ids if document_ids else None,
            top_k
        )

        # Fallback 1: Try plainto_tsquery on expanded_query if websearch returned 0 results
        if not rows and processed_query.expanded_query:
            sql_expanded = """
                WITH q AS (
                    SELECT plainto_tsquery('english', $1) AS ts_q
                )
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
                    ts_rank_cd(c.fts, q.ts_q) AS raw_rank
                FROM chunks c
                JOIN documents d ON c.document_id = d.id, q
                WHERE c.fts @@ q.ts_q
                  AND ($2::bigint[] IS NULL OR d.source_id = ANY($2::bigint[]))
                  AND ($3::bigint[] IS NULL OR c.document_id = ANY($3::bigint[]))
                ORDER BY raw_rank DESC
                LIMIT $4;
            """
            try:
                rows = await conn.fetch(
                    sql_expanded,
                    processed_query.expanded_query,
                    source_ids if source_ids else None,
                    document_ids if document_ids else None,
                    top_k
                )
            except Exception as e:
                logger.debug(f"Lexical expanded query fallback failed: {e}")
                rows = []

        # Fallback 2: Try OR-matching on keywords if still 0 results
        if not rows and processed_query.keywords:
            valid_kw = [re.sub(r"[^\w]", "", k) for k in processed_query.keywords if len(re.sub(r"[^\w]", "", k)) > 2]
            if valid_kw:
                fallback_query = " | ".join(valid_kw)
                sql_fallback = """
                    WITH q AS (
                        SELECT to_tsquery('english', $1) AS ts_q
                    )
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
                        ts_rank_cd(c.fts, q.ts_q) AS raw_rank
                    FROM chunks c
                    JOIN documents d ON c.document_id = d.id, q
                    WHERE c.fts @@ q.ts_q
                      AND ($2::bigint[] IS NULL OR d.source_id = ANY($2::bigint[]))
                      AND ($3::bigint[] IS NULL OR c.document_id = ANY($3::bigint[]))
                    ORDER BY raw_rank DESC
                    LIMIT $4;
                """
                try:
                    rows = await conn.fetch(
                        sql_fallback,
                        fallback_query,
                        source_ids if source_ids else None,
                        document_ids if document_ids else None,
                        top_k
                    )
                except Exception as e:
                    logger.debug(f"Lexical keyword fallback failed: {e}")
                    rows = []

        candidates = []
        for r in rows:
            raw_rank = float(r["raw_rank"] or 0.0)
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
                lexical_score=raw_rank,
                metadata=c_meta,
                retrieval_method="lexical"
            )
            candidates.append(cand)

        logger.debug(f"LexicalRetriever retrieved {len(candidates)} candidates for query '{query_text[:40]}...'")
        return candidates
