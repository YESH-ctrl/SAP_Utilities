# V5 Architecture Audit Report

**Date**: 2026-10-07  
**Engine Target**: SAP Utilities RAG Retrieval Engine V5 Production Optimization

---

## 1. Audit Findings & Root Cause Analysis

### A. Why V4 Final Loses Recall@10 vs V3 RRF (0.8650 vs 0.8850)
- In V4, post-fusion additive metadata scoring (`MetadataScorer`) re-sorted the pure RRF candidate ranking. Non-exact candidate chunks that scored high on domain/intent keywords displaced top RRF lexical/dense candidates out of the top 10 window.
- **Fix in V5**: Preserve `V3_RRF_fusion` candidate ordering as the primary baseline ranker. Apply lightweight relevance scoring without displacing top RRF matches.

### B. Why MRR Decreased (0.7082 vs 0.7522)
- Second-stage reranking (`FastFeatureReranker`) and metadata boosts altered top-1 candidate ordering. Keyword interaction features in secondary documents occasionally pushed the primary exact-match chunk from Rank 1 to Rank 2 or 3.
- **Fix in V5**: Make second-stage reranking strictly optional and selective. Use lightweight title/technical term protection floors that preserve Rank 1 exact matches.

### C. Why Adaptive Recovery Introduced Multi-Second Latency (up to 2,587 ms)
- In V4, recovery executed serial fallback database searches (`await lexical_retriever.search(use_expanded=True)`), leading to redundant SQL roundtrips.
- **Fix in V5**: Implement a strict recovery latency budget (`recovery_budget_ms <= 250`), trigger recovery ONLY on concrete evidence of retrieval failure, and execute fallback queries concurrently via `asyncio.gather()`.

### D. Why Query Embedding Consumes ~400–600 ms
- `EmbeddingModelService.encode_query()` performed CPU tokenization and PyTorch forward passes on every request without a process-level query embedding cache.
- **Fix in V5**: Implement a process-level singleton embedding service combined with a bounded LRU query embedding cache (`EmbeddingCache`) with TTL.

### E. Why Document-Level Evaluation Produced Artificially Low Recall (0.2476)
- The V4 ground-truth audit mapped expected source IDs to ALL documents contained within those sources ($\approx 20\text{--}80$ documents per query). This created an inflated denominator for Document Recall.
- **Fix in V5**: Implement a structured multi-level evaluation schema with explicit relevance targets (Graded relevance: 3 = Direct Answer, 2 = Strong Support, 1 = Related, 0 = Irrelevant).

---

## 2. V5 Target Architecture

```
                                      [ User Query ]
                                            │
                                            ▼
                              ┌───────────────────────────┐
                              │     Query Processor       │
                              │ (Normalize, Expand, Terms)│
                              └─────────────┬─────────────┘
                                            │
                                            ▼
                              ┌───────────────────────────┐
                              │   Query Embedding Cache   │
                              │   (Process-Level LRU)     │
                              └─────────────┬─────────────┘
                                            │
                     ┌──────────────────────┴──────────────────────┐
                     ▼ (Concurrent asyncio.gather)                 ▼
         ┌───────────────────────┐                     ┌───────────────────────┐
         │   Dense Retriever     │                     │   Lexical Retriever   │
         │ (pgvector HNSW Cosine)│                     │ (FTS + Fallback Miss) │
         └───────────┬───────────┘                     └───────────┬───────────┘
                     │                                             │
                     └──────────────────────┬──────────────────────┘
                                            ▼
                              ┌───────────────────────────┐
                              │  Candidate-Presence-Aware │
                              │    V3 RRF Fusion Engine   │
                              └─────────────┬─────────────┘
                                            │
                                            ▼
                              ┌───────────────────────────┐
                              │ Lightweight Relevance &   │
                              │   Title Protection Floor  │
                              └─────────────┬─────────────┘
                                            │
                     ┌──────────────────────┴──────────────────────┐
                     ▼ (HIGH Confidence)                           ▼ (LOW Confidence)
         ┌───────────────────────┐                     ┌───────────────────────┐
         │      FAST PATH        │                     │   Selective Recovery  │
         │ (Doc Diversification) │                     │ (Hard Budget <=250ms) │
         │  ~30–120ms Latency    │                     │  Concurrent Fallback  │
         └───────────┬───────────┘                     └───────────┬───────────┘
                     │                                             │
                     └──────────────────────┬──────────────────────┘
                                            ▼
                              ┌───────────────────────────┐
                              │ Calibrated Confidence &   │
                              │ Answerability Evaluator   │
                              └───────────────────────────┘
```
