# SAP Utilities RAG Retrieval Engine V5.5 — Production Rollback Plan

## 1. Executive Summary

This document specifies the step-by-step emergency rollback procedure for reverting from **V5.5 Release Candidate** to **V5.4 Stable Baseline** in the event of an unforeseen production incident.

---

## 2. Release Identifiers & Backward Compatibility

- **Target Release Identifier**: `V5.5-RC` (SHA-256 Corpus: `f4f0bdc4e5a9a6b79a040de22ca91fcfe9a92c2b93a79faeaeb5dba40487caf6`)
- **Rollback Target Release**: `V5.4-STABLE`
- **Database Schema Compatibility**: **100% Fully Compatible**. V5.5 uses the exact same PostgreSQL schema, chunks, and pgvector embeddings as V5.4. No schema migrations were performed for V5.5.
- **Corpus Rebuild Requirement**: **ZERO corpus rebuild required**. The corpus remains completely frozen and untouched.

---

## 3. Emergency Rollback Procedure

```
 [Production Defect Detected]
         │
         ▼
 [1. Trigger Incident Alert & Drain Traffic]
         │
         ▼
 [2. Revert Application Binaries / Git Checkout]
         │
         ▼
 [3. Restart Web Server (Uvicorn/FastAPI)]
         │
         ▼
 [4. Verify Health Probes (GET /api/v1/retrieval/health)]
         │
         ▼
 [5. Execute Smoke Test (test_v55_smoke_test.py)]
         │
         ▼
 [Traffic Restored to Previous Stable Version]
```

### Step 1: Drain Traffic & Stop Service
```bash
# Gracefully terminate running V5.5 uvicorn process
kill -SIGTERM <uvicorn_pid>
```

### Step 2: Revert Application Binaries
```bash
# Revert repository code to previous stable tag/commit
git checkout v5.4-release-tag
```

### Step 3: Restart Application Service
```bash
$env:PYTHONPATH="."
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

### Step 4: Verify Post-Rollback Health & Metrics
```bash
# Run artifact and health verification
python scripts/verify_v55_release_artifacts.py
python scripts/test_v55_smoke_test.py
```

---

## 4. Post-Rollback Verification Criteria

1. `GET /api/v1/retrieval/health` returns `HTTP 200 OK` with 6,689 chunks and vectors.
2. `test_v55_smoke_test.py` passes 100% of standard smoke queries.
3. Client search traffic resumes without exceptions.
