# SAP Utilities RAG Retrieval Engine V5.2 — Architecture Audit

## Executive Summary
V5.2 addresses top-rank MRR regression caused by additive secondary metadata scoring in V5.1. By replacing unconstrained score addition with an **RRF Stability Margin** and **Top-1 Protection Floor**, V5.2 protects Rank 1 RRF retrievals while enabling generic SAP acronym expansion, document candidate diversification, and multi-threaded query execution.

## Architectural Changes & Principles

1. **Two-Stage Ranking Policy**:
   - Stage 1: Candidate-presence-aware Reciprocal Rank Fusion ($k=60$).
   - Stage 2: Secondary SAP feature scoring operates strictly within an RRF stability margin ($\Delta_{margin} = 0.0010$).

2. **Top-1 Protection Floor**:
   - Exact title, technical term, or SAP acronym matches at Rank 1 in pure RRF are locked with `is_protected = True` and a rank-preservation floor, preventing demotion by secondary keyword overlap.

3. **Candidate Depth & Diversification**:
   - Candidate pool increased from 40 to 60 per retriever channel.
   - Document diversification enforces `max_per_doc = 2` chunks per document in top-10 slots.

4. **Network & Connection Bottleneck Elimination**:
   - Connection pool reuse (`min_size=2, max_size=10`) with concurrent `asyncio.gather` for vector and FTS retrieval reduces database network round-trips to $\le 2$.

## Verification
- Corpus SHA-256: `f4f0bdc4e5a9a6b79a040de22ca91fcfe9a92c2b93a79faeaeb5dba40487caf6` (Verified)
- Benchmark SHA-256: `53ff3a94da1692a286bd66479543d5dc16114cd33a44c71d02125578749f0a26` (Verified)
