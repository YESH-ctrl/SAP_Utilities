-- =============================================================================
-- SAP UTILITIES RAG PIPELINE - DATABASE SCHEMA MIGRATION
-- Migration: 001_initial_schema.sql
-- Target Database: PostgreSQL 17+ with pgvector & pgcrypto
-- Purpose: Enterprise-grade database schema supporting SAP Help Portal crawling,
--          parent-child documentation hierarchy traversal, semantic sectioning,
--          chunking, vector embeddings (BGE-M3), hybrid retrieval & RAG chat.
-- Idempotent script: Safe to run multiple times without data destruction.
-- =============================================================================

BEGIN;

-- -----------------------------------------------------------------------------
-- 0. EXTENSIONS
-- -----------------------------------------------------------------------------
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- -----------------------------------------------------------------------------
-- HELPER TRIGGER FUNCTION FOR UPDATED_AT TIMESTAMP REFRESH
-- -----------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- -----------------------------------------------------------------------------
-- 1. SOURCES TABLE
-- Represents the original seed reference PDFs (e.g. 29 SAP Utilities PDFs).
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS sources (
    id BIGSERIAL PRIMARY KEY,
    source_file VARCHAR(255) NOT NULL UNIQUE,
    title VARCHAR(255) NOT NULL,
    category VARCHAR(100) NOT NULL,
    seed_url TEXT NOT NULL,
    product VARCHAR(100) NOT NULL DEFAULT 'SAP S/4HANA On-Premise',
    version VARCHAR(50) NOT NULL DEFAULT 'On-Premise',
    source_type VARCHAR(50) NOT NULL DEFAULT 'reference_pdf',
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE sources IS 'Reference index PDFs serving as seed URLs for SAP Help Portal crawling.';
COMMENT ON COLUMN sources.source_file IS 'Filename of the reference PDF (e.g. 01_Utilities_Master_Data.pdf).';
COMMENT ON COLUMN sources.seed_url IS 'Initial SAP Help Portal seed URL extracted from the reference PDF.';

-- -----------------------------------------------------------------------------
-- 2. DOCUMENTS TABLE
-- Primary hierarchy store for SAP documentation pages discovered by crawler.
-- Preserves parent-child tree structure via self-referential parent_id & depth.
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS documents (
    id BIGSERIAL PRIMARY KEY,
    source_id BIGINT REFERENCES sources(id) ON DELETE SET NULL,
    parent_id BIGINT REFERENCES documents(id) ON DELETE CASCADE,
    root_document_id BIGINT REFERENCES documents(id) ON DELETE SET NULL,
    title TEXT NOT NULL,
    url TEXT NOT NULL,
    canonical_url TEXT UNIQUE NOT NULL,
    source_pdf VARCHAR(255),
    depth INT NOT NULL CHECK (depth >= 0),
    document_type VARCHAR(50) NOT NULL CHECK (document_type IN ('root', 'section', 'article', 'reference')),
    content TEXT,
    content_hash CHAR(64),
    status VARCHAR(50) NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'crawled', 'failed', 'processing', 'processed', 'archived')),
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_crawled_at TIMESTAMPTZ,
    
    -- Enforce strict root vs non-root parent-depth hierarchy invariant
    CONSTRAINT chk_documents_hierarchy CHECK (
        (parent_id IS NULL AND depth = 0) OR 
        (parent_id IS NOT NULL AND depth > 0)
    )
);

COMMENT ON TABLE documents IS 'SAP Documentation tree representation with parent-child relationships.';
COMMENT ON COLUMN documents.parent_id IS 'Self-referential key linking child document to its parent node in the documentation hierarchy.';
COMMENT ON COLUMN documents.depth IS 'Depth level in documentation tree (Root=0, Level 1 Section=1, Sub-article=2+).';

-- -----------------------------------------------------------------------------
-- 3. DOCUMENT LINKS TABLE
-- Tracks all hyperlinked relations (TOC, internal navigation, related links, etc.)
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS document_links (
    id BIGSERIAL PRIMARY KEY,
    source_document_id BIGINT NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    target_document_id BIGINT REFERENCES documents(id) ON DELETE SET NULL,
    target_url TEXT NOT NULL,
    link_text TEXT,
    link_type VARCHAR(50) NOT NULL DEFAULT 'child' CHECK (link_type IN ('toc', 'child', 'related', 'reference', 'next', 'previous', 'external')),
    is_internal BOOLEAN NOT NULL DEFAULT TRUE,
    is_crawled BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT uq_document_links_source_target UNIQUE (source_document_id, target_url)
);

COMMENT ON TABLE document_links IS 'Hyperlinks discovered during crawling for link graph & hierarchy discovery.';

