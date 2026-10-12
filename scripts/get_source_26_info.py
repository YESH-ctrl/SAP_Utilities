import asyncio
from sap_rag.database.connection import DatabasePool

async def main():
    await DatabasePool.initialize()
    async with DatabasePool.acquire() as conn:
        src = await conn.fetchrow("SELECT id, title, seed_url FROM sources WHERE id = 26;")
        print("Source #26:", dict(src) if src else None)
        job = await conn.fetchrow("SELECT id, url, depth FROM crawl_jobs WHERE source_id = 26 AND depth = 0 LIMIT 1;")
        print("Job #26:", dict(job) if job else None)
    await DatabasePool.close()

if __name__ == "__main__":
    asyncio.run(main())
