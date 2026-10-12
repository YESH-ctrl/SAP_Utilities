"""
Controlled hierarchy expansion component retrieving adjacent neighboring chunks within the same document section.
"""

import json
import logging
from typing import List, Set
import asyncpg

from sap_rag.retrieval.config import retrieval_settings
from sap_rag.retrieval.models import RetrievalCandidate

logger = logging.getLogger(__name__)

class HierarchyExpander:
    """
    Controlled neighbor and section context expander.
    """

    @classmethod
    async def expand(
        cls,
        conn: asyncpg.Connection,
        candidates: List[RetrievalCandidate],
        window: int = retrieval_settings.NEIGHBOR_WINDOW,
        enabled: bool = retrieval_settings.HIERARCHY_ENABLED,
        max_primary_candidates: int = 5
    ) -> List[RetrievalCandidate]:
        """
        Fetch adjacent (chunk_index - window ... chunk_index + window) chunks within the same document_id
        only for top high-confidence primary candidates.
        """
        if not enabled or not candidates:
            return candidates

        existing_chunk_ids: Set[int] = {c.chunk_id for c in candidates}
        expanded_list: List[RetrievalCandidate] = list(candidates)

        # Focus expansion on top primary candidates only
        primary_targets = candidates[:max_primary_candidates]

        targets = []
        for c in primary_targets:
            c_idx = c.metadata.get("chunk_index", 0)
            doc_id = c.document_id
            for offset in range(-window, window + 1):
                if offset == 0:
                    continue
                neighbor_idx = c_idx + offset
                if neighbor_idx >= 0:
                    targets.append((doc_id, neighbor_idx, c.final_score * 0.80))

        if not targets:
            return expanded_list

        sql = """
            SELECT 
                c.id AS chunk_id,
                c.document_id,
                c.section_id,
                c.chunk_index,
                d.source_id,
                d.title AS doc_title,
                d.url AS doc_url,
                COALESCE(c.metadata->>'breadcrumb', d.metadata->>'breadcrumb', '') AS breadcrumb,
                c.content,
                c.token_count,
                c.content_hash,
                c.metadata AS chunk_metadata
            FROM chunks c
            JOIN documents d ON c.document_id = d.id
            WHERE (c.document_id, c.chunk_index) IN (
                SELECT (t.doc_id)::bigint, (t.idx)::int
                FROM unnest($1::bigint[], $2::int[]) AS t(doc_id, idx)
            );
        """

        doc_ids_param = [t[0] for t in targets]
        indices_param = [t[1] for t in targets]
        score_map = {(t[0], t[1]): t[2] for t in targets}

        rows = await conn.fetch(sql, doc_ids_param, indices_param)

        for r in rows:
            cid = r["chunk_id"]
            if cid in existing_chunk_ids:
                continue

            existing_chunk_ids.add(cid)
            doc_id = r["document_id"]
            c_idx = r["chunk_index"]
            c_meta = json.loads(r["chunk_metadata"]) if isinstance(r["chunk_metadata"], str) else (r["chunk_metadata"] or {})
            c_meta["chunk_index"] = c_idx

            inherited_score = score_map.get((doc_id, c_idx), 0.5)

            neighbor_cand = RetrievalCandidate(
                chunk_id=cid,
                document_id=doc_id,
                section_id=r["section_id"],
                source_id=r["source_id"],
                title=r["doc_title"] or "",
                url=r["doc_url"] or "",
                breadcrumb=r["breadcrumb"] or "",
                content=r["content"],
                token_count=r["token_count"],
                content_hash=r["content_hash"],
                final_score=inherited_score,
                pre_rerank_score=inherited_score,
                metadata=c_meta,
                retrieval_method="hierarchy_expanded",
                is_neighbor=True
            )
            expanded_list.append(neighbor_cand)

        logger.debug(f"HierarchyExpander expanded candidates from {len(candidates)} to {len(expanded_list)} items.")
        return expanded_list

    @classmethod
    async def expand_parent_source(
        cls,
        conn: asyncpg.Connection,
        candidates: List[RetrievalCandidate],
        max_additions: int = 5
    ) -> List[RetrievalCandidate]:
        """
        Experiment C: Hierarchy-aware candidate recovery.
        Fetches intro/root chunk (chunk_index=0) for parent document/source of top candidates.
        """
        if not candidates or max_additions <= 0:
            return candidates

        existing_chunk_ids: Set[int] = {c.chunk_id for c in candidates}
        existing_doc_ids: Set[int] = {c.document_id for c in candidates if c.document_id}
        expanded_list: List[RetrievalCandidate] = list(candidates)

        # Target top 3 candidates' source/document relationships
        target_source_ids = list({c.source_id for c in candidates[:3] if c.source_id is not None})
        if not target_source_ids:
            return candidates

        sql = """
            SELECT 
                c.id AS chunk_id,
                c.document_id,
                c.section_id,
                c.chunk_index,
                d.source_id,
                d.title AS doc_title,
                d.url AS doc_url,
                COALESCE(c.metadata->>'breadcrumb', d.metadata->>'breadcrumb', '') AS breadcrumb,
                c.content,
                c.token_count,
                c.content_hash,
                c.metadata AS chunk_metadata
            FROM chunks c
            JOIN documents d ON c.document_id = d.id
            WHERE d.source_id = ANY($1::int[]) AND c.chunk_index = 0
            LIMIT $2::int;
        """

        rows = await conn.fetch(sql, target_source_ids, max_additions)
        added_cnt = 0

        for r in rows:
            cid = r["chunk_id"]
            if cid in existing_chunk_ids:
                continue

            existing_chunk_ids.add(cid)
            c_meta = json.loads(r["chunk_metadata"]) if isinstance(r["chunk_metadata"], str) else (r["chunk_metadata"] or {})
            
            # Inherit score slightly below top candidate
            inherited_score = candidates[0].hybrid_score * 0.75 if candidates else 0.01

            parent_cand = RetrievalCandidate(
                chunk_id=cid,
                document_id=r["document_id"],
                section_id=r["section_id"],
                source_id=r["source_id"],
                title=r["doc_title"] or "",
                url=r["doc_url"] or "",
                breadcrumb=r["breadcrumb"] or "",
                content=r["content"],
                token_count=r["token_count"],
                content_hash=r["content_hash"],
                final_score=inherited_score,
                pre_rerank_score=inherited_score,
                hybrid_score=inherited_score,
                metadata=c_meta,
                retrieval_method="hierarchy_parent_recovered",
                is_neighbor=True
            )
            expanded_list.append(parent_cand)
            added_cnt += 1
            if added_cnt >= max_additions:
                break

        return expanded_list
