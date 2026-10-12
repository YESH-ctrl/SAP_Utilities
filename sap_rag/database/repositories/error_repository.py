from typing import Optional
import asyncpg

class ErrorRepository:
    """
    Repository for recording crawler failure logs in `crawl_errors`.
    """

    @classmethod
    async def log_error(
        cls,
        conn: asyncpg.Connection,
        crawl_job_id: int,
        url: str,
        error_type: str,
        error_message: str,
        http_status: Optional[int] = None,
        attempt_number: int = 1
    ) -> int:
        row = await conn.fetchrow(
            """
            INSERT INTO crawl_errors (
                crawl_job_id, url, error_type, error_message, http_status, attempt_number
            ) VALUES ($1, $2, $3, $4, $5, $6)
            RETURNING id;
            """,
            crawl_job_id, url, error_type, error_message, http_status, attempt_number
        )
        return row["id"]
