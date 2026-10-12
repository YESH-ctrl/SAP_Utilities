# SAP Utilities Agentic Knowledge Intelligence Platform — Production Runbook

## 1. System Overview & Core Invariants

The **SAP Utilities Agentic Knowledge Intelligence Platform** provides an independent, multi-agent, grounded intelligence tier built natively on top of existing stored SAP Help Portal documentation assets (6,689 chunks and embeddings in PostgreSQL/Supabase with `pgvector`).

### Absolute Architectural Invariants
1. **Reuse Persisted Data Read-Only:** Queries the existing PostgreSQL tables (`chunks`, `embeddings`, `documents`, `document_sections`, `document_links`) using direct, parameterized `pgvector` nearest-neighbor SQL (`<=>` cosine distance over 1,024-dimensional BGE-M3 embeddings).
2. **Never Call the Legacy Execution Path:** The new platform operates via its own dedicated retrieval and orchestration pipeline. It **never** imports, calls, or relies on legacy `sap_rag.retrieval.retrieval_pipeline`, `lexical_retriever`, `hybrid_retriever`, legacy `reranker`, `sap_rag.chat`, or `sap_rag.llm`.
3. **No Legacy Fallback:** If an agentic stage times out, encounters capacity limits, or detects insufficient documentation, it returns a transparent partial answer or explicit abstention. It **never** falls back to legacy RAG answers.
4. **Deterministic Evidence & Zero Citation Hallucination:** Citations (`[1]`, `[2]`) are validated deterministically by `CitationValidator` against actual retrieved chunk IDs and source URLs before an answer is finalized.

---

## 2. Platform Architecture

```
                          ┌─────────────────────────────────────┐
                          │    User Request / UI (/agentic)     │
                          └──────────────────┬──────────────────┘
                                             │ POST /api/v2/agentic/chat
                                             ▼
                          ┌─────────────────────────────────────┐
                          │    ExecutionBudgetController        │
                          │   (90s deadline, timeouts, cancel)   │
                          └──────────────────┬──────────────────┘
                                             ▼
                          ┌─────────────────────────────────────┐
                          │        Query Planner (Agent)        │
                          │  (intent, subquestions, constraints) │
                          └──────────────────┬──────────────────┘
                                             ▼
                          ┌─────────────────────────────────────┐
                          │    Semantic Discovery Worker        │
                          │        (Tools & Services)           │
                          └──────────┬───────────────────────┬──┘
                                     │                       │
         ┌───────────────────────────┴───────┐   ┌───────────┴───────────────────────┐
         │     SemanticRetrievalService      │   │       GraphTraversalService       │
         │ (pgvector direct <=> cosine 1024d)│   │ (BFS parent/child & doc_links)    │
         └───────────────────┬───────────────┘   └───────────┬───────────────────────┘
                             └───────────────┬───────────────┘
                                             ▼
                          ┌─────────────────────────────────────┐
                          │        EvidenceContextBuilder       │
                          │ (stable chunk IDs, safe excerpts)   │
                          └──────────────────┬──────────────────┘
                                             ▼
                          ┌─────────────────────────────────────┐
                          │       EvidenceLedger / Matrix       │
                          │(deduplication, anti-inflation, claim)│
                          └──────────────────┬──────────────────┘
                                             │
             ┌───────────────────────────────┼───────────────────────────────┐
             │ (Procedural)                  │ (Configuration)               │ (Troubleshooting / Rel)
             ▼                               ▼                               ▼
  ┌───────────────────────┐       ┌───────────────────────┐       ┌───────────────────────┐
  │   Procedure Analyst   │       │ Configuration Analyst │       │ Troubleshooting/Rel   │
  │ (prereqs, steps, code)│       │ (tables, spro paths)  │       │ (exceptions, links)   │
  └──────────┬────────────┘       └──────────┬────────────┘       └──────────┬────────────┘
             └───────────────────────────────┼───────────────────────────────┘
                                             ▼
                          ┌─────────────────────────────────────┐
                          │        Evidence Auditor (Agent)     │
                          │  (claim challenge, contradictions)  │
                          └──────────────────┬──────────────────┘
                                             ▼
                          ┌─────────────────────────────────────┐
                          │      Answer Synthesizer (Agent)     │
                          │   (single unified grounded answer)   │
                          └──────────────────┬──────────────────┘
                                             ▼
                          ┌─────────────────────────────────────┐
                          │   Deterministic Citation Validator  │
                          │ (verifies [N] in retrieved evidence)│
                          └──────────────────┬──────────────────┘
                                             ▼
                          ┌─────────────────────────────────────┐
                          │   FinalAgenticResponse (JSON API)   │
                          └─────────────────────────────────────┘
```

