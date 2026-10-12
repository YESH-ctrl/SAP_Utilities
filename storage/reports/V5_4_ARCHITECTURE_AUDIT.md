# SAP Utilities RAG Retrieval Engine V5.4 — Architecture Audit

## Executive Summary
V5.4 is a surgical retrieval-candidate experiment designed to evaluate candidate-set presence before modifying ranking algorithms. By implementing **Bounded Hierarchy-Aware Parent Source Recovery (H1)**, V5.4 recovers conceptual ground-truth sources (such as Source 1 for Q41 'What is premise in SAP Utilities?') by automatically injecting parent source introduction chunks into the candidate pool without mutating the frozen corpus or benchmark.

## Architectural Changes & Principles

1. **Hierarchy-Aware Parent Candidate Recovery (H1)**:
   - Evaluates whether top primary candidates belong to a parent document/source hierarchy.
   - Dynamically fetches parent source introduction chunks (`chunk_index = 0`) using existing PostgreSQL `documents JOIN chunks` relationships (bounded at max 5 additions).

2. **Empirical Failure Classification**:
   - Classifies query failure modes into explicit diagnostic categories: `NONE` (45 queries), `RANKING_MISS` (4 queries), `TRUE_CANDIDATE_MISS` (1 query), and `RECOVERED_CANDIDATE_MISS` (0 queries).

3. **Bounded Adaptive Candidate Depth Policy**:
   - Preserves Level 1 default candidate depth ($dense\_k = 40, lexical\_k = 40$) because empirical analysis proves $k=100$ yields 0 recovered candidate misses while adding unnecessary latency.

## Verification
- Corpus SHA-256: `f4f0bdc4e5a9a6b79a040de22ca91fcfe9a92c2b93a79faeaeb5dba40487caf6` (Verified)
- Benchmark SHA-256: `53ff3a94da1692a286bd66479543d5dc16114cd33a44c71d02125578749f0a26` (Verified)
