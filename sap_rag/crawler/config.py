import os
from typing import List
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    """
    Central application & crawler configuration loading from environment variables or .env file.
    """
    # Supabase PostgreSQL Database Credentials
    SUPABASE_DB_HOST: str = Field(default="db.zmruzdoeslwpccppejjk.supabase.co", alias="SUPABASE_DB_HOST")
    SUPABASE_DB_PORT: int = Field(default=5432, alias="SUPABASE_DB_PORT")
    SUPABASE_DB_NAME: str = Field(default="postgres", alias="SUPABASE_DB_NAME")
    SUPABASE_DB_USER: str = Field(default="postgres", alias="SUPABASE_DB_USER")
    SUPABASE_DB_PASSWORD: str = Field(default="RAG_Internship@11", alias="SUPABASE_DB_PASSWORD")

    # Crawler Settings
    CRAWL_SOURCE_CONCURRENCY: int = Field(default=5, alias="CRAWL_SOURCE_CONCURRENCY")
    CRAWL_PAGE_CONCURRENCY: int = Field(default=3, alias="CRAWL_PAGE_CONCURRENCY")
    CRAWL_REQUEST_DELAY_SECONDS: float = Field(default=1.0, alias="CRAWL_REQUEST_DELAY_SECONDS")
    CRAWLER_MAX_CONCURRENCY: int = Field(default=3, alias="CRAWLER_MAX_CONCURRENCY")
    CRAWLER_REQUEST_DELAY: float = Field(default=1.0, alias="CRAWLER_REQUEST_DELAY")
    CRAWLER_MAX_RETRIES: int = Field(default=3, alias="CRAWLER_MAX_RETRIES")
    CRAWLER_REQUEST_TIMEOUT: float = Field(default=30.0, alias="CRAWLER_REQUEST_TIMEOUT")
    CRAWLER_MAX_DEPTH: int = Field(default=10, alias="CRAWLER_MAX_DEPTH")
    CRAWLER_MAX_ROOT_TOC_NODES: int = Field(default=300, alias="CRAWLER_MAX_ROOT_TOC_NODES")
    CRAWLER_USER_AGENT: str = Field(default="Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)", alias="CRAWLER_USER_AGENT")

    # Domain Filtering
    ALLOWED_DOMAINS: List[str] = Field(default_factory=lambda: ["help.sap.com"])

    # Local Storage Directory Paths
    STORAGE_RAW_DIR: str = Field(default="storage/raw")
    STORAGE_CLEANED_DIR: str = Field(default="storage/cleaned")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    @property
    def connection_string(self) -> str:
        """
        Build asyncpg-compatible PostgreSQL DSN connection string.
        """
        return f"postgresql://{self.SUPABASE_DB_USER}:{self.SUPABASE_DB_PASSWORD}@{self.SUPABASE_DB_HOST}:{self.SUPABASE_DB_PORT}/{self.SUPABASE_DB_NAME}?ssl=require"

# Global settings instance
settings = Settings()
