# SAP Utilities RAG Retrieval Engine V5.3 — Query Regression Report

Compared against Canonical V3 Baseline (`A_Canonical_V3`).

- **Improved Queries**: 8
- **Unchanged Queries**: 38
- **Degraded Queries**: 4

### Improved Queries

| QID | Query | V3 MRR | V5.3 MRR | V3 R@10 | V5.3 R@10 |
|---|---|---|---|---|---|
| 2 | How does clearing control work for incoming payments? | 0.5000 | 1.0000 | 1.0000 | 1.0000 |
| 6 | What happens during move-out? | 0.5000 | 1.0000 | 1.0000 | 1.0000 |
| 25 | How does disconnection and reconnection of a utility installation work? | 0.1250 | 0.2500 | 1.0000 | 1.0000 |
| 28 | How to handle move-in and move-out concurrently? | 0.2500 | 0.5000 | 1.0000 | 1.0000 |
| 31 | What is a budget billing scheme? | 0.3333 | 0.5000 | 1.0000 | 1.0000 |
| 32 | How are register groups assigned in device management? | 0.2500 | 1.0000 | 1.0000 | 1.0000 |
| 37 | How to cancel an installment plan? | 0.1667 | 0.5000 | 0.5000 | 0.5000 |
| 47 | What is plausible and implausible meter reading result? | 0.5000 | 1.0000 | 1.0000 | 1.0000 |

### Degraded Queries Breakdown

| QID | Query | V3 MRR | V5.3 MRR | V3 R@10 | V5.3 R@10 | V3 Top Sources | V5.3 Top Sources |
|---|---|---|---|---|---|---|---|
| 4 | How are meter readings estimated? | 1.0000 | 1.0000 | 1.0000 | 0.7500 | [7, 8, 7, 5, 5] | [7, 5, 8, 7, 5] |
| 41 | What is premise in SAP Utilities? | 0.1250 | 0.0000 | 1.0000 | 0.0000 | [16, 16, 13, 16, 13] | [16, 16, 13, 16, 13] |
| 42 | What is point of delivery POD? | 0.3333 | 0.2500 | 1.0000 | 1.0000 | [13, 13, 1, 13, 1] | [16, 16, 13, 1, 13] |
| 46 | How to handle meter exchange procedure? | 0.5000 | 0.3333 | 1.0000 | 1.0000 | [7, 5, 16, 5, 10] | [7, 13, 5, 10, 5] |
