# SAP Utilities RAG Retrieval Engine V5 — Production Readiness Report

## Executive Summary
- **Corpus Integrity**: 29 Sources, 6,689 Semantic Chunks (`semantic-v1`), 6,689 Embeddings (`BAAI/bge-m3`, 1024 dims) **100% UNMUTATED & FROZEN** (Fingerprint Match: `PASS`).
- **Evaluation Model**: Ground-Truth Multi-Level Evaluation (Source Level, Document Level, Chunk Level + NDCG).
- **Production Decision**: `PRODUCTION READY: NO`.

## A/B Configuration Metrics Across 3 Evaluation Levels
| Config ID & Strategy | Source R@5 | Source R@10 | Source R@20 | Doc R@10 | Chunk R@10 | MRR | NDCG@10 | Avg Latency | P95 Latency | Recovery Rate |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `A_V3_RRF_baseline` | 0.7967 | 0.8483 | 0.8483 | 0.2933 | 0.0800 | 0.7444 | 0.0614 | 840.7ms | 2038.2ms | 0.0% |
| `B_V5_RRF_relevance` | 0.7683 | 0.8650 | 0.8650 | 0.3267 | 0.1017 | 0.7065 | 0.0925 | 572.7ms | 1136.2ms | 0.0% |
| `C_V5_title_protection` | 0.7683 | 0.8650 | 0.8650 | 0.3267 | 0.1017 | 0.7065 | 0.0925 | 632.1ms | 1377.3ms | 0.0% |
| `D_V5_domain_intent` | 0.7683 | 0.8650 | 0.8650 | 0.3267 | 0.1017 | 0.7065 | 0.0925 | 533.9ms | 854.8ms | 0.0% |
| `E_V5_selective_reranker` | 0.7750 | 0.8650 | 0.8650 | 0.3267 | 0.1017 | 0.7082 | 0.0925 | 608.0ms | 1050.4ms | 0.0% |
| `F_V5_selective_recovery` | 0.7750 | 0.8650 | 0.8650 | 0.3267 | 0.1017 | 0.7082 | 0.0925 | 668.1ms | 1056.0ms | 0.0% |
| `G_V5_final_production` | 0.7750 | 0.8650 | 0.8650 | 0.3267 | 0.1017 | 0.7082 | 0.0925 | 627.4ms | 1070.4ms | 0.0% |

## Latency & Resource Breakdown
- **Average Latency**: `627.43 ms` (Target: < 500 ms)
- **P50 Latency**: `577.45 ms`
- **P95 Latency**: `1070.37 ms` (Target: < 1000 ms)
- **P99 Latency**: `1838.57 ms` (Target: < 1500 ms)
- **Query Embedding Hit Latency**: `0.000 ms` (LRU Hit Rate: `69.8%`)

## PRODUCTION READY: NO