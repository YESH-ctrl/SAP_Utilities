import argparse
import asyncio
import logging
import sys

# Configure UTF-8 output encoding for Windows terminals
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from sap_rag.database.connection import DatabasePool
from sap_rag.database.repositories.document_repository import DocumentRepository
from sap_rag.database.repositories.source_repository import SourceRepository

logging.basicConfig(level=logging.ERROR)

async def main():
    parser = argparse.ArgumentParser(description="Inspect SAP Documentation Tree stored in Supabase.")
    parser.add_argument("--root-document-id", type=int, help="Root document ID to display tree for")
    parser.add_argument("--source-id", type=int, help="Source ID to display tree for")

    args = parser.parse_args()

    await DatabasePool.initialize(min_size=1, max_size=2)
    try:
        async with DatabasePool.acquire() as conn:
            root_id = args.root_document_id

            if not root_id and args.source_id:
                source = await SourceRepository.get_by_id(conn, args.source_id)
                if source:
                    row = await conn.fetchrow(
                        "SELECT id FROM documents WHERE canonical_url = $1 AND depth = 0;",
                        source["seed_url"]
                    )
                    if row:
                        root_id = row["id"]

            if not root_id:
                row = await conn.fetchrow("SELECT id FROM documents WHERE depth = 0 ORDER BY id ASC LIMIT 1;")
                if row:
                    root_id = row["id"]

            if not root_id:
                print("No root document found in database.")
                return

            nodes = await DocumentRepository.get_tree_under_root(conn, root_id)

            print("\n" + "=" * 80)
            print(f"SAP DOCUMENTATION HIERARCHY TREE IN SUPABASE (Root ID: {root_id})")
            print("=" * 80)

            for node in nodes:
                depth = node["depth"]
                title = node["title"]
                doc_type = node["document_type"]
                status = node["status"]
                doc_id = node["id"]
                parent_id = node["parent_id"]
                indent = "|   " * depth + ("|-- " if depth > 0 else "")
                print(f"{indent}[ID:{doc_id}] {title} (depth:{depth}, type:{doc_type}, parent_id:{parent_id}, status:{status})")

            print("=" * 80 + "\n")
    finally:
        await DatabasePool.close()

if __name__ == "__main__":
    asyncio.run(main())
