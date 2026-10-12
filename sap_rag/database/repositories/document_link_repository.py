from typing import Optional, List, Dict, Any
import asyncpg

class DocumentLinkRepository:
    """
    Repository for interacting with the `document_links` table.
    """

    @classmethod
    async def insert_link(
        cls,
        conn: asyncpg.Connection,
        source_document_id: int,
        target_url: str,
        target_document_id: Optional[int] = None,
        link_text: Optional[str] = None,
        link_type: str = "child",
        is_internal: bool = True,
        is_crawled: bool = False
    ) -> Optional[int]:
        row = await conn.fetchrow(
            """
            INSERT INTO document_links (
                source_document_id, target_document_id, target_url, link_text, link_type, is_internal, is_crawled
            ) VALUES ($1, $2, $3, $4, $5, $6, $7)
            ON CONFLICT (source_document_id, target_url) DO UPDATE SET
                target_document_id = COALESCE(EXCLUDED.target_document_id, document_links.target_document_id),
                link_type = EXCLUDED.link_type,
                is_crawled = EXCLUDED.is_crawled
            RETURNING id;
            """,
            source_document_id, target_document_id, target_url, link_text, link_type, is_internal, is_crawled
        )
        return row["id"] if row else None

    @classmethod
    async def bulk_insert_links(
        cls,
        conn: asyncpg.Connection,
        links: List[Dict[str, Any]]
    ):
        for link in links:
            await cls.insert_link(
                conn,
                source_document_id=link["source_document_id"],
                target_url=link["target_url"],
                target_document_id=link.get("target_document_id"),
                link_text=link.get("link_text"),
                link_type=link.get("link_type", "child"),
                is_internal=link.get("is_internal", True),
                is_crawled=link.get("is_crawled", False)
            )
