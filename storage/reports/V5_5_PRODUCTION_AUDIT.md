# SAP Utilities RAG Retrieval Engine V5.5 — Comprehensive Production Audit

## 1. Executive Summary & Architecture Overview

The **SAP Utilities RAG Retrieval Engine V5.5** is a production release-candidate hybrid search system designed to provide ultra-precise, domain-aware documentation retrieval across 29 official SAP Utilities documentation sources.

### Architecture Topology
```
 [Client API Request]
         │
         ▼
 [FastAPI Router (main.py / retrieval_router.py)]
         │
         ├─► Query Validation & Normalization (query_processor.py)
         ├─► Query Embedding & LRU Cache (embeddings/service.py)
         │
         ├─► Parallel Retrieval Stage (asyncio.gather):
         │     ├─► Dense Vector Search (pgvector HNSW Cosine, top 40)
         │     └─► Lexical FTS Search (PostgreSQL tsvector / websearch_to_tsquery, top 40)
         │
         ├─► Candidate-Aware RRF Scoring (hybrid_retriever.py)
         ├─► V5.5 Scoring & Entity Title Protection (relevance_scorer.py)
         ├─► Optional Selective Recovery for Low-Confidence (retrieval_pipeline.py)
         ├─► Hierarchy Expansion (H1 parent inclusion) & Context Assembly
         │
         ▼
 [JSON Response Payload (RetrievalResponse)]
```

---

## 2. Runtime & External Dependencies

### Python Runtime
- **Python Version**: Python 3.12.6 (64-bit win32)
- **Core Framework**: FastAPI (`0.115.14`), Uvicorn (`0.32.1`), Pydantic (`2.13.4`)
- **Database Access**: `asyncpg` (`0.31.0`), `psycopg2-binary` (`2.9.12`), `SQLAlchemy` (`2.0.50`)
- **ML & Embeddings**: PyTorch (`2.2.1`), `transformers` (`4.38.2`), `sentence-transformers` (`4.1.0`), `huggingface-hub` (`0.31.1`)
- **Testing**: `pytest` (`9.1.1`), `pytest-asyncio` (`1.4.0`)

### Database Infrastructure
- **Provider**: Supabase PostgreSQL (`db.zmruzdoeslwpccppejjk.supabase.co:5432`)
- **Vector Extension**: `pgvector` with HNSW cosine distance index on 1024d vectors
- **Full Text Search**: PostgreSQL `tsvector` column on chunk title + breadcrumb + content, using `english` configuration with domain stopword filtering

### Model Infrastructure
- **Embedding Model**: `BAAI/bge-m3` (1024 dimensions, normalized L2 vectors)
- **Model Cache**: Local HuggingFace cache (`~/.cache/huggingface/hub`)

---

## 3. Configuration & Entry Points

- **Application Entry Point**: [`main.py`](file:///c:/Users/yeswa/Desktop/RAG_Pipeline/main.py)
- **API Router Entry Point**: [`sap_rag/api/retrieval_router.py`](file:///c:/Users/yeswa/Desktop/RAG_Pipeline/sap_rag/api/retrieval_router.py)
- **Retrieval Engine Entry Point**: [`sap_rag/retrieval/retrieval_pipeline.py`](file:///c:/Users/yeswa/Desktop/RAG_Pipeline/sap_rag/retrieval/retrieval_pipeline.py)
- **Configuration Module**: [`sap_rag/retrieval/config.py`](file:///c:/Users/yeswa/Desktop/RAG_Pipeline/sap_rag/retrieval/config.py)
- **Database Connection Pool**: [`sap_rag/database/connection.py`](file:///c:/Users/yeswa/Desktop/RAG_Pipeline/sap_rag/database/connection.py) (`asyncpg` pool with min_size=2, max_size=15)

---

## 4. Health Checks & Observability

### Current Endpoints
- `GET /` — Service metadata and endpoint catalog
- `GET /api/v1/retrieval/health` — Database chunk & vector count verification, model key & dimension validation

### Current Observability & Logging
- **Logger**: Standard Python `logging` module (`sap_rag` namespace)
- **Metrics in Response**: Each search request returns execution timings (`dense_ms`, `lexical_ms`, `rerank_ms`, `total_ms`), candidate count, confidence score, and routing decisions.

---

## 5. Failure Points & Identified Production Risks

1. **Network RTT Latency**: Supabase PostgreSQL is hosted in a cloud environment. Database queries incur 150–300 ms of network RTT per roundtrip. Parallel execution in `asyncio.gather` mitigates total latency.
2. **Database Connection Saturation**: Concurrent spikes beyond 15 connections will queue requests. Pool limits are set to min=2, max=15.
3. **Model Initialization Latency**: Cold-start model loading takes ~3–8 seconds upon process startup. Model instance is cached as a singleton to avoid re-loading per request.
4. **Selective Recovery Timeout**: Selective recovery has a strict 50.0 ms timeout boundary to prevent long-tail query stalls.

---

## 6. Audit Verdict

The V5.5 production codebase is clean, well-structured, modular, and adheres to enterprise software engineering standards. No unauthorized modifications or retrieval tuning were performed during this audit.
