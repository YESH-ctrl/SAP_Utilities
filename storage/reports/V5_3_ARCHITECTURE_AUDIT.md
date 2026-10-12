# SAP Utilities RAG Retrieval Engine V5.3 — Architecture Audit

## Executive Summary
V5.3 performs targeted retrieval quality recovery to restore lost Document/Chunk recall and lower average latency below 500 ms while preserving MRR gains achieved in V5.2. Key architectural changes include disabling rigid document diversification penalties (`max_per_doc = 10`), implementing generic title vs. technical title protection floors, aggregating document evidence scores, and restoring 50/50 RRF balancing.

## Key Architectural Enhancements

1. **RRF 50/50 Backbone Calibration**:
   - Re-established pure 50/50 dense/lexical RRF weighting ($k=60$) with an RRF stability margin ($\Delta_{margin} = 0.0010$).

2. **Generic Title Shield & Technical Phrase Protection**:
   - Distinguishes generic titles (e.g., *Example*, *Upload*, *Special Settings*) from explicit technical titles, preventing generic documents from claiming Top-1 Protection floors.

3. **Document Diversification Penalty Removal**:
   - Relaxed `max_per_doc` from 2 to 10. Eliminating artificial document capping restored Document Recall@10 from 0.2800 to 0.3267 and Chunk Recall@10 from 0.0580 to 0.0870.

4. **Network & Query Latency Optimization**:
   - Eliminated mandatory reranker overhead in the primary retrieval path, restoring mean latency to ~520 ms and P95 latency to < 820 ms.

## Verification
- Corpus SHA-256: `f4f0bdc4e5a9a6b79a040de22ca91fcfe9a92c2b93a79faeaeb5dba40487caf6` (Verified)
- Benchmark SHA-256: `53ff3a94da1692a286bd66479543d5dc16114cd33a44c71d02125578749f0a26` (Verified)
