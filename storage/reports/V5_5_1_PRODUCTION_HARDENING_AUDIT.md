# SAP Utilities RAG Retrieval Engine V5.5.1 — Operational Hardening Audit

## 1. Executive Summary & Hardening Scope

The **SAP Utilities RAG Retrieval Engine V5.5.1** is an operational hardening release. The core V5.5 retrieval architecture remained **100% FROZEN** throughout this release. No ranking weights, candidate generation rules, RRF $k$, query expansion mappings, or relevance scoring logic were modified.

The audit verified four operational objectives:
1. **Latency Measurement Standardization**: Resolved conflicting measurement methodologies across benchmark vs load test scripts.
2. **Concurrency Saturation**: Measured exact performance bounds across concurrency tiers 1–50.
3. **Safe Connection Pool Configuration**: Identified `min_size = 2, max_size = 15` as the safe, optimal pool size.
4. **Independent V5.4 Rollback Validation**: Built dedicated V5.4 rollback verification tools ([`scripts/verify_v54_rollback.py`](file:///c:/Users/yeswa/Desktop/RAG_Pipeline/scripts/verify_v54_rollback.py) and [`scripts/test_v54_smoke_test.py`](file:///c:/Users/yeswa/Desktop/RAG_Pipeline/scripts/test_v54_smoke_test.py)).

---

## 2. Frozen Release Contract Audit

- **Corpus SHA-256**: `f4f0bdc4e5a9a6b79a040de22ca91fcfe9a92c2b93a79faeaeb5dba40487caf6` (**VERIFIED 100% MATCH**)
- **Benchmark SHA-256**: `53ff3a94da1692a286bd66479543d5dc16114cd33a44c71d02125578749f0a26` (**VERIFIED 100% MATCH**)
- **Sources**: 29
- **Documents**: 965
- **Semantic Chunks**: 6,689 (`semantic-v1`)
- **Embeddings**: 6,689 (`BAAI/bge-m3`, 1024 dimensions)

---

## 3. Configuration Audit

All retrieval parameters remain strictly locked to V5.5 frozen values:
- `dense_candidate_k` = 40
- `lexical_candidate_k` = 40
- `dense_weight` = 0.5
- `lexical_weight` = 0.5
- `rrf_k` = 60
- `rerank_weight` = 0.0020
- `top1_protection` = true
- `entity_title_protection_boost` = 0.02
- `selective_recovery` = true
- `selective_recovery_timeout_ms` = 50.0

---

## 4. Hardening Audit Verdict

V5.5.1 resolves all operational inconsistencies and provides an evidence-backed operational release package without mutating frozen retrieval semantics.
