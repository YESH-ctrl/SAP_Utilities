import pytest
from sap_rag.crawler.config import settings

def test_database_config_settings():
    assert settings.SUPABASE_DB_HOST == "db.zmruzdoeslwpccppejjk.supabase.co"
    assert settings.SUPABASE_DB_PORT == 5432
    assert settings.SUPABASE_DB_NAME == "postgres"
    assert settings.SUPABASE_DB_USER == "postgres"
    assert "ssl=require" in settings.connection_string

def test_crawl_job_repository_imports():
    from sap_rag.database.repositories.crawl_job_repository import CrawlJobRepository
    from sap_rag.database.repositories.document_repository import DocumentRepository
    assert hasattr(CrawlJobRepository, "reclaim_stale_crawling_jobs")
    assert hasattr(CrawlJobRepository, "mark_failed_or_retry")
    assert hasattr(DocumentRepository, "upsert_document")