---

## 3. Specialist Roles & Responsibilities

The agentic platform implements an **MVP-first core vertical slice of 5 core roles**, complemented by **3 conditionally routed specialist roles**:

| Specialist Role | Execution Mode | Responsibilities |
| :--- | :--- | :--- |
| **Query Planner** | Core (Always) | Categorizes intent (`procedural`, `configuration`, `troubleshooting`, `factual`), decomposes complex queries into bounded subquestions (`SQ-1`, `SQ-2`), extracts SAP entities and constraints. |
| **Semantic Discovery Worker** | Core (Always) | Executes direct parameterized pgvector queries via narrow typed tool `search_sap_documentation`. |
| **Procedure Analyst** | Core Slice | Turns retrieved passages into chronological steps, prerequisites, transaction codes, and expected system outcomes. |
| **Evidence Auditor** | Core (Always) | Challenges unbacked claims, detects contradictions, checks coverage against original plan, flags unanswered subquestions. |
| **Answer Synthesizer** | Core (Always) | Formulates one cohesive, readable answer with inline bracketed citations (`[1]`, `[2]`). Does not concatenate agent reports. |
| **Configuration Analyst** | Conditional Router | Triggered for configuration intents; extracts customizing paths, tables, customizing objects, and dependencies. |
| **Relationship Analyst** | Conditional Router | Triggered for multi-hop relationship queries; traverses stored `document_links` and parent hierarchy. |
| **Troubleshooting Analyst** | Conditional Router | Triggered for diagnostic inquiries; analyzes error messages, root causes, and corrective actions. |

---

## 4. API Specification & Endpoints

All agentic platform endpoints are isolated under the `/api/v2/agentic/` namespace.

### 1. `POST /api/v2/agentic/chat`
Full end-to-end multi-agent execution pipeline.

**Request Body:**
```json
{
  "query": "What is the procedure to reverse a contract in SAP Utilities integration?",
  "max_investigation_rounds": 2,
  "allow_graph_expansion": true,
  "timeout_seconds": 90.0,
  "min_similarity": 0.30
}
```

**Response Contract (`FinalAgenticResponse`):**
```json
{
  "request_id": "REQ-0d3a492f",
  "original_query": "What is the procedure to reverse a contract in SAP Utilities integration?",
  "answer": "To reverse a contract in SAP Utilities, proceed as follows...",
  "citations": [
    {
      "citation_id": 1,
      "evidence_id": "EV-SQ-MAIN-1",
      "chunk_id": 7193,
      "document_id": 2691,
      "title": "Reverse Contract Integration",
      "canonical_url": "https://help.sap.com/docs/...",
      "excerpt": "Contract reversal requires...",
      "cosine_distance": 0.28,
      "similarity_score": 0.72
    }
  ],
  "evidence_payload": [...],
  "agent_stage_summary": [
    {"stage_name": "Query Planning", "status": "completed", "latency_ms": 3200.0, "details": "Planned 1 subquestions"},
    {"stage_name": "Semantic Discovery", "status": "completed", "latency_ms": 450.0, "details": "Retrieved 5 chunks"},
    {"stage_name": "Procedure Analyst", "status": "completed", "latency_ms": 4800.0, "details": "Extracted sequential steps"},
    {"stage_name": "Evidence Audit", "status": "completed", "latency_ms": 2800.0, "details": "100% evidence supported"},
    {"stage_name": "Answer Synthesis", "status": "completed", "latency_ms": 4100.0, "details": "Synthesized with 5 citations"},
    {"stage_name": "Citation Validation", "status": "completed", "latency_ms": 1.2, "details": "100% citations verified"}
  ],
  "validation_report": {
    "citation_integrity": true,
    "claim_support": true,
    "question_coverage": true,
    "overall_status": "verified",
    "unanswered_subquestions": []
  },
  "execution_status": "completed"
}
```

### 2. `POST /api/v2/agentic/search`
Direct pgvector retrieval bypass without running agentic reasoning.
- **Parameters:** `query` (str), `top_k` (int, default: 10), `min_similarity` (float, default: 0.30)
- **Returns:** `List[EvidenceItem]`

