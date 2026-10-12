# SAP Utilities RAG Retrieval Engine V5.2 — Benchmark Report

## 1. Experiment Matrix Results

| Config | Description | R@5 | R@10 | R@20 | Doc R@10 | Chunk R@10 | MRR | NDCG@10 | Mean Lat (ms) | P95 Lat (ms) |
|---|---|---|---|---|---|---|---|---|---|---|
| `A_Canonical_V3_RRF` | Canonical V3 Pure RRF (dense_w=0.5, lex_w=0.5 | 0.8017 | 0.9000 | 0.9000 | 0.3067 | 0.0740 | 0.7175 | 0.0640 | 588.6 | 919.6 |
| `B_V5_1_Current_Prod` | V5.1 Current Production (dense_w=0.4, lex_w=0 | 0.7850 | 0.8650 | 0.8650 | 0.3267 | 0.1017 | 0.7099 | 0.0925 | 532.9 | 866.1 |
| `C_RRF_30_70_TopProt` | RRF 30/70 + Top Protection (dense_w=0.3, lex_ | 0.7967 | 0.8583 | 0.8583 | 0.2933 | 0.0710 | 0.7439 | 0.0567 | 521.6 | 815.2 |
| `D_RRF_40_60_TopProt` | RRF 40/60 + Top Protection (dense_w=0.4, lex_ | 0.8017 | 0.8483 | 0.8483 | 0.2933 | 0.0710 | 0.7569 | 0.0568 | 673.4 | 1040.0 |
| `E_RRF_50_50_TopProt` | RRF 50/50 + Top Protection (dense_w=0.5, lex_ | 0.8383 | 0.8750 | 0.8750 | 0.3267 | 0.0870 | 0.7724 | 0.0696 | 528.7 | 815.4 |
| `F_Best_RRF_Depth60` | Best RRF (40/60) + Candidate Depth 60 | 0.8117 | 0.8583 | 0.8583 | 0.2867 | 0.0670 | 0.7509 | 0.0565 | 673.6 | 1118.2 |
| `G_Best_RRF_QueryNorm` | Best RRF + Generic SAP Normalization (40/60,  | 0.8117 | 0.8583 | 0.8583 | 0.2867 | 0.0670 | 0.7509 | 0.0567 | 697.5 | 1201.2 |
| `H_Best_RRF_DocDiversification` | Best RRF + Document Diversification (max_per_ | 0.8117 | 0.8683 | 0.8683 | 0.2800 | 0.0580 | 0.7538 | 0.0510 | 686.6 | 1281.5 |
| `I_Best_RRF_SelectiveReranker` | Best RRF + Selective Reranker | 0.8117 | 0.8683 | 0.8683 | 0.2800 | 0.0580 | 0.7538 | 0.0510 | 1889.0 | 4081.3 |
| `J_Best_Overall_V5_2` | V5.2 Best Overall Configuration (RRF 40/60 +  | 0.8117 | 0.8683 | 0.8683 | 0.2800 | 0.0580 | 0.7538 | 0.0510 | 681.0 | 1508.1 |

## 2. Gate Verification Summary

- **Source Recall@5**: 0.8117 (Target $\ge 0.85$)
- **Source Recall@10**: 0.8683 (Target $\ge 0.92$)
- **Source Recall@20**: 0.8683 (Target $\ge 0.95$)
- **Document Recall@10**: 0.2800 (Target $\ge 0.92$)
- **MRR**: 0.7538 (Target $\ge 0.80$)
- **Mean Latency**: 681.0 ms (Target $< 500$ ms)
- **P95 Latency**: 1508.1 ms (Target $< 1000$ ms)
