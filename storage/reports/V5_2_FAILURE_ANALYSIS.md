# SAP Utilities RAG Retrieval Engine V5.2 — Failure Analysis

## Root Cause Classification of Remaining Retrieval Weaknesses

1. **LEXICAL / DENSE INDEX COVERAGE**: Questions querying very generic procedures (e.g. general master data concepts) where relevant chunks lack specific distinct terminology.
2. **DOCUMENT AMBIGUITY**: Multiple SAP Utilities sources containing overlapping terminology for contract account roles and device extrapolation.
3. **CANDIDATE POOL LIMITS**: At candidate depth $k=60$, 3 queries require $k \ge 100$ to bring relevant long-tail chunks into the candidate set.
