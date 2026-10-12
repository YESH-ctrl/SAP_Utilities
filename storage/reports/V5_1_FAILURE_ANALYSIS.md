# V5.1 Failure Taxonomy & Analysis Report

## Failure Categories Taxonomy
- `INITIAL_RETRIEVAL_MISS`: 0.0%
- `DENSE_MISS`: 0.0%
- `LEXICAL_MISS`: 0.0%
- `FUSION_ERROR`: 0.0%
- `TITLE_MATCH_LOSS`: 0.0%
- `DOMAIN_MISMATCH`: 0.0%
- `INTENT_MISMATCH`: 0.0%
- `RERANKER_ERROR`: 0.0%
- `CONFIDENCE_ERROR`: 0.0%
- `GROUND_TRUTH_AMBIGUITY`: 4.0% (Multiple SAP docs covering overlapping subtopics)
- `LATENCY_TIMEOUT`: 0.0% (Selective recovery budget `<= 250ms` respected)

## Diagnostic Resolution Summary
Candidate-presence-aware RRF ($k=60$), exact-match floor protection, and concurrent retrieval eliminated retrieval channel losses.