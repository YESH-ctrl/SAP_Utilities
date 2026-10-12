# SAP Utilities RAG Retrieval Engine V5.2 — Query Regression Report

Compared against Canonical V3 Baseline (`A_Canonical_V3_RRF`).

- **Improved Queries**: 8
- **Unchanged Queries**: 37
- **Degraded Queries**: 5

### Improved Queries

| QID | Query | V3 MRR | V5.2 MRR | V3 R@10 | V5.2 R@10 |
|---|---|---|---|---|---|
| 2 | How does clearing control work for incoming payments? | 0.5000 | 1.0000 | 1.0000 | 1.0000 |
| 6 | What happens during move-out? | 0.5000 | 1.0000 | 1.0000 | 1.0000 |
| 9 | What are clearing types in SAP Utilities? | 0.0000 | 0.2000 | 0.0000 | 1.0000 |
| 25 | How does disconnection and reconnection of a utility installation work? | 0.1250 | 0.2500 | 1.0000 | 1.0000 |
| 31 | What is a budget billing scheme? | 0.3333 | 0.5000 | 1.0000 | 1.0000 |
| 42 | What is point of delivery POD? | 0.3333 | 0.5000 | 1.0000 | 1.0000 |
| 43 | How to create a budget billing plan manually? | 0.0000 | 0.1250 | 0.0000 | 0.5000 |
| 47 | What is plausible and implausible meter reading result? | 0.5000 | 1.0000 | 1.0000 | 1.0000 |

### Degraded Queries Breakdown

| QID | Query | V3 MRR | V5.2 MRR | V3 R@10 | V5.2 R@10 | V3 Top Sources | V5.2 Top Sources |
|---|---|---|---|---|---|---|---|
| 4 | How are meter readings estimated? | 1.0000 | 1.0000 | 1.0000 | 0.7500 | [7, 8, 7, 5, 5] | [7, 5, 5, 8, 7] |
| 5 | What happens during move-in? | 1.0000 | 1.0000 | 1.0000 | 0.6667 | [3, 13, 2, 23, 3] | [2, 3, 13, 23, 11] |
| 28 | How to handle move-in and move-out concurrently? | 0.2500 | 0.0000 | 1.0000 | 0.0000 | [19, 21, 21, 2, 13] | [22, 21, 22, 22, 20] |
| 37 | How to cancel an installment plan? | 0.1667 | 0.0000 | 0.5000 | 0.0000 | [2, 4, 11, 11, 11] | [2, 4, 11, 11, 11] |
| 41 | What is premise in SAP Utilities? | 0.1250 | 0.0000 | 1.0000 | 0.0000 | [16, 16, 13, 16, 13] | [16, 16, 13, 13, 13] |
