# SAP Utilities RAG Retrieval Engine V5.4 — Benchmark Report

## 1. Experiment Matrix Results

| Config | Description | R@5 | R@10 | R@20 | Doc R@10 | Chunk R@10 | MRR | NDCG@10 | Mean Lat (ms) | P95 Lat (ms) |
|---|---|---|---|---|---|---|---|---|---|---|
| `A_V5_3_G_Baseline` | V5.3 G Baseline (RRF 50/50 + Doc Evidence Agg | 0.8383 | 0.8750 | 0.8750 | 0.3200 | 0.0870 | 0.7624 | 0.0701 | 1304.2 | 2382.0 |
| `B_Adaptive_Depth_Only` | Adaptive Depth Only (Level 1: k=40, Level 2:  | 0.8383 | 0.8750 | 0.8750 | 0.3200 | 0.0870 | 0.7624 | 0.0701 | 597.8 | 1059.5 |
| `C_Adaptive_Depth_H1_Parent` | Adaptive Depth + H1 Parent Source Recovery (A | 0.8383 | 0.8750 | 0.8750 | 0.3200 | 0.0870 | 0.7590 | 0.0701 | 765.4 | 1238.0 |
| `D_Adaptive_Depth_H2_ParentSibling` | Adaptive Depth + H2 Parent + Sibling Recovery | 0.8383 | 0.8750 | 0.8750 | 0.3200 | 0.0870 | 0.7590 | 0.0701 | 793.2 | 1178.8 |
| `E_Conceptual_Entity_Recovery` | Adaptive Depth + Entity/Conceptual Intent Rec | 0.8383 | 0.8750 | 0.8750 | 0.3200 | 0.0870 | 0.7590 | 0.0701 | 838.9 | 1345.5 |
| `F_Best_Candidate_Recovery_V5_3_Rank` | Best Candidate Recovery (H1) + V5.3 Relevance | 0.8383 | 0.8750 | 0.8750 | 0.3200 | 0.0870 | 0.7590 | 0.0701 | 867.0 | 1280.0 |
| `G_Best_Candidate_Recovery_Small_Calibration` | V5.4 Final (Best Recovery H1 + Stability Marg | 0.8383 | 0.8750 | 0.8750 | 0.3200 | 0.0870 | 0.7640 | 0.0702 | 1016.6 | 2173.6 |

## 2. Production Target Evaluation Summary

- **Source Recall@5**: 0.8383 (Target $\ge 0.85$)
- **Source Recall@10**: 0.8750 (Target $\ge 0.92$)
- **Source Recall@20**: 0.8750 (Target $\ge 0.95$)
- **Document Recall@10**: 0.3200 (Target $\ge 0.92$)
- **MRR**: 0.7590 (Target $\ge 0.80$)
- **Mean Latency**: 765.4 ms (Target $< 500$ ms)
- **P95 Latency**: 1238.0 ms (Target $< 1000$ ms)
