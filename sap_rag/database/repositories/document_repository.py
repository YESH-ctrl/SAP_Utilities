import json
from typing import Optional, List, Dict, Any
import asyncpg

class DocumentRepository:
    """
    Repository for interacting with the `documents` hierarchy table.
    """

    @classmethod
    async def get_by_id(cls, conn: asyncpg.Connection, doc_id: int) -> Optional[Dict[str, Any]]:
        row = await conn.fetchrow(
            """
            SELECT id, source_id, parent_id, root_document_id, title, url, canonical_url,
                   source_pdf, depth, document_type, content, content_hash, status, metadata,
                   created_at, updated_at, last_crawled_at
            FROM documents WHERE id = $1;
            """,
            doc_id
        )
        return dict(row) if row else None

    @classmethod
    async def get_by_canonical_url(cls, conn: asyncpg.Connection, canonical_url: str) -> Optional[Dict[str, Any]]:
        row = await conn.fetchrow(
            """
            SELECT id, source_id, parent_id, root_document_id, title, url, canonical_url,
                   source_pdf, depth, document_type, content, content_hash, status, metadata,
                   created_at, updated_at, last_crawled_at
            FROM documents WHERE canonical_url = $1;
            """,
            canonical_url
        )
        return dict(row) if row else None

    @classmethod
    async def upsert_document(
        cls,
        conn: asyncpg.Connection,
        source_id: Optional[int],
        parent_id: Optional[int],
        root_document_id: Optional[int],
        title: str,
        url: str,
        canonical_url: str,
        source_pdf: Optional[str],
        depth: int,
        document_type: str,
        content: Optional[str] = None,
        content_hash: Optional[str] = None,
        status: str = "crawled",
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Upsert a document record into the `documents` table using canonical_url identity.
        """
        metadata_json = json.dumps(metadata or {})
        row = await conn.fetchrow(
            """
            INSERT INTO documents (
                source_id, parent_id, root_document_id, title, url, canonical_url,
                source_pdf, depth, document_type, content, content_hash, status, metadata, last_crawled_at
            ) VALUES (
                $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12::varchar, $13::jsonb,
                CASE WHEN $12::varchar = 'crawled' THEN NOW() ELSE NULL END
            )
            ON CONFLICT (canonical_url) DO UPDATE SET
                title = EXCLUDED.title,
                content = COALESCE(EXCLUDED.content, documents.content),
                content_hash = COALESCE(EXCLUDED.content_hash, documents.content_hash),
                status = CASE
                    WHEN EXCLUDED.status = 'crawled' THEN 'crawled'
                    ELSE documents.status
                END,
                last_crawled_at = CASE
                    WHEN EXCLUDED.status = 'crawled' THEN NOW()
                    ELSE documents.last_crawled_at
                END,
                updated_at = NOW()
            RETURNING id, source_id, parent_id, root_document_id, title, url, canonical_url,
                      source_pdf, depth, document_type, content, content_hash, status, metadata,
                      created_at, updated_at, last_crawled_at;
            """,
            source_id, parent_id, root_document_id, title, url, canonical_url,
            source_pdf, depth, document_type, content, content_hash, status, metadata_json
        )
        return dict(row)

    @classmethod
    async def get_tree_under_root(cls, conn: asyncpg.Connection, root_doc_id: int) -> List[Dict[str, Any]]:
        """
        Get complete documentation tree under a root document using recursive CTE.
        """
        rows = await conn.fetch(
            """
            WITH RECURSIVE doc_tree AS (
                SELECT id, source_id, parent_id, root_document_id, title, url, canonical_url,
                       depth, document_type, status, ARRAY[title] AS path
                FROM documents
                WHERE id = $1

                UNION ALL

                SELECT d.id, d.source_id, d.parent_id, d.root_document_id, d.title, d.url, d.canonical_url,
                       d.depth, d.document_type, d.status, dt.path || d.title AS path
                FROM documents d
                INNER JOIN doc_tree dt ON d.parent_id = dt.id
            )
            SELECT * FROM doc_tree ORDER BY path;
            """,
            root_doc_id
        )
        return [dict(r) for r in rows]
