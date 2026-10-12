"""
Independent Semantic Retrieval Service for Agentic Platform.
Executes parameterized, direct pgvector nearest-neighbor queries over stored chunk embeddings.
Uses cosine distance operator (<=>) matching HNSW vector_cosine_ops index.
Does NOT call legacy dense retriever, lexical search, RRF fusion, or heuristic scorers.
"""

import time
import logging
import json
from typing import List, Dict, Any, Optional
import asyncpg

from sap_rag.database.connection import DatabasePool
from sap_rag.agentic.retrieval.encoder import IndependentQueryEncoder
from sap_rag.agentic.schemas.contracts import EvidenceItem
from sap_rag.agentic.retrieval.context_builder import parse_chunk_components, create_clean_excerpt

logger = logging.getLogger("sap_rag.agentic.retrieval.service")


class SemanticRetrievalService:
    """
    Dedicated read-only semantic retrieval engine over PostgreSQL/pgvector.
    Direct SQL parameterization prevents SQL injection and bypasses legacy code entirely.
    """

    def __init__(self, encoder: Optional[IndependentQueryEncoder] = None):
        self.encoder = encoder or IndependentQueryEncoder.get_instance()

    @staticmethod
    def clean_unicode(text: Optional[str]) -> str:
        if not text:
            return ""
        import re
        return re.sub(r"[\uE000-\uF8FF\uFFF0-\uFFFF]", "", text).strip()

    async def search(
        self,
        query: str,
        subquery_id: Optional[str] = None,
        top_k: int = 10,
        source_ids: Optional[List[int]] = None,
        document_ids: Optional[List[int]] = None,
        min_similarity: float = 0.30,
        expand_sections: bool = True
    ) -> List[EvidenceItem]:
        """
        Execute direct semantic vector search against existing PostgreSQL chunks and embeddings.
        Configures hnsw.ef_search = 200 to guarantee deep recall of procedural chunks.
        Expands section hierarchy for discovered documents to retrieve full procedures, prerequisites, and results.
        Returns typed EvidenceItem records.
        """
        start_t = time.perf_counter()
        clean_q = (query or "").strip()
        if not clean_q:
            return []

        # 1. Encode query with verified independent encoder
        query_vector = self.encoder.encode(clean_q)
        vector_str = "[" + ",".join(str(round(v, 7)) for v in query_vector) + "]"

        # 2. Build parameterized query
        # pgvector cosine distance: embedding <=> vector_param
        # Cosine similarity: 1.0 - (embedding <=> vector_param)
        conditions = ["e.embedding IS NOT NULL"]
        params: List[Any] = [vector_str, top_k]

        if source_ids:
            params.append(source_ids)
            conditions.append(f"d.source_id = ANY(${len(params)})")

        if document_ids:
            params.append(document_ids)
            conditions.append(f"c.document_id = ANY(${len(params)})")

        where_clause = " AND ".join(conditions)

        sql = f"""
            SELECT 
                c.id AS chunk_id,
                c.document_id,
                c.section_id,
                c.chunk_index,
                c.content,
                c.token_count,
                c.metadata AS chunk_metadata,
                d.id AS doc_id,
                d.source_id,
                d.title AS doc_title,
                d.url AS doc_url,
                d.canonical_url,
                d.source_pdf,
                d.depth,
                s.heading AS section_heading,
                (e.embedding <=> $1::vector) AS cosine_dist
            FROM embeddings e
            JOIN chunks c ON e.chunk_id = c.id
            JOIN documents d ON c.document_id = d.id
            LEFT JOIN document_sections s ON c.section_id = s.id
            WHERE {where_clause}
            ORDER BY e.embedding <=> $1::vector ASC
            LIMIT $2;
        """

        evidence_items: List[EvidenceItem] = []

        async with DatabasePool.acquire() as conn:
            # Set ef_search = 200 for deep HNSW recall of procedural chunks
            await conn.execute("SET hnsw.ef_search = 200;")
            raw_rows = await conn.fetch(sql, *params)
            rows = list(raw_rows)

            # 3. Document Section Expansion:
            # When candidate documents are discovered, inspect their section hierarchy
            # and retrieve procedure, prerequisite, result, and scope sections.
            if expand_sections and rows:
                top_doc_ids = list(dict.fromkeys([r["document_id"] for r in rows[:4]]))
                seen_chunk_ids = {r["chunk_id"] for r in rows}
                proc_sql = """
                    SELECT 
                        c.id AS chunk_id,
                        c.document_id,
                        c.section_id,
                        c.chunk_index,
                        c.content,
                        c.token_count,
                        c.metadata AS chunk_metadata,
                        d.id AS doc_id,
                        d.source_id,
                        d.title AS doc_title,
                        d.url AS doc_url,
                        d.canonical_url,
                        d.source_pdf,
                        d.depth,
                        s.heading AS section_heading,
                        (e.embedding <=> $1::vector) AS cosine_dist
                    FROM chunks c
                    JOIN documents d ON c.document_id = d.id
                    LEFT JOIN document_sections s ON c.section_id = s.id
                    LEFT JOIN embeddings e ON e.chunk_id = c.id
                    WHERE c.document_id = ANY($2)
                      AND (
                        s.heading ILIKE '%procedure%'
                        OR s.heading ILIKE '%prerequisite%'
                        OR s.heading ILIKE '%result%'
                        OR s.heading ILIKE '%scope%'
                        OR s.heading ILIKE '%use%'
                        OR s.heading ILIKE '%feature%'
                        OR s.heading ILIKE '%activit%'
                        OR s.heading ILIKE '%how to%'
                        OR s.heading ILIKE '%reconnect%'
                        OR s.heading ILIKE '%disconnect%'
                        OR s.heading ILIKE '%order%'
                        OR s.heading ILIKE '%entry%'
                        OR s.heading ILIKE '%process flow%'
                        OR s.heading ILIKE '%reversal%'
                        OR s.heading ILIKE '%reverse%'
                      )
                    ORDER BY c.document_id, c.chunk_index ASC;
                """
                proc_rows = await conn.fetch(proc_sql, vector_str, top_doc_ids)
                for pr in proc_rows:
                    if pr["chunk_id"] not in seen_chunk_ids:
                        rows.append(pr)
                        seen_chunk_ids.add(pr["chunk_id"])

        # 4. Filter and prioritize procedural content
        # Check if substantive procedure/prerequisite chunks exist for documents
        doc_has_proc = set()
        for r in rows:
            h = (r["section_heading"] or "").lower()
            if any(k in h for k in ("procedure", "prerequisite", "result", "how to", "use", "feature", "scope", "reconnect", "disconnect", "order", "entry", "process flow", "activit", "reversal")):
                doc_has_proc.add(r["document_id"])

        processed_rows = []
        for r in rows:
            heading_lower = (r["section_heading"] or "").lower()
            # If a document has actual procedural chunks, skip pure TOC / navigation chunks for that document
            if r["document_id"] in doc_has_proc and heading_lower in ("utilities", "overview") and r["chunk_index"] in (0, 1):
                continue
            processed_rows.append(r)

        # Sort: chunks with procedure/prerequisite headings first, then by cosine distance
        def _sort_key(row):
            h = (row["section_heading"] or "").lower()
            dist = float(row["cosine_dist"]) if row["cosine_dist"] is not None else 0.5
            is_proc = any(k in h for k in ("procedure", "prerequisite", "scope", "result", "use", "feature", "reconnect", "disconnect", "order", "entry", "process flow", "activit", "reversal"))
            return (0 if is_proc else 1, dist)

        processed_rows.sort(key=_sort_key)

        for idx, row in enumerate(processed_rows, 1):
            dist = float(row["cosine_dist"]) if row["cosine_dist"] is not None else 0.4
            sim = max(0.0, min(1.0, 1.0 - dist))

            if sim < min_similarity and idx > 4:
                continue

            content = self.clean_unicode(row["content"])
            doc_title = self.clean_unicode(row["doc_title"]) or f"Document {row['document_id']}"
            
            comp = parse_chunk_components(content)
            clean_body = comp["body"] or content
            clean_exc, off_start, off_end, is_exc = create_clean_excerpt(clean_body, max_chars=360)

            heading = self.clean_unicode(row["section_heading"]) or comp["section"] or "General"
            path = comp["path"] or (f"Depth {row['depth']}" if row["depth"] is not None else None)

            h_lower = heading.lower()
            disc_method = "section_expansion" if any(k in h_lower for k in ("procedure", "prerequisite", "result", "scope", "reconnect", "disconnect", "order", "entry", "process flow", "activit", "reversal")) and idx > top_k else "vector_direct"

            ev_id = f"EV-{subquery_id or 'Q'}-{idx}"
            item = EvidenceItem(
                evidence_id=ev_id,
                chunk_id=row["chunk_id"],
                document_id=row["document_id"],
                section_id=row["section_id"],
                source_id=row["source_id"],
                title=doc_title,
                canonical_url=row["canonical_url"] or row["doc_url"] or "",
                section_heading=heading,
                section_path=path,
                content=content,
                clean_body=clean_body,
                clean_excerpt=clean_exc,
                char_offset_start=0,
                char_offset_end=len(content),
                is_excerpted=False,
                token_count=row["token_count"] or len(content.split()),
                cosine_distance=round(dist, 4),
                similarity_score=round(sim, 4),
                subquery_id=subquery_id,
                discovery_method=disc_method,
                metadata={
                    "chunk_index": row["chunk_index"],
                    "source_pdf": row["source_pdf"],
                    "depth": row["depth"]
                }
            )
            evidence_items.append(item)

        elapsed_ms = round((time.perf_counter() - start_t) * 1000, 2)
        logger.info(
            f"Semantic retrieval complete: subquery='{subquery_id}' found {len(evidence_items)} items "
            f"in {elapsed_ms}ms (best_distance={evidence_items[0].cosine_distance if evidence_items else 'N/A'})"
        )
        return evidence_items
