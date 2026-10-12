"""
Test script for V5.5 to evaluate Q9, Q10, Q41, Q43, and Q50 performance.
"""

import os
import json
import asyncio
from typing import Dict, Any

from sap_rag.database.connection import DatabasePool
from sap_rag.retrieval.retrieval_pipeline import RetrievalPipeline
from evaluation.metrics import RetrievalEvaluator

BENCHMARK_FILE = "evaluation/datasets/retrieval_benchmark_v5_1.json"
TARGET_QIDS = ["9", "10", "41", "43", "50"]

async def test_targets():
    await DatabasePool.initialize(min_size=2, max_size=10)
    pipeline = RetrievalPipeline()

    with open(BENCHMARK_FILE, "r", encoding="utf-8") as f:
        dataset = json.load(f)

    target_items = [item for item in dataset if item["query_id"] in TARGET_QIDS]

    async with DatabasePool.acquire() as conn:
        for item in target_items:
            q_id = item["query_id"]
            q_text = item["query"]
            exp_sources = item["expected_source_ids"]

            cands, _, p_query, metrics = await pipeline.execute(
                conn,
                query=q_text,
                top_k=10,
                dense_candidate_k=40,
                lexical_candidate_k=40,
                dense_weight=0.5,
                lexical_weight=0.5,
                config_name="V5_FINAL",
                adaptive_routing=True,
                relevance_weight=0.0025,
                enable_top1_protection=True,
                max_per_doc=10,
                hierarchy_recovery_mode="H1"
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

            print(f"QID {q_id:2s} | '{q_text}'")
            print(f"       Domain: {p_query.domain} | Intent: {p_query.intent} | TechTerms: {p_query.technical_terms}")
            print(f"       Expected Sources: {exp_sources}")
            print(f"       Retrieved Top-5 Sources: {retrieved_sources[:5]}")
            print(f"       R@5={q_m['source_recall@5']:.4f} | R@10={q_m['source_recall@10']:.4f} | MRR={q_m['mrr']:.4f}")
            print("       Top 5 Candidates:")
            for rank, c in enumerate(cands[:5], 1):
                print(f"         #{rank} | Src: {c.source_id:2d} | Doc: {c.document_id:3d} | RRF: {c.hybrid_score:.4f} | Pre: {c.pre_rerank_score:.4f} | Final: {c.final_score:.4f} | Title: {c.title[:45]}")
            print()

    await DatabasePool.close()

if __name__ == "__main__":
    asyncio.run(test_targets())
