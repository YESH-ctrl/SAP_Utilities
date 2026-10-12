"""
Chunking service orchestrating document section chunking, breadcrumb hierarchy, dry-run, and transactional DB updates.
"""

import asyncio
import time
import logging
from typing import List, Dict, Any, Optional
import asyncpg
import json

from sap_rag.database.connection import DatabasePool
from sap_rag.chunking.config import chunking_settings
from sap_rag.chunking.semantic_chunker import SemanticChunker
from sap_rag.chunking.breadcrumb import BreadcrumbBuilder
from sap_rag.chunking.validators import ChunkValidator
from sap_rag.chunking.metrics import ChunkMetricsCalculator
from sap_rag.database.repositories.chunk_repository import ChunkRepository

logger = logging.getLogger(__name__)

class ChunkingService:
    """
    Service for executing structure-aware semantic chunking across documents and sources.
    """

    def __init__(self, chunker: Optional[SemanticChunker] = None):
        self.chunker = chunker or SemanticChunker()

    async def process_document(
        self,
        conn: asyncpg.Connection,
        doc_id: int,
        breadcrumb_builder: Optional[BreadcrumbBuilder] = None,
        dry_run: bool = False
    ) -> Dict[str, Any]:
        """
        Process a single document: read sections, chunk, validate, and persist.
        """
        start_time = time.time()

        # Fetch document record
        doc_row = await conn.fetchrow(
            """
            SELECT d.id, d.source_id, d.parent_id, d.root_document_id, d.title, d.url, d.canonical_url,
                   d.source_pdf, d.depth, s.title as source_title
            FROM documents d
            LEFT JOIN sources s ON d.source_id = s.id
            WHERE d.id = $1;
            """,
            doc_id
        )

        if not doc_row:
            raise ValueError(f"Document ID {doc_id} not found in database.")

        doc_info = dict(doc_row)

        # Build breadcrumb hierarchy
        if breadcrumb_builder is None:
            breadcrumb_builder = BreadcrumbBuilder()
            if doc_info.get("source_id"):
                await breadcrumb_builder.fetch_source_hierarchy(conn, doc_info["source_id"])
            else:
                breadcrumb_builder.load_documents_map([doc_info])

        breadcrumb = breadcrumb_builder.build_breadcrumb(doc_id)

        # Fetch document sections
        sec_rows = await conn.fetch(
            """
            SELECT id, document_id, parent_section_id, heading, content, section_order, level, metadata
            FROM document_sections
            WHERE document_id = $1
            ORDER BY section_order, id;
            """,
            doc_id
        )

        all_doc_chunks: List[Dict[str, Any]] = []
        sections_processed = 0
        sections_skipped = 0

        for s_row in sec_rows:
            sec_dict = dict(s_row)
            sec_heading = sec_dict.get("heading")
            sec_bc = breadcrumb_builder.build_breadcrumb(doc_id, section_title=sec_heading)

            chunks = self.chunker.chunk_section(
                doc_info=doc_info,
                section=sec_dict,
                breadcrumb=sec_bc,
                chunking_version=chunking_settings.CHUNKING_VERSION
            )

            if not chunks:
                sections_skipped += 1
            else:
                sections_processed += 1
                all_doc_chunks.extend(chunks)

        # Re-index chunk_index sequentially for document
        for i, chk in enumerate(all_doc_chunks):
            chk["chunk_index"] = i
            chk["metadata"]["chunk_index"] = i

        # Run automated quality validation
        is_valid, validation_errors = ChunkValidator.validate_chunks(all_doc_chunks)
        if not is_valid:
            logger.error(f"Validation failed for doc_id={doc_id}: {validation_errors[:5]}")

        # Persist if not dry-run
        if not dry_run:
            await ChunkRepository.replace_chunks_for_document(
                conn=conn,
                document_id=doc_id,
                version=chunking_settings.CHUNKING_VERSION,
                chunks=all_doc_chunks
            )

        duration = round(time.time() - start_time, 3)

        logger.info(
            f"Doc ID {doc_id} ('{doc_info.get('title')}'): {len(all_doc_chunks)} chunks generated "
            f"({sections_processed} sections processed, {sections_skipped} skipped) in {duration}s."
        )

        return {
            "document_id": doc_id,
            "document_title": doc_info.get("title"),
            "source_id": doc_info.get("source_id"),
            "sections_total": len(sec_rows),
            "sections_processed": sections_processed,
            "sections_skipped": sections_skipped,
            "chunks_created": len(all_doc_chunks),
            "chunks": all_doc_chunks,
            "duration": duration,
            "validation_errors": validation_errors
        }

    async def process_source(
        self,
        conn: asyncpg.Connection,
        source_id: int,
        dry_run: bool = False
    ) -> Dict[str, Any]:
        """
        High-performance batch processing of all documents in a source_id using PostgreSQL UNNEST.
        """
        start_time = time.time()

        # 1. Fetch document tree hierarchy
        bc_builder = BreadcrumbBuilder()
        await bc_builder.fetch_source_hierarchy(conn, source_id)

        doc_rows = await conn.fetch(
            """
            SELECT d.id, d.source_id, d.parent_id, d.root_document_id, d.title, d.url, d.canonical_url,
                   d.source_pdf, d.depth, s.title as source_title
            FROM documents d
            LEFT JOIN sources s ON d.source_id = s.id
            WHERE d.source_id = $1
            ORDER BY d.id;
            """,
            source_id
        )

        if not doc_rows:
            return {
                "source_id": source_id,
                "documents_count": 0,
                "sections_processed": 0,
                "sections_skipped": 0,
                "chunks_count": 0,
                "metrics": ChunkMetricsCalculator.compute_metrics([]),
                "doc_summaries": []
            }

        doc_dict_map = {r["id"]: dict(r) for r in doc_rows}

        doc_ids_list = list(doc_dict_map.keys())
        sec_rows = await conn.fetch(
            """
            SELECT id, document_id, parent_section_id, heading, content, section_order, level, metadata
            FROM document_sections
            WHERE document_id = ANY($1::bigint[])
            ORDER BY document_id, section_order, id;
            """,
            doc_ids_list
        )

        doc_sections_map: Dict[int, List[Dict[str, Any]]] = {doc_id: [] for doc_id in doc_dict_map}
        for s in sec_rows:
            doc_sections_map[s["document_id"]].append(dict(s))

        # 3. Chunk documents in memory
        all_source_chunks: List[Dict[str, Any]] = []
        doc_summaries: List[Dict[str, Any]] = []
        total_proc_secs = 0
        total_skip_secs = 0

        doc_ids, sec_ids, chunk_idxs, contents, token_counts, hashes, metadatas = [], [], [], [], [], [], []

        for doc_id, doc_info in doc_dict_map.items():
            sections = doc_sections_map.get(doc_id, [])
            doc_chunks = []
            proc_secs = 0
            skip_secs = 0

            for sec in sections:
                sec_heading = sec.get("heading")
                sec_bc = bc_builder.build_breadcrumb(doc_id, section_title=sec_heading)

                chunks = self.chunker.chunk_section(
                    doc_info=doc_info,
                    section=sec,
                    breadcrumb=sec_bc,
                    chunking_version=chunking_settings.CHUNKING_VERSION
                )

                if not chunks:
                    skip_secs += 1
                else:
                    proc_secs += 1
                    doc_chunks.extend(chunks)

            # Re-index
            for i, chk in enumerate(doc_chunks):
                chk["chunk_index"] = i
                chk["metadata"]["chunk_index"] = i
                
                doc_ids.append(chk["document_id"])
                sec_ids.append(chk["section_id"])
                chunk_idxs.append(chk["chunk_index"])
                contents.append(chk["content"])
                token_counts.append(chk["token_count"])
                hashes.append(chk["content_hash"])
                metadatas.append(json.dumps(chk["metadata"]))

            all_source_chunks.extend(doc_chunks)
            total_proc_secs += proc_secs
            total_skip_secs += skip_secs

            doc_summaries.append({
                "document_id": doc_id,
                "document_title": doc_info.get("title"),
                "source_id": source_id,
                "sections_total": len(sections),
                "sections_processed": proc_secs,
                "sections_skipped": skip_secs,
                "chunks_created": len(doc_chunks),
                "chunks": doc_chunks,
                "duration": 0,
                "validation_errors": []
            })

        insert_records = list(zip(doc_ids, sec_ids, chunk_idxs, contents, token_counts, hashes, metadatas))

        # 4. Batch persistence to Database if not dry_run
        if not dry_run:
            async with conn.transaction():
                await conn.execute(
                    """
                    DELETE FROM chunks 
                    WHERE document_id IN (SELECT id FROM documents WHERE source_id = $1)
                      AND (metadata->>'chunking_version' = $2 OR metadata->>'chunking_version' IS NULL);
                    """,
                    source_id,
                    chunking_settings.CHUNKING_VERSION
                )

                if doc_ids:
                    await conn.execute(
                        """
                        INSERT INTO chunks (
                            document_id, section_id, chunk_index, content, token_count, content_hash, metadata
                        )
                        SELECT d, s, i, c, tc, h, m::jsonb
                        FROM unnest(
                            $1::bigint[], $2::bigint[], $3::int[], $4::text[], $5::int[], $6::text[], $7::text[]
                        ) AS t(d, s, i, c, tc, h, m);
                        """,
                        doc_ids, sec_ids, chunk_idxs, contents, token_counts, hashes, metadatas
                    )

        duration = round(time.time() - start_time, 3)
        logger.info(
            f"Source #{source_id}: Processed {len(doc_rows)} docs, {total_proc_secs} sections -> "
            f"{len(all_source_chunks)} chunks created in {duration}s."
        )

        metrics = ChunkMetricsCalculator.compute_metrics(all_source_chunks)

        return {
            "source_id": source_id,
            "documents_count": len(doc_rows),
            "sections_processed": total_proc_secs,
            "sections_skipped": total_skip_secs,
            "chunks_count": len(all_source_chunks),
            "metrics": metrics,
            "doc_summaries": doc_summaries
        }
