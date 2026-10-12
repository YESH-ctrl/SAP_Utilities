"""
Check source_id of Doc 2690 and Doc 2685 in DB.
"""

import asyncio
from sap_rag.database.connection import DatabasePool

async def check():
    await DatabasePool.initialize(min_size=2, max_size=5)
    async with DatabasePool.acquire() as conn:
        rows = await conn.fetch("SELECT id, source_id, title FROM documents WHERE id IN (2690, 2685, 2687);")
        for r in rows:
            print(f"Doc ID {r['id']} | Source ID: {r['source_id']} | Title: {r['title']}")
        
        # Also check all documents in Source 29
        s29 = await conn.fetch("SELECT id, source_id, title FROM documents WHERE source_id = 29;")
        print(f"\nAll documents in Source 29:")
        for r in s29:
            print(f"Doc ID {r['id']} | Source ID: {r['source_id']} | Title: {r['title']}")

        # Also check all documents in Source 10
        s10 = await conn.fetch("SELECT id, source_id, title FROM documents WHERE source_id = 10;")
        print(f"\nAll documents in Source 10:")
        for r in s10:
            print(f"Doc ID {r['id']} | Source ID: {r['source_id']} | Title: {r['title']}")

    await DatabasePool.close()

if __name__ == "__main__":
    asyncio.run(check())
