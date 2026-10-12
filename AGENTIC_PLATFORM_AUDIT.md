# AUDIT AND ARCHITECTURAL ISOLATION SPECIFICATION
## Independent CrewAI Agentic Knowledge Intelligence Platform for SAP Utilities

**Date:** 2026-10-10  
**Status:** Approved & Verified against Live Database and Codebase

---

## 1. Executive Summary & Architectural Invariant

The goal of this platform is to build an independent agentic knowledge-intelligence system for SAP Utilities documentation on top of existing stored database assets, while completely isolating retrieval, orchestration, evidence validation, and answer generation from the legacy RAG pipeline.

### The Absolute Architectural Decision
* **Reuse Existing Persisted Data:** The platform reuses existing PostgreSQL/Supabase records (`sources`, `documents`, `document_sections`, `document_links`, `chunks`, `embeddings`) through a strict read-only query boundary.
* **Never Mutate or Re-embed Persisted Data:** No existing chunks, vectors, or metadata are modified or regenerated.
* **Zero Legacy Code in Execution Path:** The new platform never calls, imports, or falls back to the legacy retriever, lexical/FTS search, old RRF fusion, heuristic boosts, legacy reranker, old recovery logic, or legacy chat/answer generator.
* **Offline Benchmark Only:** The legacy pipeline remains untouched and functional solely for offline comparative benchmarking. If the new agentic workflow encounters an unrecoverable failure, it returns a structured, transparent error or partial result—never a legacy fallback answer.

---

## 2. Live Database Schema & Data Asset Verification

Verified directly via live inspection against PostgreSQL 17 / Supabase instance:

### 2.1 Table Inventory & Record Counts
| Table Name | Row Count | Primary Purpose in New Platform |
| :--- | :--- | :--- |
| `sources` | 29 | Reference index metadata for the 29 seed SAP Utilities PDFs |
| `documents` | 965 | Documentation tree hierarchy (`parent_id`, `depth`, `title`, `url`, `canonical_url`) |
| `document_sections` | 5,051 | Page semantic section layout (`parent_section_id`, `heading`, `section_order`, `level`) |
| `document_links` | 585,085 | Hyperlink graph edges (`source_document_id`, `target_document_id`, `target_url`, `link_type`) |
| `chunks` | 6,689 | Granular text passages (`document_id`, `section_id`, `content`, `token_count`, `metadata`) |
| `embeddings` | 6,689 | Dense 1024-dim vectors (`chunk_id`, `model`, `dimension`, `embedding`) |
| `conversations` | 0 | Legacy session store (not used by new platform) |
| `messages` | 0 | Legacy message store (not used by new platform) |

### 2.2 Vector Storage & Metric Verification
* **Model Key:** `BGE-M3` (BAAI/bge-m3)
* **Stored Vector Dimension:** `1,024` dimensions (confirmed via PostgreSQL `vector_dims(embedding) = 1024`)
* **Vector Normalization:** Stored vectors are L2-normalized upon encoding (`normalize_embeddings=True`).
* **Distance Metric:** Cosine distance.
* **PostgreSQL Index:** `idx_embeddings_vector_hnsw ON public.embeddings USING hnsw (embedding vector_cosine_ops)`.
* **Cosine Operator:** `<=>` where `cosine_distance = (embedding <=> query_vec)` and `cosine_similarity = 1.0 - distance`.

---

## 3. Explicit Forbidden-Dependency List (Legacy Execution Path)

Under no circumstances may the new production agentic platform import, instantiate, or invoke any of the following legacy components:

```
[FORBIDDEN LEGACY DEPENDENCIES]
❌ sap_rag.retrieval.retrieval_pipeline.RetrievalPipeline (Legacy orchestrator)
❌ sap_rag.retrieval.dense_retriever.DenseRetriever       (Legacy dense search)
❌ sap_rag.retrieval.lexical_retriever.LexicalRetriever   (Legacy PostgreSQL tsvector/FTS search)
❌ sap_rag.retrieval.hybrid_retriever.HybridRetriever     (Legacy RRF fusion)
❌ sap_rag.retrieval.relevance_scorer.SAPRelevanceScorer (Legacy heuristic boosts)
❌ sap_rag.retrieval.metadata_scorer.MetadataScorer       (Legacy title/breadcrumb boosts)
❌ sap_rag.retrieval.reranker.RetrievalReranker           (Legacy cross-encoder / feature reranker)
❌ sap_rag.retrieval.hierarchy_expander.HierarchyExpander (Legacy recovery expander)
❌ sap_rag.retrieval.mmr.MMRSelector                      (Legacy MMR selection)
❌ sap_rag.retrieval.context_builder.ContextBuilder       (Legacy context string builder)
❌ sap_rag.chat.service.ChatService                       (Legacy chat orchestrator)
❌ sap_rag.chat.service.ConversationStore                 (Legacy session store)
❌ sap_rag.llm.service.LLMService                         (Legacy LLM wrapper)
❌ sap_rag.llm.gemini_service.GeminiService               (Legacy Gemini prompt & generation path)
❌ sap_rag.api.chat_router.router                         (Legacy /api/v1/chat endpoint)
❌ sap_rag.api.retrieval_router.router                    (Legacy /api/v1/retrieval endpoints)
```

---

## 4. End-to-End System Architecture Diagram