### 3. `GET /api/v2/agentic/health`
Health telemetry verifying database vector count, embedding dimensions, and read-only connection pool.
- **Returns:**
```json
{
  "status": "healthy",
  "version": "v2.0-agentic",
  "database": {
    "chunks": 6689,
    "vectors": 6689,
    "distance_metric": "cosine (<=>)"
  },
  "encoder": {
    "model": "BAAI/bge-m3",
    "dimension": 1024,
    "normalized": true
  }
}
```

---

## 5. Operations & Execution Guide

### 5.1 Environment Configuration (`.env`)
Ensure the following variables are defined in `.env`:
```bash
# Database (Read-only connection to Supabase PostgreSQL)
SUPABASE_DB_HOST=db.zmruzdoeslwpccppejjk.supabase.co
SUPABASE_DB_PORT=5432
SUPABASE_DB_NAME=postgres
SUPABASE_DB_USER=postgres
SUPABASE_DB_PASSWORD=...

# Gemini LLM Provider (Gemini 3.8 Flash active model)
GEMINI_API_KEY=...
GOOGLE_API_KEY=...
AGENTIC_MODEL=gemini-3.8-flash
AGENTIC_LLM_TEMP=0.1
AGENTIC_LLM_MAX_TOKENS=3000
```

### 5.2 Starting the Backend Server
```bash
C:\Python312\python.exe -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### 5.3 Starting the Frontend Development Server
```bash
cd frontend
npm run dev
```
Navigate to `http://localhost:5173/agentic` to access the **Agentic Intelligence Platform UI**.

### 5.4 Running Automated Verification Tests
Run the complete unit, boundary, and regression test suites:
```bash
# Agentic platform isolation & boundary tests (12 tests)
C:\Python312\python.exe -m pytest tests/test_agentic_platform.py -v

# Legacy regression test suites (16 tests)
C:\Python312\python.exe -m pytest tests/test_retrieval.py tests/test_chat_api.py -v

# Full workspace test suite (28 tests total)
C:\Python312\python.exe -m pytest -v
```

### 5.5 Running the Offline Benchmark Harness
Compare Legacy RAG vs Direct Semantic vs CrewAI Agentic Platform:
```bash
C:\Python312\python.exe -u evaluation/agentic_benchmark/benchmark_runner.py
```
Outputs:
- `evaluation/agentic_benchmark/benchmark_results.json`
- `AGENTIC_PLATFORM_BENCHMARK_REPORT.md`

---

## 6. Security & Invariant Enforcement

1. **Strict Import Boundary Enforcement (`test_01_forbidden_dependencies_boundary`):**
   An automated AST / file token scanner confirms that zero files inside `sap_rag/agentic/` reference legacy modules.
2. **Immutable Stored Corpus:**
   Chunk texts and embeddings are never updated or mutated at query time. Long chunks exceeding LLM context budgets are safely excerpted in-memory by `EvidenceContextBuilder` (`is_excerpted=True`, `char_offset_start`, `char_offset_end`) while preserving the permanent `chunk_id`.
3. **Prompt Injection Sanitization (`SecurityGuardrails`):**
   Untrusted retrieved document texts are sanitized against instruction override patterns (`"ignore previous instructions"`, system prompt extraction, jailbreaks) before injection into LLM prompts.
4. **Secret Redaction:**
   High-entropy API keys, database credentials, and Bearer tokens are redacted prior to payload transmission.
5. **Request-Scoped State Isolation (`test_10_concurrent_requests_state_isolation`):**
   Each request instantiates a unique `EvidenceLedger` and `ExecutionBudgetController`. Memory is strictly garbage-collected per request.

---

## 7. Known Limitations & Roadmap

- **Model Latency:** Multi-agent reasoning (Query Planner + Specialists + Auditor + Synthesizer) involves multiple LLM turns. P50 latency is ~25-35 seconds compared to single-turn retrieval (~2-4 seconds).
- **Rate Limits:** In high-concurrency environments, multi-turn agent calls require Gemini Tier-1 API rate quota headroom.
- **Future Enhancements:**
  - Streaming token responses via Server-Sent Events (`/api/v2/agentic/chat/stream`).
  - Graph edge weighting based on hyperlink co-occurrence frequency.
