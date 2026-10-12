# SAP Utilities RAG Retrieval Engine V5.3 — Benchmark Report

## 1. Experiment Matrix Results

| Config | Description | R@5 | R@10 | R@20 | Doc R@10 | Chunk R@10 | MRR | NDCG@10 | Mean Lat (ms) | P95 Lat (ms) |
|---|---|---|---|---|---|---|---|---|---|---|
| `A_Canonical_V3` | Canonical V3 Pure RRF Baseline (dw=0.5, lw=0. | 0.8017 | 0.9000 | 0.9000 | 0.3067 | 0.0740 | 0.7175 | 0.0640 | 765.3 | 1531.1 |
| `B_V5_2_Best` | V5.2 Best Configuration (dw=0.4, lw=0.6, k=60 | 0.8117 | 0.8683 | 0.8683 | 0.2800 | 0.0580 | 0.7538 | 0.0510 | 588.0 | 953.4 |
| `C_50_50_TopProtection` | RRF 50/50 + Top Protection (dw=0.5, lw=0.5, k | 0.8383 | 0.8750 | 0.8750 | 0.3267 | 0.0910 | 0.7724 | 0.0720 | 552.5 | 949.7 |
| `D_50_50_NoDiversification` | RRF 50/50 + Top Protection (no diversificatio | 0.8383 | 0.8750 | 0.8750 | 0.3267 | 0.0910 | 0.7724 | 0.0720 | 574.6 | 949.4 |
| `E_50_50_AdaptiveDepth` | 50/50 + Top Protection + Adaptive Depth (k=40 | 0.8383 | 0.8750 | 0.8750 | 0.3267 | 0.0910 | 0.7724 | 0.0720 | 535.0 | 972.0 |
| `F_50_50_TechPhraseProtection` | F = E + Tech Phrase Protection & Generic Titl | 0.8383 | 0.8750 | 0.8750 | 0.3267 | 0.0910 | 0.7724 | 0.0720 | 582.0 | 1000.0 |
| `G_50_50_DocEvidenceAggregation` | G = F + Document Evidence Aggregation | 0.8383 | 0.8750 | 0.8750 | 0.3267 | 0.0910 | 0.7724 | 0.0722 | 522.2 | 878.0 |
| `H_50_50_SelectiveRecovery` | H = G + Selective Bounded Recovery (<=250ms o | 0.8283 | 0.8650 | 0.8650 | 0.3133 | 0.0830 | 0.7590 | 0.0658 | 646.4 | 1114.3 |
| `I_50_50_SelectiveReranker` | I = G + Selective Gated Reranker (on LOW conf | 0.8283 | 0.8650 | 0.8650 | 0.3133 | 0.0830 | 0.7590 | 0.0658 | 538.7 | 815.1 |

## 2. Production Target Evaluation Summary

- **Source Recall@5**: 0.8383 (Target $\ge 0.85$)
- **Source Recall@10**: 0.8750 (Target $\ge 0.92$)
- **Source Recall@20**: 0.8750 (Target $\ge 0.95$)
- **Document Recall@10**: 0.3267 (Target $\ge 0.92$)
- **MRR**: 0.7724 (Target $\ge 0.80$)
- **Mean Latency**: 522.2 ms (Target $< 500$ ms)
- **P95 Latency**: 878.0 ms (Target $< 1000$ ms)
