"""
Database repository for `chunks` table.
"""

import json
from typing import List, Dict, Any, Optional
import asyncpg
import logging

logger = logging.getLogger(__name__)

class ChunkRepository:
    """
    Repository for storing and querying semantic chunks in `chunks`.
    """

    @classmethod
    async def replace_chunks_for_document(
        cls,
        conn: asyncpg.Connection,
        document_id: int,
        version: str,
        chunks: List[Dict[str, Any]]
    ):
        """
        Transactional deletion of previous chunks for document_id & version, and insertion of new chunks.
        """
        # Delete existing chunks for this document matching chunking version
        await conn.execute(
            """
            DELETE FROM chunks 
            WHERE document_id = $1 
              AND (metadata->>'chunking_version' = $2 OR metadata->>'chunking_version' IS NULL);
            """,
            document_id,
            version
        )

        if not chunks:
            return

        records = [
            (
                document_id,
                chk.get("section_id"),
                chk.get("chunk_index", 0),
                chk["content"],
                chk.get("token_count", 0),
                chk.get("content_hash"),
                json.dumps(chk.get("metadata", {}))
            )
            for chk in chunks
        ]

        await conn.executemany(
            """
            INSERT INTO chunks (
                document_id, section_id, chunk_index, content, token_count, content_hash, metadata
            ) VALUES (
                $1, $2, $3, $4, $5, $6, $7::jsonb
            );
            """,
            records
        )

    @classmethod
    async def delete_chunks_for_document(cls, conn: asyncpg.Connection, document_id: int, version: str):
        await conn.execute(
            "DELETE FROM chunks WHERE document_id = $1 AND metadata->>'chunking_version' = $2;",
            document_id,
            version
        )

    @classmethod
    async def get_chunks_by_document(cls, conn: asyncpg.Connection, document_id: int) -> List[Dict[str, Any]]:
        rows = await conn.fetch(
            """
            SELECT id, document_id, section_id, chunk_index, content, token_count, content_hash, metadata, created_at
            FROM chunks WHERE document_id = $1 ORDER BY chunk_index;
            """,
            document_id
        )
        return [dict(r) for r in rows]

    @classmethod
    async def get_total_chunks_count(cls, conn: asyncpg.Connection) -> int:
        val = await conn.fetchval("SELECT COUNT(*) FROM chunks;")
        return val or 0
