import asyncio
import logging
import socket
from typing import Optional
from contextlib import asynccontextmanager
import asyncpg

from sap_rag.crawler.config import settings

logger = logging.getLogger(__name__)

class DatabasePool:
    """
    Async PostgreSQL Connection Pool manager using asyncpg for Supabase.
    """
    _pool: Optional[asyncpg.Pool] = None

    @classmethod
    async def initialize(cls, min_size: int = 1, max_size: int = 5):
        """
        Initialize the asyncpg connection pool with ssl='require'.
        """
        if cls._pool is None:
            logger.info(f"Initializing asyncpg pool to Supabase ({settings.SUPABASE_DB_HOST}:{settings.SUPABASE_DB_PORT})...")
            try:
                cls._pool = await asyncpg.create_pool(
                    host=settings.SUPABASE_DB_HOST,
                    port=settings.SUPABASE_DB_PORT,
                    database=settings.SUPABASE_DB_NAME,
                    user=settings.SUPABASE_DB_USER,
                    password=settings.SUPABASE_DB_PASSWORD,
                    ssl="require",
                    min_size=min_size,
                    max_size=max_size,
                    timeout=30.0,
                )
                logger.info("Supabase connection pool initialized successfully!")
            except Exception as e:
                logger.error(f"Failed to connect to Supabase: {e}")
                raise e

    @classmethod
    async def close(cls):
        """
        Close all active connection pool connections.
        """
        if cls._pool:
            logger.info("Closing Supabase asyncpg pool...")
            await cls._pool.close()
            cls._pool = None
            logger.info("Pool closed.")

    @classmethod
    def get_pool(cls) -> asyncpg.Pool:
        if cls._pool is None:
            raise RuntimeError("Database pool has not been initialized. Call DatabasePool.initialize() first.")
        return cls._pool

    @classmethod
    @asynccontextmanager
    async def acquire(cls):
        """
        Acquire a single connection from the pool with retry for transient network errors.
        """
        pool = cls.get_pool()
        max_retries = 5
        backoff = 1.0
        conn = None
        for attempt in range(1, max_retries + 1):
            try:
                conn = await pool.acquire()
                break
            except Exception as e:
                if attempt == max_retries:
                    logger.error(f"Failed to acquire DB connection after {max_retries} attempts: {e}")
                    raise
                logger.warning(f"Transient error acquiring DB connection (attempt {attempt}/{max_retries}): {e}. Retrying in {backoff}s...")
                await asyncio.sleep(backoff)
                backoff *= 2
        try:
            yield conn
        finally:
            if conn:
                await pool.release(conn)

    @classmethod
    @asynccontextmanager
    async def transaction(cls):
        """
        Acquire connection and start transaction context manager.
        """
        async with cls.acquire() as conn:
            async with conn.transaction():
                yield conn

