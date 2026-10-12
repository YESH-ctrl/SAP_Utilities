"""
Diagnostic script for V5.3 to analyze the 5 degraded queries (Q4, Q5, Q28, Q37, Q41)
and high-value MRR failure queries across RRF weights, candidate depths, and diversification settings.
"""

import os
import json
import asyncio
from typing import Dict, Any, List

from sap_rag.database.connection import DatabasePool
from sap_rag.retrieval.retrieval_pipeline import RetrievalPipeline
from evaluation.metrics import RetrievalEvaluator

BENCHMARK_FILE = "evaluation/datasets/retrieval_benchmark_v5_1.json"
TARGET_QIDS = ["4", "5", "28", "37", "41", "8", "17", "19", "20", "31", "39", "42", "45", "46", "47"]

async def diagnose():
    await DatabasePool.initialize(min_size=2, max_size=10)
    pipeline = RetrievalPipeline()

    with open(BENCHMARK_FILE, "r", encoding="utf-8") as f:
        dataset = json.load(f)

    target_items = [item for item in dataset if item["query_id"] in TARGET_QIDS]

    configs = [
        ("V3_RRF_50_50_k20", "V3_RRF", 0.5, 0.5, 20, 20, 0.0, False, 10),
        ("V5_2_Best_40_60_k60_div2", "V5_FINAL", 0.4, 0.6, 60, 60, 0.0010, True, 2),
        ("V5_3_RRF_50_50_k40_nodiv", "V5_FINAL", 0.5, 0.5, 40, 40, 0.0010, True, 10),
        ("V5_3_RRF_50_50_k60_nodiv", "V5_FINAL", 0.5, 0.5, 60, 60, 0.0010, True, 10),
        ("V5_3_RRF_50_50_k40_div3", "V5_FINAL", 0.5, 0.5, 40, 40, 0.0010, True, 3),
    ]

    results = []

    async with DatabasePool.acquire() as conn:
        for item in target_items:
            q_id = item["query_id"]
            q_text = item["query"]
            exp_sources = item["expected_source_ids"]

            q_res = {
                "query_id": q_id,
                "query": q_text,
                "expected_sources": exp_sources,
                "config_scores": {}
            }

            for cfg_name, cfg_code, dw, lw, dk, lk, rel_w, prot, max_doc in configs:
                cands, _, p_query, metrics = await pipeline.execute(
                    conn,
                    query=q_text,
                    top_k=8,
                    dense_candidate_k=dk,
                    lexical_candidate_k=lk,
                    dense_weight=dw,
                    lexical_weight=lw,
                    config_name=cfg_code,
                    adaptive_routing=True,
                    relevance_weight=rel_w,
                    enable_top1_protection=prot,
                    max_per_doc=max_doc
                )

                retrieved_sources = [c.source_id for c in cands if c.source_id is not None]
                retrieved_docs = [c.document_id for c in cands]

                exp_docs = [rd["document_id"] for rd in item.get("relevant_documents", []) if rd.get("relevance", 0) >= 2]

                q_m = RetrievalEvaluator.compute_question_metrics(
                    retrieved_source_ids=retrieved_sources,
                    expected_source_ids=exp_sources,
                    retrieved_doc_ids=retrieved_docs,
                    expected_doc_ids=exp_docs
                )

                q_res["config_scores"][cfg_name] = {
                    "source_r5": q_m["source_recall@5"],
                    "source_r10": q_m["source_recall@10"],
                    "doc_r10": q_m["doc_recall@10"],
                    "mrr": q_m["mrr"],
                    "top5_sources": retrieved_sources[:5]
                }

            results.append(q_res)

    print(json.dumps(results, indent=2))
    await DatabasePool.close()

if __name__ == "__main__":
    asyncio.run(diagnose())
