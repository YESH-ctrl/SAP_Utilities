import asyncio
from sap_rag.database.connection import DatabasePool

async def main():
    await DatabasePool.initialize()
    async with DatabasePool.acquire() as conn:
        src = await conn.fetchrow("SELECT * FROM sources WHERE id = 11;")
        print("Source #11:", dict(src) if src else None)
        root_doc = await conn.fetchrow("SELECT id, title, canonical_url, depth FROM documents WHERE source_id = 11 AND depth = 0;")
        print("Root Doc #11:", dict(root_doc) if root_doc else None)
    await DatabasePool.close()

if __name__ == "__main__":
    asyncio.run(main())
