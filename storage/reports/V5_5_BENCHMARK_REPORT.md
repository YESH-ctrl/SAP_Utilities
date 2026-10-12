# SAP Utilities RAG Retrieval Engine V5.5 — Benchmark Report

## Summary Matrix Across Configurations A-F

| Config | Description | Source R@5 | Source R@10 | Source R@20 | Doc R@10 | Chunk R@10 | MRR | NDCG@10 | Mean Lat (ms) | P95 Lat (ms) |
|---|---|---|---|---|---|---|---|---|---|---|
| `A_V5_4_Baseline` | Authoritative V5.4 Baseline (RRF 50/50 + H1 P | 0.8683 | 0.9150 | 0.9150 | 0.3133 | 0.0940 | 0.8159 | 0.0762 | 860.0 | 1289.8 |
| `B_V5_5_Targeted_Reranker` | V5.5 Targeted Candidate-Pool Reranker | 0.8783 | 0.9250 | 0.9250 | 0.3133 | 0.0980 | 0.8159 | 0.0783 | 645.7 | 1049.0 |
| `C_V5_5_Semantic_Intent_Signals` | V5.5 Reranker + Conceptual/Procedural Intent  | 0.8783 | 0.9250 | 0.9250 | 0.3133 | 0.1030 | 0.8192 | 0.0806 | 625.9 | 1003.4 |
| `D_V5_5_Q50_Recovery` | V5.5 Q50 Semantic Recovery + FTS Expansion | 0.8783 | 0.9250 | 0.9250 | 0.3133 | 0.0980 | 0.8159 | 0.0783 | 638.1 | 1024.4 |
| `E_V5_5_Reranker_Q50_Recovery` | V5.5 Targeted Reranker + Q50 Recovery Combine | 0.8783 | 0.9250 | 0.9250 | 0.3133 | 0.1030 | 0.8192 | 0.0806 | 656.5 | 1067.7 |
| `F_V5_5_Best_Calibration` | V5.5 Final Best Calibration (Reranker + Inten | 0.8783 | 0.9250 | 0.9250 | 0.3133 | 0.1030 | 0.8192 | 0.0806 | 670.0 | 1074.3 |
