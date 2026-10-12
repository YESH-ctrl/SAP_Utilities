"""
Script to inspect document titles and source IDs in the database for target concepts.
"""

import asyncio
import json
from sap_rag.database.connection import DatabasePool

async def inspect():
    await DatabasePool.initialize(min_size=2, max_size=5)

    async with DatabasePool.acquire() as conn:
        print("=== DB SOURCES & DOC TITLES INSPECTION ===")
        
        # 1. Inspect Source IDs
        sources = await conn.fetch("SELECT id, title FROM sources ORDER BY id;")
        print("\nAll 29 Sources in DB:")
        for s in sources:
            print(f"Source ID {s['id']:2d} | Title: {s['title']}")

        # 2. Check documents for Source 20, 21 (Clearing Types - Q9)
        print("\nDocuments for Sources 20, 21 (Q9 - Clearing Types):")
        q9_docs = await conn.fetch("SELECT id, source_id, title FROM documents WHERE source_id IN (20, 21);")
        for d in q9_docs:
            print(f"Doc ID {d['id']:4d} | Src {d['source_id']:2d} | Title: {d['title']}")

        # 3. Check documents for Source 13, 15 (Budget Billing - Q10, Q43)
        print("\nDocuments for Sources 13, 15 (Q10, Q43 - Budget Billing):")
        bb_docs = await conn.fetch("SELECT id, source_id, title FROM documents WHERE source_id IN (13, 15);")
        for d in bb_docs:
            print(f"Doc ID {d['id']:4d} | Src {d['source_id']:2d} | Title: {d['title']}")

        # 4. Check documents for Source 1 (Premise - Q41)
        print("\nDocuments for Source 1 (Q41 - Premise):")
        p_docs = await conn.fetch("SELECT id, source_id, title FROM documents WHERE source_id IN (1) AND title ILIKE '%premise%';")
        for d in p_docs:
            print(f"Doc ID {d['id']:4d} | Src {d['source_id']:2d} | Title: {d['title']}")

        # 5. Check documents for Source 29 (Reconnection - Q50)
        print("\nDocuments for Source 29 (Q50 - Reconnection):")
        r_docs = await conn.fetch("SELECT id, source_id, title FROM documents WHERE source_id IN (29) AND (title ILIKE '%reconnect%' OR title ILIKE '%disconnect%');")
        for d in r_docs:
            print(f"Doc ID {d['id']:4d} | Src {d['source_id']:2d} | Title: {d['title']}")

    await DatabasePool.close()

if __name__ == "__main__":
    asyncio.run(inspect())
