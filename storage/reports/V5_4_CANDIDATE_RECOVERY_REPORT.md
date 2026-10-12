# SAP Utilities RAG Retrieval Engine V5.4 — Candidate Recovery Report

## 1. Failure Mode Taxonomy Summary

- **Total Queries**: 50
- **Top-10 Ground Truth Hits (`NONE`)**: 45 (90.0%)
- **Ranking Misses (GT in pool, ranked > 10)**: 4 (8.0%)
- **Recovered Candidate Misses ($k=100$)**: 0 (0.0%)
- **True Candidate Misses ($k > 100$)**: 1 (2.0%)

## 2. Answers to Mandatory V5.4 Candidate Questions

1. **How many V5.3 misses were true candidate-generation failures?**: Exactly 1 query (Q50).
2. **How many were ranking failures?**: Exactly 4 queries (Q9, Q10, Q41, Q43).
3. **How many relevant sources were recovered by $k=60$?**: 0 additional sources.
4. **How many were recovered only by $k=100$?**: 0 additional sources.
5. **What percentage of queries required expansion?**: 0% for $k=100$, 100% for H1 hierarchy recovery.
6. **Did hierarchy recovery solve Q41?**: Yes, H1 parent source recovery fetched Source 1 for Q41!
