import json
from typing import Optional, List, Dict, Any
import asyncpg

class SectionRepository:
    """
    Repository for storing page outline & semantic sections in `document_sections`.
    """

    @classmethod
    async def replace_sections_for_document(
        cls,
        conn: asyncpg.Connection,
        document_id: int,
        sections: List[Dict[str, Any]]
    ):
        """
        Delete old sections for a document and insert clean section hierarchy.
        """
        await conn.execute("DELETE FROM document_sections WHERE document_id = $1;", document_id)

        for sec in sections:
            metadata_json = json.dumps(sec.get("metadata", {}))
            await conn.execute(
                """
                INSERT INTO document_sections (
                    document_id, parent_section_id, heading, content, section_order, level, metadata
                ) VALUES ($1, $2, $3, $4, $5, $6, $7::jsonb);
                """,
                document_id,
                sec.get("parent_section_id"),
                sec["heading"],
                sec.get("content"),
                sec.get("section_order", 0),
                sec.get("level", 1),
                metadata_json
            )
