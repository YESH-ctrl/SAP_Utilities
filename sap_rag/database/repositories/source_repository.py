from typing import Optional, List, Dict, Any
import asyncpg

class SourceRepository:
    """
    Repository for interacting with the `sources` table.
    """

    @classmethod
    async def get_by_id(cls, conn: asyncpg.Connection, source_id: int) -> Optional[Dict[str, Any]]:
        row = await conn.fetchrow(
            "SELECT id, source_file, title, category, seed_url, product, version, source_type, metadata, created_at, updated_at FROM sources WHERE id = $1;",
            source_id
        )
        return dict(row) if row else None

    @classmethod
    async def get_by_file(cls, conn: asyncpg.Connection, source_file: str) -> Optional[Dict[str, Any]]:
        row = await conn.fetchrow(
            "SELECT id, source_file, title, category, seed_url, product, version, source_type, metadata, created_at, updated_at FROM sources WHERE source_file = $1;",
            source_file
        )
        return dict(row) if row else None

    @classmethod
    async def list_all(cls, conn: asyncpg.Connection) -> List[Dict[str, Any]]:
        rows = await conn.fetch(
            "SELECT id, source_file, title, category, seed_url, product, version, source_type, metadata, created_at, updated_at FROM sources ORDER BY id ASC;"
        )
        return [dict(r) for r in rows]