```
                             [ CLIENT APPLICATIONS ]
           ┌──────────────────────────────────────────────┐
           │  React Frontend (/agentic)  |  Streamlit UI  │
           └───────────────────────┬──────────────────────┘
                                   │ HTTP POST (Typed Contracts)
                                   ▼
             [ ISOLATED FASTAPI ROUTER: /api/v2/agentic ]
                                   │
                                   ▼
             [ CREWAI FLOW: AgenticIntelligenceFlow ]
   ┌──────────────────────────────────────────────────────────────┐
   │                                                              │
   │  [STAGE 1: PLAN]                                             │
   │  Query Planner Agent ──► Typed QueryPlan                     │
   │                                                              │
   │  [STAGE 2: DISCOVER]                                         │
   │  Semantic Discovery Worker                                   │
   │    │                                                         │
   │    ▼ [Deterministic Tools]                                   │
   │    SemanticRetrievalService (Parameterized direct pgvector)  │
   │    EvidenceContextBuilder (Safe request-time excerpts)       │
   │                                                              │
   │  [STAGE 3: REASON & EXPAND]                                  │
   │  - Procedure Analyst (Core)                                  │
   │  - Configuration Analyst (Conditional)                       │
   │  - Relationship Analyst (Stored link graph traversal)        │
   │  - Troubleshooting Analyst (Conditional)                     │
   │                                                              │
   │  [STAGE 4: RECONCILE & AUDIT]                                │
   │  Deterministic EvidenceLedger ◄── Deduplication & Provenance │
   │  Evidence Auditor Agent ──► Challenges claims & detects gaps │
   │                                                              │
   │  [STAGE 5: SYNTHESIZE & VALIDATE]                            │
   │  Answer Synthesizer Agent ──► Single coherent synthesis     │
   │  Deterministic CitationValidator (Strict provenance checks)  │
   │  AnswerCoverageValidator (Checks subquestion coverage)       │
   │                                                              │
   └──────────────────────────────┬───────────────────────────────┘
                                  │
                                  ▼
                     [ READ-ONLY DATABASE BOUNDARY ]
           ┌──────────────────────────────────────────────┐
           │ PostgreSQL 17 + pgvector (Supabase)          │
           │ Tables: chunks, embeddings, documents,       │
           │         document_sections, document_links    │
           └──────────────────────────────────────────────┘
```

---

## 5. Architectural Components & Phased Implementation Plan

### Phase 1: Independent Semantic Retrieval Service (`sap_rag/agentic/retrieval/`)
1. **`IndependentQueryEncoder`**: Dedicated BGE-M3 query vector encoder with normalization matching stored 1024-d vectors.
2. **`SemanticRetrievalService`**: Parameterized direct pgvector queries over existing embeddings. Cosine distance (`<=>`), metadata filters, and diagnostic metrics.
3. **`GraphTraversalService`**: Controlled BFS/DFS over `document_links` and `documents.parent_id` with bounded depth (max 2), candidate limits, and cycle detection.
4. **`EvidenceContextBuilder`**: Stable chunk ID preservation, character/token offset extraction, safe context excerpting without DB mutation.

### Phase 2: CrewAI Flow & Specialist Roles (`sap_rag/agentic/orchestration/`)
1. **Flow Controller**: `AgenticIntelligenceFlow` orchestrating typed state transitions.
2. **Core 5-Role Vertical Slice**:
   - `Query Planner`: Deconstructs query into intent, subquestions, entity constraints.
   - `Semantic Discovery Worker`: Uses narrow retrieval tools to acquire grounded hits.
   - `Procedure Analyst`: Extracts prerequisites, sequential steps, verification actions.
   - `Evidence Auditor`: Verifies citation coverage, checks contradictions, flags ungrounded assertions.
   - `Answer Synthesizer`: Produces one cohesive, non-concatenated synthesis.
3. **Conditional Specialists**:
   - `Configuration Analyst`: Parameters, tables, maintenance views.
   - `Relationship Analyst`: Multi-hop link expansion across related business objects.
   - `Troubleshooting Analyst`: Error codes, diagnostic procedures, workarounds.

### Phase 3: Typed Output Contracts (`sap_rag/agentic/schemas/`)
Strict Pydantic v2 schemas:
- `QueryPlan`
- `EvidenceItem` / `RetrievalHit`
- `AgentFinding`
- `ClaimRecord`
- `ValidationReport`
- `FinalAgenticResponse`

### Phase 4: Deterministic Evidence Ledger & Bounded Loop (`sap_rag/agentic/ledger/`)
- `EvidenceLedger`: In-memory aggregator preventing multi-agent citation inflation.
- Provenance tracking, contradiction registry, coverage matrix.
- Bounded iterative gap retrieval (max 2 investigation rounds).

### Phase 5: Deterministic Citation & Coverage Validation (`sap_rag/agentic/validators/`)
- `CitationValidator`: Ensures every citation points to an actual retrieved chunk with matching URL/title and substring verification.
- `AnswerCoverageValidator`: Cross-references final response against initial subquestions.
- Bounded single repair attempt if hallucination or invalid citation is detected.

### Phase 6: Isolated API & Frontend Layer (`sap_rag/agentic/api/` & `frontend/`)
- Backend: `/api/v2/agentic/chat`, `/api/v2/agentic/search`, `/api/v2/agentic/health`.
- Frontend: New dedicated route `/agentic` in React UI with rich visualization of reasoning stages, evidence drawer, citation inspection, and conflict reporting.

### Phase 7: Security & Reliability (`sap_rag/agentic/security/`)
- Read-only parameterized DB operations.
- Prompt injection defense (treating retrieved content as untrusted data).
- Execution budget controller (timeouts, concurrency limit, cost tracking).

### Phase 8: Offline Benchmark Harness (`evaluation/agentic_benchmark/`)
- Three-way comparison on frozen benchmark:
  1. Legacy RAG Baseline (offline evaluation only)
  2. Direct Semantic Retrieval (no agents)
  3. Full CrewAI Agentic Platform
- Evaluation of precision, recall, citation validity, hallucination rate, latency, and token cost.
