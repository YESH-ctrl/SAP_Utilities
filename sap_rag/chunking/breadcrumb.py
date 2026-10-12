"""
Breadcrumb builder using database hierarchy:
source.title -> root_document -> parent_document -> ... -> document
"""

from typing import Dict, Any, List, Optional
import asyncpg
import logging

logger = logging.getLogger(__name__)

class BreadcrumbBuilder:
    """
    Builds clean, hierarchical breadcrumbs derived from the database hierarchy.
    Maintains in-memory map per batch to prevent N+1 DB queries.
    """

    def __init__(self):
        # Map: doc_id -> dict with keys: 'id', 'parent_id', 'title', 'source_title'
        self._doc_map: Dict[int, Dict[str, Any]] = {}

    def load_documents_map(self, doc_rows: List[Dict[str, Any]]):
        """
        Preload document dictionary from fetched records.
        """
        for r in doc_rows:
            self._doc_map[r["id"]] = r

    async def fetch_source_hierarchy(self, conn: asyncpg.Connection, source_id: int):
        """
        Fetch all documents for a given source and build the document tree map.
        """
        rows = await conn.fetch(
            """
            SELECT d.id, d.source_id, d.parent_id, d.root_document_id, d.title, s.title as source_title
            FROM documents d
            LEFT JOIN sources s ON d.source_id = s.id
            WHERE d.source_id = $1;
            """,
            source_id
        )
        for r in rows:
            self._doc_map[r["id"]] = dict(r)

    def build_breadcrumb(self, document_id: int, section_title: Optional[str] = None) -> str:
        """
        Construct breadcrumb string for a given document_id and optional section_title.
        Example output:
        'SAP Utilities Billing Procedure > Automatic Billing > Billing Documents > Creating Billing Documents'
        """
        path_titles = []
        curr_id = document_id
        visited = set()

        source_title = None

        while curr_id and curr_id not in visited:
            visited.add(curr_id)
            doc = self._doc_map.get(curr_id)
            if not doc:
                break

            if doc.get("title"):
                path_titles.append(doc["title"])

            if not source_title and doc.get("source_title"):
                source_title = doc["source_title"]

            curr_id = doc.get("parent_id")

        # Reverse path so it goes root -> child
        path_titles.reverse()

        # Prepend source title if available and distinct from root doc title
        if source_title:
            if not path_titles or path_titles[0] != source_title:
                path_titles.insert(0, source_title)

        # Append section title if given
        if section_title and (not path_titles or path_titles[-1] != section_title):
            path_titles.append(section_title)

        return " > ".join(path_titles) if path_titles else (section_title or "SAP Documentation")