-- -----------------------------------------------------------------------------
-- 4. CRAWL JOBS TABLE
-- Controls stateful, restartable crawler queue and work scheduling.
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS crawl_jobs (
    id BIGSERIAL PRIMARY KEY,
    source_id BIGINT REFERENCES sources(id) ON DELETE CASCADE,
    document_id BIGINT REFERENCES documents(id) ON DELETE SET NULL,
    url TEXT NOT NULL,
    parent_document_id BIGINT REFERENCES documents(id) ON DELETE SET NULL,
    depth INT NOT NULL DEFAULT 0 CHECK (depth >= 0),
    status VARCHAR(50) NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'queued', 'crawling', 'success', 'failed', 'skipped')),
    priority INT NOT NULL DEFAULT 10,
    attempts INT NOT NULL DEFAULT 0 CHECK (attempts >= 0),
    max_attempts INT NOT NULL DEFAULT 3 CHECK (max_attempts >= 1),
    last_error TEXT,
    scheduled_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE crawl_jobs IS 'Stateful crawler tasks supporting idempotent execution and auto-resume.';

-- -----------------------------------------------------------------------------
-- 5. CRAWL ERRORS TABLE
-- Granular log store for HTTP errors, timeout issues, and parsing failures.
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS crawl_errors (
    id BIGSERIAL PRIMARY KEY,
    crawl_job_id BIGINT REFERENCES crawl_jobs(id) ON DELETE CASCADE,
    url TEXT NOT NULL,
    error_type VARCHAR(100) NOT NULL,
    error_message TEXT NOT NULL,
    http_status INT,
    attempt_number INT NOT NULL DEFAULT 1 CHECK (attempt_number >= 1),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE crawl_errors IS 'Crawler error history log for debugging without altering crawl job state.';

-- -----------------------------------------------------------------------------
-- 6. DOCUMENT SECTIONS TABLE
-- Preserves page semantic layout (Heading 1, 2, Prerequisites, Procedure, etc.).
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS document_sections (
    id BIGSERIAL PRIMARY KEY,
    document_id BIGINT NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    parent_section_id BIGINT REFERENCES document_sections(id) ON DELETE CASCADE,
    heading TEXT NOT NULL,
    content TEXT,
    section_order INT NOT NULL DEFAULT 0 CHECK (section_order >= 0),
    level INT NOT NULL DEFAULT 1 CHECK (level >= 1),
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE document_sections IS 'Semantic structure of individual SAP documentation pages prior to chunking.';

-- -----------------------------------------------------------------------------
-- 7. CHUNKS TABLE
-- Semantic text passages ready for embedding vector generation and FTS.
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS chunks (
    id BIGSERIAL PRIMARY KEY,
    document_id BIGINT NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    section_id BIGINT REFERENCES document_sections(id) ON DELETE SET NULL,
    chunk_index INT NOT NULL CHECK (chunk_index >= 0),
    content TEXT NOT NULL,
    token_count INT NOT NULL CHECK (token_count >= 0),
    content_hash CHAR(64) NOT NULL,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    fts tsvector GENERATED ALWAYS AS (to_tsvector('english', coalesce(content, ''))) STORED,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE chunks IS 'Granular text units for hybrid search (Full-Text Search + Dense Vector Search).';

-- -----------------------------------------------------------------------------
-- 8. EMBEDDINGS TABLE
-- High-dimensional vector storage using pgvector (BGE-M3 default, 1024 dims).
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS embeddings (
    id BIGSERIAL PRIMARY KEY,
    chunk_id BIGINT NOT NULL REFERENCES chunks(id) ON DELETE CASCADE,
    embedding vector(1024),
    model VARCHAR(100) NOT NULL DEFAULT 'BGE-M3',
    dimension INT NOT NULL DEFAULT 1024 CHECK (dimension > 0),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT uq_embeddings_chunk_model UNIQUE (chunk_id, model)
);

COMMENT ON TABLE embeddings IS 'Dense vector embeddings for chunks (pgvector).';

-- -----------------------------------------------------------------------------
-- 9. CONVERSATIONS TABLE
-- Chatbot user sessions store.
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id VARCHAR(255) NOT NULL,
    title TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE conversations IS 'Chatbot user interaction sessions.';

-- -----------------------------------------------------------------------------
-- 10. MESSAGES TABLE
-- Individual conversational turns between user, assistant, and system prompt.
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    role VARCHAR(50) NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
    content TEXT NOT NULL,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE messages IS 'Individual user and assistant messages in chat sessions.';

-- =============================================================================
-- INDEXES FOR PERFORMANCE OPTIMIZATION
-- =============================================================================

-- Documents Table Indexes
CREATE INDEX IF NOT EXISTS idx_documents_source_id ON documents(source_id);
CREATE INDEX IF NOT EXISTS idx_documents_parent_id ON documents(parent_id);
CREATE INDEX IF NOT EXISTS idx_documents_depth ON documents(depth);
CREATE INDEX IF NOT EXISTS idx_documents_document_type ON documents(document_type);
CREATE INDEX IF NOT EXISTS idx_documents_url ON documents(url);
CREATE INDEX IF NOT EXISTS idx_documents_canonical_url ON documents(canonical_url);
CREATE INDEX IF NOT EXISTS idx_documents_status ON documents(status);

-- Document Links Table Indexes
CREATE INDEX IF NOT EXISTS idx_document_links_source_document_id ON document_links(source_document_id);
CREATE INDEX IF NOT EXISTS idx_document_links_target_url ON document_links(target_url);
CREATE INDEX IF NOT EXISTS idx_document_links_is_crawled ON document_links(is_crawled);

-- Crawl Jobs Table Indexes & Unique Constraints
CREATE INDEX IF NOT EXISTS idx_crawl_jobs_status ON crawl_jobs(status);
CREATE INDEX IF NOT EXISTS idx_crawl_jobs_depth ON crawl_jobs(depth);
CREATE INDEX IF NOT EXISTS idx_crawl_jobs_priority ON crawl_jobs(priority);
CREATE INDEX IF NOT EXISTS idx_crawl_jobs_url ON crawl_jobs(url);
CREATE INDEX IF NOT EXISTS idx_crawl_jobs_source_id ON crawl_jobs(source_id);

-- Deduplication index preventing concurrent active crawl jobs for identical URL
CREATE UNIQUE INDEX IF NOT EXISTS idx_crawl_jobs_url_active 
ON crawl_jobs (url) 
WHERE status IN ('pending', 'queued', 'crawling');

-- Crawl Errors Table Indexes
CREATE INDEX IF NOT EXISTS idx_crawl_errors_job_id ON crawl_errors(crawl_job_id);

-- Document Sections Table Indexes
CREATE INDEX IF NOT EXISTS idx_document_sections_document_id ON document_sections(document_id);
CREATE INDEX IF NOT EXISTS idx_document_sections_parent_section_id ON document_sections(parent_section_id);

-- Chunks Table Indexes (Including GIN Full-Text Search Index)
CREATE INDEX IF NOT EXISTS idx_chunks_document_id ON chunks(document_id);
CREATE INDEX IF NOT EXISTS idx_chunks_section_id ON chunks(section_id);
CREATE INDEX IF NOT EXISTS idx_chunks_content_hash ON chunks(content_hash);
CREATE INDEX IF NOT EXISTS idx_chunks_fts ON chunks USING gin(fts);

-- Embeddings Table Indexes (Including HNSW Vector Cosine Index)
CREATE INDEX IF NOT EXISTS idx_embeddings_chunk_id ON embeddings(chunk_id);
CREATE INDEX IF NOT EXISTS idx_embeddings_model ON embeddings(model);

-- HNSW Vector Index for Cosine Distance Search
CREATE INDEX IF NOT EXISTS idx_embeddings_vector_hnsw 
ON embeddings USING hnsw (embedding vector_cosine_ops);

-- Messages Table Indexes
CREATE INDEX IF NOT EXISTS idx_messages_conversation_id ON messages(conversation_id);

-- =============================================================================
-- ATTACH UPDATED_AT TRIGGERS
-- =============================================================================
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'trg_sources_updated_at') THEN
        CREATE TRIGGER trg_sources_updated_at BEFORE UPDATE ON sources FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'trg_documents_updated_at') THEN
        CREATE TRIGGER trg_documents_updated_at BEFORE UPDATE ON documents FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'trg_crawl_jobs_updated_at') THEN
        CREATE TRIGGER trg_crawl_jobs_updated_at BEFORE UPDATE ON crawl_jobs FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'trg_document_sections_updated_at') THEN
        CREATE TRIGGER trg_document_sections_updated_at BEFORE UPDATE ON document_sections FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'trg_chunks_updated_at') THEN
        CREATE TRIGGER trg_chunks_updated_at BEFORE UPDATE ON chunks FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'trg_embeddings_updated_at') THEN
        CREATE TRIGGER trg_embeddings_updated_at BEFORE UPDATE ON embeddings FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'trg_conversations_updated_at') THEN
        CREATE TRIGGER trg_conversations_updated_at BEFORE UPDATE ON conversations FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
    END IF;
END $$;

COMMIT;
