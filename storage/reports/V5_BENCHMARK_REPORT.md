# V5 Master Benchmark Report

## Summary Matrix
| Strategy | Source Recall@10 | Doc Recall@10 | Chunk Recall@10 | MRR | NDCG@10 | Mean Latency (ms) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| `A_V3_RRF_baseline` | 0.8483 | 0.2933 | 0.0800 | 0.7444 | 0.0614 | 840.7 |
| `B_V5_RRF_relevance` | 0.8650 | 0.3267 | 0.1017 | 0.7065 | 0.0925 | 572.7 |
| `C_V5_title_protection` | 0.8650 | 0.3267 | 0.1017 | 0.7065 | 0.0925 | 632.1 |
| `D_V5_domain_intent` | 0.8650 | 0.3267 | 0.1017 | 0.7065 | 0.0925 | 533.9 |
| `E_V5_selective_reranker` | 0.8650 | 0.3267 | 0.1017 | 0.7082 | 0.0925 | 608.0 |
| `F_V5_selective_recovery` | 0.8650 | 0.3267 | 0.1017 | 0.7082 | 0.0925 | 668.1 |
| `G_V5_final_production` | 0.8650 | 0.3267 | 0.1017 | 0.7082 | 0.0925 | 627.4 |