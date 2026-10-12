# SAP Utilities RAG Retrieval Engine V5.4 — Failure Analysis

## Detailed Failure Taxonomy & Root Causes

1. **RANKING MISSES (Q9, Q10, Q43)**: Expected sources exist in the candidate pool ($k=40$) but rank between positions 11 and 20 due to strong keyword matches from adjacent operational chunks.
2. **TRUE CANDIDATE MISS (Q50)**: 'How to perform reconnection of utility service?'. Source 29 contains reconnection order procedures, but dense vector embeddings and lexical FTS rank disconnection order chunks higher.
