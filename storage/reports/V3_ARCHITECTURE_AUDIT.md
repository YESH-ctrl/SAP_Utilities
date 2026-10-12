# V3 Architecture Audit Report

**Date**: 2026-10-07  
**Engine Target**: SAP Utilities RAG Retrieval Engine V3 $\rightarrow$ V4 Production Hardening

---

## 1. Current Pipeline Architecture

The SAP Utilities Retrieval Engine V3 is organized into modular asynchronous components:

```
Query -> QueryProcessor -> DenseRetriever & LexicalRetriever -> HybridRetriever (RRF)
      -> MetadataScorer -> FastFeatureReranker -> HierarchyExpander -> MMRSelector -> ContextBuilder
```

### File & Component Breakdown
- **[`sap_rag/retrieval/retrieval_pipeline.py`](file:///c:/Users/yeswa/Desktop/RAG_Pipeline/sap_rag/retrieval/retrieval_pipeline.py)**: Master orchestrator.
- **[`sap_rag/retrieval/query_processor.py`](file:///c:/Users/yeswa/Desktop/RAG_Pipeline/sap_rag/retrieval/query_processor.py)**: Query normalization & term expansion.
- **[`sap_rag/retrieval/dense_retriever.py`](file:///c:/Users/yeswa/Desktop/RAG_Pipeline/sap_rag/retrieval/dense_retriever.py)**: pgvector HNSW cosine distance vector search (`BAAI/bge-m3`, 1024d).
- **[`sap_rag/retrieval/lexical_retriever.py`](file:///c:/Users/yeswa/Desktop/RAG_Pipeline/sap_rag/retrieval/lexical_retriever.py)**: PostgreSQL FTS (`tsvector`, `websearch_to_tsquery`, `plainto_tsquery` fallback).
- **[`sap_rag/retrieval/hybrid_retriever.py`](file:///c:/Users/yeswa/Desktop/RAG_Pipeline/sap_rag/retrieval/hybrid_retriever.py)**: Reciprocal Rank Fusion (RRF $k=60$) with candidate protection.
- **[`sap_rag/retrieval/metadata_scorer.py`](file:///c:/Users/yeswa/Desktop/RAG_Pipeline/sap_rag/retrieval/metadata_scorer.py)**: Title, breadcrumb, technical term, and document frequency confidence scoring.
- **[`sap_rag/retrieval/reranker.py`](file:///c:/Users/yeswa/Desktop/RAG_Pipeline/sap_rag/retrieval/reranker.py)**: `FastFeatureReranker` with protected candidate floor.
- **[`sap_rag/retrieval/hierarchy_expander.py`](file:///c:/Users/yeswa/Desktop/RAG_Pipeline/sap_rag/retrieval/hierarchy_expander.py)**: Neighbor chunk window expansion (`window=1`).
- **[`sap_rag/retrieval/mmr.py`](file:///c:/Users/yeswa/Desktop/RAG_Pipeline/sap_rag/retrieval/mmr.py)**: Maximal Marginal Relevance diversity selection ($lambda=0.75$).

---

## 2. Entry Points

- **API Layer**: [`sap_rag/api/retrieval_router.py`](file:///c:/Users/yeswa/Desktop/RAG_Pipeline/sap_rag/api/retrieval_router.py) (`POST /api/v1/retrieval/search`, `GET /api/v1/retrieval/health`).
- **Internal API**: `RetrievalPipeline.execute(conn, query, top_k=8)`.

---

## 3. Candidate Generation

- **Dense Channel**: Queries embedded via `EmbeddingModelService.encode_query()`. Vector search executed over Supabase PostgreSQL `embeddings` table (`1.0 - (e.embedding <=> query_vec)`). Top $k=40$.
- **Lexical Channel**: Executes PostgreSQL `tsvector` FTS over `chunks.fts` using `websearch_to_tsquery('english', query)`. Fallback to `plainto_tsquery` and keyword `OR` query if 0 rows returned. Top $k=40$.

---

## 4. Candidate Fusion

- Uses candidate-presence-aware Reciprocal Rank Fusion (RRF):
  $$\text{RRF Score} = \frac{w_{\text{dense}}}{k + \text{rank}_{\text{dense}}} + \frac{w_{\text{lexical}}}{k + \text{rank}_{\text{lexical}}}$$
  where $k=60$, $w_{\text{dense}}=0.30$, and $w_{\text{lexical}}=0.70$.
- Missing ranks do not incur negative penalties.
- Top lexical matches ($\text{lexical\_rank} \le 3$) receive exact match protection (`is_protected = True`).

---

## 5. Ranking & Reranking

- `MetadataScorer` adds title boost ($0.20$), breadcrumb boost ($0.20$), technical term boost ($0.10$), hierarchy boost ($0.05$), and document frequency confidence ($0.03 \times (\text{freq}-1)$).
- `FastFeatureReranker` scores query-document interaction (phrase boost, keyword overlap ratio, technical term match, title alignment) on top of `pre_rerank_score`. Protected candidates enforce `rerank_score >= pre_rerank_score`.

---

## 6. Confidence Calculation & Fallback

- Uncalibrated heuristic rules based on raw RRF score ($>0.012 \Rightarrow \text{HIGH}$, $>0.007 \Rightarrow \text{MEDIUM}$, else $\text{LOW}$).
- Fallback search triggers only on `LOW` confidence or $<3$ candidates.

---

## 7. Evaluation Methodology & Bottlenecks

### Current Issues in V3
1. **Source-Only Evaluation**: Evaluation benchmark (`evaluate_retrieval.py`) only checked `expected_source_ids`. Overlapping documentation across sources caused false mismatches.
2. **Adaptive Pipeline Regression**: `V3_final_adaptive_pipeline` regressed Recall@10 to $0.8483$ compared to `V3_RRF_fusion` baseline ($0.8850$).
3. **High Latency**: Adaptive pipeline average latency reached $\approx 786.9\text{ ms}$ (P95 $\approx 1381.1\text{ ms}$) due to unoptimized hierarchy expansion and secondary database queries.

---

## 8. Recommended V4 Production Architecture

1. **Establish `V3_RRF_fusion` as Primary Baseline** (Recall@5 = 0.8017, Recall@10 = 0.8850, Recall@20 = 0.9400, MRR = 0.7522).
2. **Implement 3-Level Evaluation Model**: Source Level, Document Level, Chunk Level + NDCG@5/10.
3. **Audit Benchmark Ground Truth**: Map questions to source IDs, expected document IDs, document titles, canonical URLs, and chunk IDs.
4. **Implement Transparent SAP Relevance Scorer**: Explicit normalized feature vector + feature contribution dictionary.
5. **Implement Calibrated Confidence & Answerability Evaluator**: Separate `ranking_score`, `relevance_score`, `confidence_score`, and `answerability_score` (`ANSWERABLE`, `PARTIALLY_ANSWERABLE`, `INSUFFICIENT_EVIDENCE`).
6. **Implement Document-Aware Diversification**: `same_document_limit = 3`, `same_section_limit = 2`.
7. **Latency Optimization**: Sub-500ms average latency via selective recovery and fast path candidate routing.
