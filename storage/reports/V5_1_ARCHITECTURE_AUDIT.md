# V5.1 Architecture Audit & System Inspection Report

**Engine**: SAP Utilities RAG Retrieval Engine V5.1 Production Correction  
**Date**: October 7, 2026  
**Status**: Completed Architecture Audit  

---

## 1. Executive Audit Overview

The V5 retrieval system introduced major infrastructure improvements—including process-level model singleton initialization, LRU query embedding caching, 3-level IR evaluation metrics, and bounded selective recovery. However, the V5 master benchmark revealed critical gaps that prevented production certification:

1. **Benchmark Baseline Inconsistency**: V3 RRF baseline metrics differed between old reports and V5 evaluation scripts due to non-standardized dataset ground-truth formats and evaluation harnesses.
2. **Ranking Regression**: Secondary relevance scoring and reranking re-ordered top RRF candidate lists, dropping Source MRR from `0.7444` (V3 baseline) to `0.7082` (V5 final).
3. **End-to-End Latency**: While query embedding latency was reduced to `<0.1 ms` via LRU caching, total end-to-end latency averaged `627.4 ms` (P95 = `1070.4 ms`) due to public internet TLS network round-trips to Supabase PostgreSQL.

---

## 2. Root Cause Analysis

### A. Ground-Truth Model Inconsistency & Benchmark Flaw
In earlier versions, document-level ground truth was calculated by marking **every document within an expected source ID** as relevant. For SAP Utilities sources containing 20 to 80 documents, this artificially inflated the relevance denominator ($|\mathcal{D}_{\text{relevant}}| \approx 50$), capping Document Recall@10 at $\sim 0.2476$.
- **V5.1 Solution**: Audit all 50 benchmark queries to create a canonical, immutable ground-truth dataset (`retrieval_benchmark_v5_1.json`) with graded relevance (3 = direct answer, 2 = strong supporting context, 1 = related, 0 = irrelevant) and explicit document & chunk IDs.

### B. Why RRF Quality Regressed Under Heavy Second-Stage Scoring
Pure Candidate-Presence-Aware RRF ($k=60$) is extremely effective for technical SAP terms. Adding post-fusion additive feature scoring (domain/intent match, query coverage) displaced exact-match title and lexical candidates out of the top 5 slots when partial keyword matches accumulated high secondary scores.
- **V5.1 Solution**: Preserve RRF candidate order as the primary backbone. Apply lightweight title protection and technical-term floor ranking without altering the relative order of top RRF candidates.

### C. Latency Breakdown & Hot Path Profiling
Profiling identified the following component latencies across warm production requests:

| Component | V4 Latency | V5.0 Latency | V5.1 Optimization Strategy |
| :--- | :--- | :--- | :--- |
| **Query Processing** | ~10.0 ms | ~3.5 ms | Pre-compiled regex & SAP synonym dictionary |
| **Query Embedding** | 400–600 ms | **0.000 ms** (Cached) / ~45 ms (Warm CPU) | Singleton `EmbeddingModelService` + LRU `EmbeddingCache` |
| **Dense Vector DB Search** | ~250.0 ms | ~180.0 ms | Concurrent execution via `asyncio.gather()` + HNSW index |
| **Lexical FTS DB Search** | ~200.0 ms | ~160.0 ms | Concurrent execution via `asyncio.gather()` + GIN tsvector index |
| **RRF Fusion** | ~2.0 ms | ~1.5 ms | $k=60$ candidate-presence-aware vectorized RRF |
| **Relevance Scoring** | ~15.0 ms | ~4.0 ms | Vectorized NumPy feature scoring |
| **Second-Stage Reranker** | ~180.0 ms | **0.0 ms** (Skipped on Fast Path) | Invoked ONLY when retrieval confidence is MEDIUM/LOW |
| **Selective Recovery** | ~1200.0 ms | **0.0 ms** (Skipped on HIGH conf) | Hard budget `<=` 250 ms with concurrent fallback queries |

---

## 3. V5.1 Target Architecture

The default production pipeline for V5.1 adheres strictly to the Minimal Complexity Principle:

```
[User Query]
     │
     ▼
[Query Processor & SAP Normalization]
     │
     ▼
[Process-Level Singleton Embedding Service] ──► (LRU Query Cache)
     │
     ▼
[Concurrent PostgreSQL Search (asyncio.gather)]
┌───────────────────────────┴───────────────────────────┐
│                                                       │
▼                                                       ▼
[Dense HNSW Vector Search]               [Lexical FTS GIN Search]
│                                                       │
└───────────────────────────┬───────────────────────────┘
                            │
                            ▼
           [Candidate-Presence-Aware RRF (k=60)]
                            │
                            ▼
       [Lightweight Title / Tech-Term Floor Protection]
                            │
                            ▼
           [Calibrated Confidence & Answerability]
                            │
                            ▼
          [Adaptive Fast Path / Standard Path / Recovery]
```

1. **Fast Path (High Confidence)**: Pure RRF + Lightweight Floor Protection. Bypasses reranker & recovery entirely. Total execution time: `< 350 ms` (excluding network latency).
2. **Standard Path (Medium Confidence)**: RRF + Lightweight Reranker.
3. **Recovery Path (Low Confidence)**: Selective expanded search bounded by a hard `250 ms` timeout budget.

---

## 4. Verification Plan

1. Create and freeze `evaluation/datasets/retrieval_benchmark_v5_1.json` and `evaluation/datasets/retrieval_benchmark_v5_1.sha256`.
2. Re-run canonical V3 baseline against the frozen V5.1 benchmark.
3. Evaluate 7 A/B configurations.
4. Perform query-by-query regression analysis and audit failure taxonomy.
5. Verify corpus SHA-256 fingerprint match.
