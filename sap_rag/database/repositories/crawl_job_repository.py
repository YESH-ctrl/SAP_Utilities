from typing import Optional, List, Dict, Any
from datetime import datetime
import asyncpg

class CrawlJobRepository:
    """
    Repository for stateful, restartable crawl task queue operations (`crawl_jobs`).
    Supports atomic worker claiming via row-locking (`FOR UPDATE SKIP LOCKED`).
    """

    @classmethod
    async def claim_pending_job(
        cls,
        conn: asyncpg.Connection,
        source_id_filter: Optional[int] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Atomically claim a pending crawl job using PostgreSQL FOR UPDATE SKIP LOCKED.
        """
        if source_id_filter:
            row = await conn.fetchrow(
                """
                SELECT id, source_id, document_id, url, parent_document_id, depth, status,
                       priority, attempts, max_attempts, last_error, scheduled_at, created_at, updated_at
                FROM crawl_jobs
                WHERE status = 'pending' AND source_id = $1 AND scheduled_at <= NOW()
                ORDER BY priority DESC, id ASC
                FOR UPDATE SKIP LOCKED
                LIMIT 1;
                """,
                source_id_filter
            )
        else:
            row = await conn.fetchrow(
                """
                SELECT id, source_id, document_id, url, parent_document_id, depth, status,
                       priority, attempts, max_attempts, last_error, scheduled_at, created_at, updated_at
                FROM crawl_jobs
                WHERE status = 'pending' AND scheduled_at <= NOW()
                ORDER BY priority DESC, id ASC
                FOR UPDATE SKIP LOCKED
                LIMIT 1;
                """
            )

        if not row:
            return None

        job_id = row["id"]
        # Transition state from pending -> crawling
        await conn.execute(
            """
            UPDATE crawl_jobs
            SET status = 'crawling',
                started_at = NOW(),
                updated_at = NOW()
            WHERE id = $1;
            """,
            job_id
        )

        job_dict = dict(row)
        job_dict["status"] = "crawling"
        return job_dict

    @classmethod
    async def get_pending_job_read_only(
        cls,
        conn: asyncpg.Connection,
        source_id_filter: Optional[int] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Fetch a pending job without updating its status (read-only for dry-run).
        """
        if source_id_filter:
            row = await conn.fetchrow(
                """
                SELECT id, source_id, document_id, url, parent_document_id, depth, status,
                       priority, attempts, max_attempts, last_error, scheduled_at, created_at, updated_at
                FROM crawl_jobs
                WHERE (status = 'pending' OR status = 'crawling') AND source_id = $1
                ORDER BY priority DESC, id ASC
                LIMIT 1;
                """,
                source_id_filter
            )
        else:
            row = await conn.fetchrow(
                """
                SELECT id, source_id, document_id, url, parent_document_id, depth, status,
                       priority, attempts, max_attempts, last_error, scheduled_at, created_at, updated_at
                FROM crawl_jobs
                WHERE status = 'pending' OR status = 'crawling'
                ORDER BY priority DESC, id ASC
                LIMIT 1;
                """
            )
        return dict(row) if row else None

    @classmethod
    async def schedule_child_job(
        cls,
        conn: asyncpg.Connection,
        source_id: Optional[int],
        url: str,
        parent_document_id: Optional[int],
        depth: int,
        priority: int = 10,
        max_attempts: int = 3
    ) -> Optional[int]:
        """
        Schedule a new crawl job for a discovered child URL.
        Deduplication protected by partial unique index idx_crawl_jobs_url_active.
        """
        row = await conn.fetchrow(
            """
            INSERT INTO crawl_jobs (
                source_id, url, parent_document_id, depth, status, priority, max_attempts, scheduled_at
            ) VALUES ($1, $2, $3, $4, 'pending', $5, $6, NOW())
            ON CONFLICT (url) WHERE status IN ('pending', 'queued', 'crawling') DO NOTHING
            RETURNING id;
            """,
            source_id, url, parent_document_id, depth, priority, max_attempts
        )
        return row["id"] if row else None

    @classmethod
    async def mark_success(
        cls,
        conn: asyncpg.Connection,
        job_id: int,
        document_id: Optional[int] = None
    ):
        await conn.execute(
            """
            UPDATE crawl_jobs
            SET status = 'success',
                document_id = COALESCE($2, document_id),
                completed_at = NOW(),
                updated_at = NOW()
            WHERE id = $1;
            """,
            job_id, document_id
        )

    @classmethod
    async def mark_failed_or_retry(
        cls,
        conn: asyncpg.Connection,
        job_id: int,
        error_message: str,
        max_attempts: int = 3
    ):
        row = await conn.fetchrow(
            """
            UPDATE crawl_jobs
            SET attempts = attempts + 1,
                last_error = $2,
                status = CASE WHEN attempts + 1 >= $3 THEN 'failed' ELSE 'pending' END,
                scheduled_at = NOW() + (INTERVAL '5 seconds' * (attempts + 1)),
                updated_at = NOW()
            WHERE id = $1
            RETURNING url, status;
            """,
            job_id, error_message, max_attempts
        )
        if row and row["status"] == "failed":
            await conn.execute(
                """
                UPDATE documents
                SET status = 'failed',
                    updated_at = NOW()
                WHERE canonical_url = $1 AND status = 'pending';
                """,
                row["url"]
            )

    @classmethod
    async def requeue_failed_jobs(cls, conn: asyncpg.Connection) -> int:
        """
        Reset failed jobs back to pending state for retries.
        """
        result = await conn.execute(
            """
            UPDATE crawl_jobs
            SET status = 'pending',
                attempts = 0,
                last_error = NULL,
                scheduled_at = NOW(),
                updated_at = NOW()
            WHERE status = 'failed';
            """
        )
        # Result format: "UPDATE <count>"
        parts = result.split(" ")
        return int(parts[1]) if len(parts) > 1 else 0

    @classmethod
    async def reclaim_stale_crawling_jobs(cls, conn: asyncpg.Connection, timeout_seconds: int = 300) -> int:
        """
        Reclaim jobs stuck in 'crawling' state whose started_at was more than timeout_seconds ago.
        If attempts + 1 >= max_attempts, mark as failed. Otherwise reset status to 'pending'.
        """
        rows = await conn.fetch(
            """
            SELECT id, url, attempts, max_attempts
            FROM crawl_jobs
            WHERE status = 'crawling' AND started_at < NOW() - (INTERVAL '1 second' * $1);
            """,
            timeout_seconds
        )
        reclaimed_count = 0
        for r in rows:
            job_id = r["id"]
            attempts = r["attempts"]
            max_attempts = r["max_attempts"]
            if attempts + 1 >= max_attempts:
                await conn.execute(
                    """
                    UPDATE crawl_jobs
                    SET status = 'failed',
                        attempts = attempts + 1,
                        last_error = 'Stale worker timeout exceeded',
                        completed_at = NOW(),
                        updated_at = NOW()
                    WHERE id = $1;
                    """,
                    job_id
                )
            else:
                await conn.execute(
                    """
                    UPDATE crawl_jobs
                    SET status = 'pending',
                        attempts = attempts + 1,
                        started_at = NULL,
                        last_error = 'Stale worker timeout reset',
                        scheduled_at = NOW(),
                        updated_at = NOW()
                    WHERE id = $1;
                    """,
                    job_id
                )
            reclaimed_count += 1
        return reclaimed_count

