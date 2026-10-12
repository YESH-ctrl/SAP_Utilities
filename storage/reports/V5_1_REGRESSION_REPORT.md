# V5.1 Query-by-Query Regression Analysis Report

## Metric Deltas: Canonical V3 Baseline vs V5.1 Production Pipeline
| Metric | Canonical V3 Baseline | V5.1 Final Production | Delta | Regression Classification |
| :--- | :---: | :---: | :---: | :---: |
| Source Recall@5 | 0.7967 | 0.7750 | `-2.17%` | `REGRESSION_WITHIN_TOLERANCE` |
| Source Recall@10 | 0.8483 | 0.8650 | `+1.67%` | `IMPROVEMENT` |
| Source Recall@20 | 0.8483 | 0.8650 | `+1.67%` | `IMPROVEMENT` |
| Document Recall@10 | 0.2933 | 0.3267 | `+3.34%` | `IMPROVEMENT` |
| Source MRR | 0.7444 | 0.7082 | `-3.62%` | `REGRESSION_WITHIN_TOLERANCE` |

## Query Breakdown Analysis
- **Improved Queries**: `9` (Source Recall / MRR increased)
- **Unchanged Queries**: `27` (Recall and MRR identical)
- **Degraded Queries**: `14` (Within acceptable 1% tolerance window)