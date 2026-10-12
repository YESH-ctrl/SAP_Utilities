# SAP Utilities RAG Retrieval Engine V4 — Production Readiness Report

## Executive Summary
- **Corpus Integrity**: 29 Sources, 6,689 Semantic Chunks (`semantic-v1`), 6,689 Embeddings (`BAAI/bge-m3`, 1024 dims) **100% UNMUTATED & FROZEN**.
- **Evaluation Model**: 3-Level Evaluation (Source Level, Document Level, Chunk Level + NDCG).
- **Production Decision**: `PRODUCTION READY: NO`.

## A/B Configuration Metrics Across 3 Evaluation Levels
| Config ID & Strategy | Source R@5 | Source R@10 | Source R@20 | Doc R@10 | Chunk R@10 | MRR | NDCG@10 | Avg Latency | P95 Latency |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `1_V3_RRF_baseline` | 0.8017 | 0.8850 | 0.9400 | 0.2735 | 0.1040 | 0.7522 | 0.0940 | 0.3ms | 1.0ms |
| `2_V4_RRF_relevance_scoring` | 0.7583 | 0.8900 | 0.9300 | 0.3015 | 0.1587 | 0.7085 | 0.1582 | 17.5ms | 41.1ms |
| `3_V4_title_protection` | 0.7583 | 0.8900 | 0.9300 | 0.3015 | 0.1587 | 0.7085 | 0.1582 | 17.1ms | 40.1ms |
| `4_V4_domain_intent_scoring` | 0.7583 | 0.8900 | 0.9300 | 0.3015 | 0.1587 | 0.7085 | 0.1582 | 17.3ms | 41.2ms |
| `5_V4_protected_reranker` | 0.7783 | 0.8800 | 0.8800 | 0.3021 | 0.1517 | 0.7111 | 0.1505 | 34.1ms | 81.7ms |
| `6_V4_adaptive_recovery` | 0.8350 | 0.8900 | 0.8900 | 0.2632 | 0.1230 | 0.7169 | 0.1295 | 1033.8ms | 2587.0ms |
| `7_V4_final_production_pipeline` | 0.7750 | 0.8650 | 0.8650 | 0.2476 | 0.1183 | 0.7082 | 0.1306 | 638.9ms | 1143.3ms |

## Latency Breakdown
- **Average Latency**: `1581.06 ms` (Target: < 500 ms)
- **P50 Latency**: `1597.36 ms`
- **P95 Latency**: `2372.24 ms` (Target: < 1000 ms)
- **P99 Latency**: `2663.75 ms` (Target: < 1500 ms)

## PRODUCTION READY: NO