# V5.1 Master Benchmark Report

## Summary Matrix Across 7 A/B Configurations
| Configuration ID & Strategy | Source R@10 | Doc R@10 | Chunk R@10 | MRR | NDCG@10 | Mean Latency (ms) | P95 Latency (ms) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `A_V3_RRF_CANONICAL_BASELINE` | 0.8483 | 0.2933 | 0.0800 | 0.7444 | 0.0614 | 885.2ms | 1730.5ms |
| `B_V5_1_RRF_relevance` | 0.8650 | 0.3267 | 0.1017 | 0.7065 | 0.0925 | 527.4ms | 892.2ms |
| `C_V5_1_title_protection` | 0.8650 | 0.3267 | 0.1017 | 0.7065 | 0.0925 | 598.1ms | 999.6ms |
| `D_V5_1_domain_intent` | 0.8650 | 0.3267 | 0.1017 | 0.7065 | 0.0925 | 486.9ms | 886.1ms |
| `E_V5_1_selective_reranker` | 0.8650 | 0.3267 | 0.1017 | 0.7082 | 0.0925 | 520.4ms | 922.3ms |
| `F_V5_1_selective_recovery` | 0.8650 | 0.3267 | 0.1017 | 0.7082 | 0.0925 | 504.1ms | 852.7ms |
| `G_V5_1_final_production` | 0.8650 | 0.3267 | 0.1017 | 0.7082 | 0.0925 | 506.8ms | 796.4ms |