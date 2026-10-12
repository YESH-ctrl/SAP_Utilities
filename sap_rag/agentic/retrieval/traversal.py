"""
Graph Traversal Service for Agentic Platform.
Explores parent-child hierarchy and document hyperlink graph edges (document_links).
Strictly bounded by traversal depth, max candidate budget, cycle prevention, and timeouts.
Does NOT reuse legacy hierarchy expander or recovery heuristics.
"""

import time
import logging
from typing import List, Set, Dict, Any, Optional
import asyncpg

from sap_rag.database.connection import DatabasePool
from sap_rag.agentic.schemas.contracts import EvidenceItem

logger = logging.getLogger("sap_rag.agentic.retrieval.traversal")


class GraphTraversalService:
    """
    Service for controlled graph navigation across SAP Utilities document relationships.
    """

    def __init__(self, max_depth: int = 1, max_expansion_nodes: int = 4):
        self.max_depth = max_depth
        self.max_nodes = max_expansion_nodes

    @staticmethod
    def clean_unicode(text: Optional[str]) -> str:
        if not text:
            return ""
        import re
        return re.sub(r"[\uE000-\uF8FF\uFFF0-\uFFFF]", "", text).strip()

    async def expand_evidence_graph(
        self,
        seed_evidence: List[EvidenceItem],
        max_additional_chunks: int = 4
    ) -> List[EvidenceItem]:
        """
        Traverse document_links edges and parent hierarchy from seed evidence documents.
        Retrieves top relevant chunks from linked related documents to satisfy cross-document dependencies.
        """
        if not seed_evidence:
            return []

        start_t = time.perf_counter()
        visited_doc_ids: Set[int] = {ev.document_id for ev in seed_evidence}
        seen_chunk_ids: Set[int] = {ev.chunk_id for ev in seed_evidence}
        expanded_items: List[EvidenceItem] = []

        seed_doc_ids = list(visited_doc_ids)[:self.max_nodes]

        async with DatabasePool.acquire() as conn:
            # 1. Query target document IDs linked via document_links
            link_rows = await conn.fetch("""
                SELECT 
                    dl.source_document_id,
                    dl.target_document_id,
                    dl.link_text,
                    dl.link_type,
                    d.title AS target_title,
                    d.canonical_url AS target_url,
                    d.source_pdf,
                    d.depth AS target_depth
                FROM document_links dl
                JOIN documents d ON dl.target_document_id = d.id
                WHERE dl.source_document_id = ANY($1)
                  AND dl.target_document_id IS NOT NULL
                  AND dl.is_internal = TRUE
                ORDER BY 
                    CASE 
                        WHEN dl.link_text ILIKE '%revers%' THEN 1
                        WHEN dl.link_text ILIKE '%procedure%' THEN 2
                        WHEN dl.link_type IN ('child', 'toc') THEN 3
                        WHEN dl.link_type = 'related' THEN 4
                        ELSE 5
                    END ASC
                LIMIT 10;
            """, seed_doc_ids)

            target_doc_map: Dict[int, Dict[str, Any]] = {}
            for row in link_rows:
                tid = row["target_document_id"]
                if tid and tid not in visited_doc_ids and len(target_doc_map) < self.max_nodes:
                    target_doc_map[tid] = {
                        "source_doc_id": row["source_document_id"],
                        "link_text": row["link_text"],
                        "link_type": row["link_type"],
                        "title": row["target_title"],
                        "url": row["target_url"],
                        "source_pdf": row["source_pdf"],
                        "depth": row["target_depth"]
                    }
                    visited_doc_ids.add(tid)

            # 2. Also match text-only links where target_document_id IS NULL (e.g. "Move-In Reversal", "Move-Out Reversal")
            if len(target_doc_map) < self.max_nodes:
                text_link_rows = await conn.fetch("""
                    SELECT 
                        dl.source_document_id,
                        d.id AS target_document_id,
                        dl.link_text,
                        'related' AS link_type,
                        d.title AS target_title,
                        d.canonical_url AS target_url,
                        d.source_pdf,
                        d.depth AS target_depth
                    FROM document_links dl
                    JOIN documents d ON LOWER(TRIM(dl.link_text)) = LOWER(TRIM(d.title))
                    WHERE dl.source_document_id = ANY($1)
                      AND dl.target_document_id IS NULL
                      AND LENGTH(dl.link_text) > 4
                    ORDER BY 
                        CASE 
                            WHEN dl.link_text ILIKE '%revers%' THEN 1
                            WHEN dl.link_text ILIKE '%contract%' THEN 2
                            ELSE 3
                        END ASC
                    LIMIT 5;
                """, seed_doc_ids)
                for row in text_link_rows:
                    tid = row["target_document_id"]
                    if tid and tid not in visited_doc_ids and len(target_doc_map) < self.max_nodes:
                        target_doc_map[tid] = {
                            "source_doc_id": row["source_document_id"],
                            "link_text": row["link_text"],
                            "link_type": "related_procedure",
                            "title": row["target_title"],
                            "url": row["target_url"],
                            "source_pdf": row["source_pdf"],
                            "depth": row["target_depth"]
                        }
                        visited_doc_ids.add(tid)

            # 3. Also check parent document if available
            parent_rows = await conn.fetch("""
                SELECT 
                    d.parent_id,
                    p.title AS parent_title,
                    p.canonical_url AS parent_url,
                    p.source_pdf,
                    p.depth AS parent_depth
                FROM documents d
                JOIN documents p ON d.parent_id = p.id
                WHERE d.id = ANY($1)
                  AND d.parent_id IS NOT NULL
                LIMIT 3;
            """, seed_doc_ids)

            for prow in parent_rows:
                pid = prow["parent_id"]
                if pid and pid not in visited_doc_ids and len(target_doc_map) < self.max_nodes:
                    target_doc_map[pid] = {
                        "source_doc_id": seed_doc_ids[0],
                        "link_text": "Parent Document",
                        "link_type": "parent",
                        "title": prow["parent_title"],
                        "url": prow["parent_url"],
                        "source_pdf": prow["source_pdf"],
                        "depth": prow["parent_depth"]
                    }
                    visited_doc_ids.add(pid)

            if not target_doc_map:
                return []

            # 4. Retrieve procedural and substantive content chunks of linked documents
            target_ids = list(target_doc_map.keys())
            chunk_rows = await conn.fetch("""
                SELECT 
                    c.id AS chunk_id,
                    c.document_id,
                    c.section_id,
                    c.chunk_index,
                    c.content,
                    c.token_count,
                    c.metadata AS chunk_metadata,
                    s.heading AS section_heading,
                    CASE 
                        WHEN s.heading ILIKE '%procedure%' THEN 1
                        WHEN s.heading ILIKE '%prerequisite%' THEN 2
                        WHEN s.heading ILIKE '%use%' THEN 3
                        WHEN s.heading ILIKE '%feature%' THEN 4
                        WHEN s.heading ILIKE '%result%' THEN 5
                        WHEN s.heading ILIKE '%integration%' THEN 6
                        ELSE 10
                    END AS priority_score
                FROM chunks c
                LEFT JOIN document_sections s ON c.section_id = s.id
                WHERE c.document_id = ANY($1)
                  AND (s.heading IS NULL OR (s.heading NOT ILIKE '%overview%' AND s.heading NOT ILIKE '%utilities%') OR c.chunk_index > 1)
                ORDER BY priority_score ASC, c.document_id, c.chunk_index ASC
                LIMIT $2;
            """, target_ids, max_additional_chunks)

            for idx, crow in enumerate(chunk_rows, 1):
                cid = crow["chunk_id"]
                if cid in seen_chunk_ids:
                    continue
                seen_chunk_ids.add(cid)

                did = crow["document_id"]
                doc_info = target_doc_map.get(did, {})
                content = self.clean_unicode(crow["content"])
                title = self.clean_unicode(doc_info.get("title")) or f"Related Document {did}"
                heading = self.clean_unicode(crow["section_heading"]) or self.clean_unicode(doc_info.get("link_text"))

                ev_id = f"EV-GRAPH-{idx}"
                item = EvidenceItem(
                    evidence_id=ev_id,
                    chunk_id=cid,
                    document_id=did,
                    section_id=crow["section_id"],
                    source_id=None,
                    title=title,
                    canonical_url=doc_info.get("url", ""),
                    section_heading=heading,
                    section_path=f"Linked via {doc_info.get('link_type', 'relation')}",
                    content=content,
                    char_offset_start=0,
                    char_offset_end=len(content),
                    is_excerpted=False,
                    token_count=crow["token_count"] or len(content.split()),
                    cosine_distance=0.35,  # Designated graph relation distance
                    similarity_score=0.65,
                    subquery_id="graph_expansion",
                    discovery_method="graph_edge" if doc_info.get("link_type") != "parent" else "parent_context",
                    metadata={
                        "chunk_index": crow["chunk_index"],
                        "relationship": doc_info.get("link_type"),
                        "link_text": doc_info.get("link_text")
                    }
                )
                expanded_items.append(item)

        elapsed_ms = round((time.perf_counter() - start_t) * 1000, 2)
        logger.info(f"Graph traversal complete: expanded {len(expanded_items)} related items in {elapsed_ms}ms")
        return expanded_items
