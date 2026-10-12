import argparse
import asyncio
import logging
import sys

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from sap_rag.database.connection import DatabasePool
from sap_rag.database.repositories.source_repository import SourceRepository

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("reset_source")

async def reset_source_data(source_id: int):
    logger.info(f"Connecting to Supabase to reset data for source_id={source_id}...")
    await DatabasePool.initialize(min_size=1, max_size=2)
    try:
        async with DatabasePool.acquire() as conn:
            source = await SourceRepository.get_by_id(conn, source_id)
            if not source:
                logger.error(f"Source with ID #{source_id} not found in database.")
                return

            print("\n" + "=" * 60)
            print(f"RESETTING CRAWL DATA FOR SOURCE #{source_id} ({source['title']})")
            print("=" * 60)

            async with conn.transaction():
                # 1. Delete All Child Crawl Jobs
                deleted_jobs = await conn.execute(
                    "DELETE FROM crawl_jobs WHERE source_id = $1 AND depth > 0;",
                    source_id
                )

                # 2. Delete All Child Document Sections
                deleted_sections = await conn.execute(
                    """
                    DELETE FROM document_sections 
                    WHERE document_id IN (
                        SELECT id FROM documents WHERE source_id = $1 AND depth > 0
                    );
                    """,
                    source_id
                )

                # 3. Delete All Child Document Links
                deleted_links = await conn.execute(
                    """
                    DELETE FROM document_links 
                    WHERE source_document_id IN (
                        SELECT id FROM documents WHERE source_id = $1 AND depth > 0
                    );
                    """,
                    source_id
                )

                # 4. Delete All Child Documents
                deleted_docs = await conn.execute(
                    "DELETE FROM documents WHERE source_id = $1 AND depth > 0;",
                    source_id
                )

                # 5. Reset Root Document State
                await conn.execute(
                    """
                    UPDATE documents 
                    SET status = 'pending',
                        content = NULL,
                        content_hash = NULL,
                        updated_at = NOW()
                    WHERE source_id = $1 AND depth = 0;
                    """,
                    source_id
                )

                # 6. Requeue Root Crawl Job
                requeued_root_job = await conn.execute(
                    """
                    UPDATE crawl_jobs 
                    SET status = 'pending',
                        attempts = 0,
                        last_error = NULL,
                        scheduled_at = NOW(),
                        started_at = NULL,
                        completed_at = NULL,
                        updated_at = NOW()
                    WHERE source_id = $1 AND depth = 0;
                    """,
                    source_id
                )

            print(f"Summary of Reset Operations for Source #{source_id}:")
            print(f" - Deleted Child Sections       : {deleted_sections}")
            print(f" - Deleted Child Document Links : {deleted_links}")
            print(f" - Deleted Child Documents      : {deleted_docs}")
            print(f" - Deleted Child Crawl Jobs     : {deleted_jobs}")
            print(f" - Requeued Root Crawl Job      : {requeued_root_job}")
            print(f" - Source Record & Root Doc     : PRESERVED")
            print("=" * 60 + "\n")
    finally:
        await DatabasePool.close()

def main():
    parser = argparse.ArgumentParser(description="Reset child documents and crawl jobs for a specific source ID.")
    parser.add_argument("--source-id", type=int, required=True, help="Source ID to reset (e.g. 1)")
    args = parser.parse_args()

    asyncio.run(reset_source_data(args.source_id))

if __name__ == "__main__":
    main()
