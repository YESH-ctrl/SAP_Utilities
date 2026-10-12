# SAP Utilities RAG Retrieval Engine V5.5 — Experiment Matrix

| Config ID | Description | Source R@10 | MRR | Degraded Count | P95 Latency |
|---|---|---|---|---|---|
| `A_V5_4_Baseline` | Authoritative V5.4 Baseline (RRF 50/50 + H1 Parent Recovery) | 0.9150 | 0.8159 | 0 | 1289.8 ms |
| `B_V5_5_Targeted_Reranker` | V5.5 Targeted Candidate-Pool Reranker | 0.9250 | 0.8159 | 0 | 1049.0 ms |
| `C_V5_5_Semantic_Intent_Signals` | V5.5 Reranker + Conceptual/Procedural Intent Alignment | 0.9250 | 0.8192 | 0 | 1003.4 ms |
| `D_V5_5_Q50_Recovery` | V5.5 Q50 Semantic Recovery + FTS Expansion | 0.9250 | 0.8159 | 0 | 1024.4 ms |
| `E_V5_5_Reranker_Q50_Recovery` | V5.5 Targeted Reranker + Q50 Recovery Combined | 0.9250 | 0.8192 | 0 | 1067.7 ms |
| `F_V5_5_Best_Calibration` | V5.5 Final Best Calibration (Reranker + Intent + Q50 Recovery) | 0.9250 | 0.8192 | 0 | 1074.3 ms |
