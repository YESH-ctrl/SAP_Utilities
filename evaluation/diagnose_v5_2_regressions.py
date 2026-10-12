"""
Query-by-Query Regression Diagnostic Tool for V5.2 (Phase 7).
Executes Canonical V3 RRF baseline and V5.1 production pipeline on all 50 queries,
isolates the degraded queries, extracts candidate rank shifts, RRF scores, and feature breakdowns,
and classifies root causes.
"""

import os
import json
import asyncio
import logging
from typing import List, Dict, Any

from sap_rag.database.connection import DatabasePool
from sap_rag.retrieval.retrieval_pipeline import RetrievalPipeline
from evaluation.metrics import RetrievalEvaluator

if os.sys.platform == "win32":
    os.sys.stdout.reconfigure(encoding="utf-8")

logging.basicConfig(level=logging.WARNING)

async def diagnose_regressions():
    bench_file = "evaluation/datasets/retrieval_benchmark_v5_1.json"
    with open(bench_file, "r", encoding="utf-8") as f:
        dataset = json.load(f)

    await DatabasePool.initialize(min_size=2, max_size=5)
    pipeline = RetrievalPipeline()

    v3_results = []
    v51_results = []

    try:
        async with DatabasePool.acquire() as conn:
            for item in dataset:
                q_id = item["query_id"]
                q_text = item["query"]

                exp_docs = [rd["document_id"] for rd in item.get("relevant_documents", []) if rd.get("relevance", 0) >= 2]
                exp_chunks = [rc["chunk_id"] for rc in item.get("relevant_chunks", []) if rc.get("relevance", 0) >= 2]

                # Run V3 RRF baseline
                v3_cands, _, _, _ = await pipeline.execute(conn, query=q_text, top_k=8, config_name="V3_RRF")
                v3_m = RetrievalEvaluator.compute_question_metrics(
                    retrieved_source_ids=[c.source_id for c in v3_cands if c.source_id],
                    expected_source_ids=item["expected_source_ids"],
                    retrieved_doc_ids=[c.document_id for c in v3_cands],
                    expected_doc_ids=exp_docs,
                    retrieved_chunk_ids=[c.chunk_id for c in v3_cands],
                    expected_chunk_ids=exp_chunks
                )

                # Run V5.1 Final pipeline
                v51_cands, _, p_q, _ = await pipeline.execute(conn, query=q_text, top_k=8, config_name="V5_FINAL")
                v51_m = RetrievalEvaluator.compute_question_metrics(
                    retrieved_source_ids=[c.source_id for c in v51_cands if c.source_id],
                    expected_source_ids=item["expected_source_ids"],
                    retrieved_doc_ids=[c.document_id for c in v51_cands],
                    expected_doc_ids=exp_docs,
                    retrieved_chunk_ids=[c.chunk_id for c in v51_cands],
                    expected_chunk_ids=exp_chunks
                )

                v3_results.append({
                    "query_id": q_id,
                    "query": q_text,
                    "metrics": v3_m,
                    "cands": v3_cands
                })

                v51_results.append({
                    "query_id": q_id,
                    "query": q_text,
                    "metrics": v51_m,
                    "cands": v51_cands
                })

    finally:
        await DatabasePool.close()

    # Compare query-by-query
    degraded = []
    for v3_res, v51_res in zip(v3_results, v51_results):
        mrr_delta = v51_res["metrics"]["mrr"] - v3_res["metrics"]["mrr"]
        r10_delta = v51_res["metrics"]["source_recall@10"] - v3_res["metrics"]["source_recall@10"]

        if mrr_delta < -0.001 or r10_delta < -0.001:
            degraded.append({
                "query_id": v3_res["query_id"],
                "query": v3_res["query"],
                "v3_mrr": v3_res["metrics"]["mrr"],
                "v51_mrr": v51_res["metrics"]["mrr"],
                "mrr_delta": round(mrr_delta, 4),
                "v3_r10": v3_res["metrics"]["source_recall@10"],
                "v51_r10": v51_res["metrics"]["source_recall@10"],
                "v3_top1": v3_res["cands"][0].title if v3_res["cands"] else "None",
                "v51_top1": v51_res["cands"][0].title if v51_res["cands"] else "None",
                "v3_top1_source": v3_res["cands"][0].source_id if v3_res["cands"] else None,
                "v51_top1_source": v51_res["cands"][0].source_id if v51_res["cands"] else None,
                "feature_breakdown": v51_res["cands"][0].feature_breakdown if v51_res["cands"] else {}
            })

    print(f"Total Degraded Queries Identified: {len(degraded)}")
    for d in degraded:
        print(f"Q{d['query_id']}: '{d['query']}' | MRR: {d['v3_mrr']} -> {d['v51_mrr']} ({d['mrr_delta']})")

    # Output to JSON for audit inspection
    os.makedirs("storage/reports", exist_ok=True)
    with open("storage/reports/v5_2_degraded_queries_analysis.json", "w", encoding="utf-8") as f:
        json.dump(degraded, f, indent=2)

if __name__ == "__main__":
    asyncio.run(diagnose_regressions())
