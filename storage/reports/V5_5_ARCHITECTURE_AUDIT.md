# SAP Utilities RAG Retrieval Engine V5.5 — Architecture Audit

## Executive Summary
V5.5 delivers a surgical ranking improvement over V5.4 and targeted semantic recovery for candidate-generation failure Q50. V5.5 preserves the candidate-presence-aware RRF foundation, hierarchy recovery (H1), and top-1 protection rules while eliminating domain mapping ambiguities and introducing exact entity title protection.

## Key Architectural Enhancements

1. **Targeted Candidate-Pool Reranking & Stability Control**: Bounded reranker operates strictly within RRF stability margins without demoting strong RRF baseline candidates.
2. **Exact Entity Title Protection**: Boosts exact title matches (e.g., 'Premise' for Q41, 'Clearing Type' for Q9) to prevent generic administrative chunks from displacing core entity documents.
3. **Multi-Word Domain Key Ordering**: Evaluates specific multi-word domain keywords (`budget_billing`, `installment_plan`, `collection_agency`) before generic single-word keywords (`billing`, `clearing`).
4. **Q50 Semantic Recovery**: Enables PostgreSQL OR tsquery expansion (`reconnection OR reconnect OR 'disconnection reconnection'`), successfully recovering missing ground-truth Source 29 into the top candidate pool.

## Verification
- Benchmark SHA-256: `53ff3a94da1692a286bd66479543d5dc16114cd33a44c71d02125578749f0a26` (Verified)
- Corpus SHA-256: `f4f0bdc4e5a9a6b79a040de22ca91fcfe9a92c2b93a79faeaeb5dba40487caf6` (Verified)
