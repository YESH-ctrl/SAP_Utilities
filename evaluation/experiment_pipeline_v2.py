"""
Pipeline V2 Optimization Experiment Script.
Tests RRF + Enhanced Query Processor + Strong Metadata & Document Boosting + Reranker Fix + Hierarchy Conditioning + MMR Tuning.
"""

import os
import json
import asyncio
import logging
from typing import List, Dict, Any

from sap_rag.database.connection import DatabasePool
from sap_rag.retrieval.models import ProcessedQuery, RetrievalCandidate
from sap_rag.retrieval.dense_retriever import DenseRetriever
from sap_rag.retrieval.lexical_retriever import LexicalRetriever
from sap_rag.retrieval.hybrid_retriever import HybridRetriever
from sap_rag.retrieval.metadata_scorer import MetadataScorer
from sap_rag.retrieval.reranker import FastFeatureReranker
from sap_rag.retrieval.query_processor import QueryProcessor
from evaluation.metrics import RetrievalEvaluator

if os.sys.platform == "win32":
    os.sys.stdout.reconfigure(encoding="utf-8")

logging.basicConfig(level=logging.WARNING)

async def run_pipeline_v2_experiments():
    with open("evaluation/retrieval_dataset.json", "r", encoding="utf-8") as f:
        dataset = json.load(f)

    await DatabasePool.initialize(min_size=2, max_size=10)
    dense_retriever = DenseRetriever()
    lexical_retriever = LexicalRetriever()

    try:
        async with DatabasePool.acquire() as conn:
            cached_data = []
            for item in dataset:
                q_text = item["question"]
                p_query = QueryProcessor.process(q_text)
                d_cands = await dense_retriever.search(conn, q_text, top_k=40)
                l_cands = await lexical_retriever.search(conn, p_query, top_k=40)
                cached_data.append((item, p_query, d_cands, l_cands))

            # Test different combinations of Metadata Boost weights
            configs = [
                ("RRF (0.3D/0.7L)", 0.0, 0.0, 0.0),
                ("RRF + Title(0.15) + Breadcrumb(0.15)", 0.15, 0.15, 0.10),
                ("RRF + Title(0.20) + Breadcrumb(0.20)", 0.20, 0.20, 0.10),
                ("RRF + Title(0.25) + Breadcrumb(0.25)", 0.25, 0.25, 0.10),
                ("RRF + Title(0.30) + Breadcrumb(0.20)", 0.30, 0.20, 0.10),
            ]

            print(f"\n{'Config Description':<40} | {'Recall@5':<9} | {'Recall@10':<10} | {'Recall@20':<10} | {'MRR':<8}")
            print("-" * 90)

            for cfg_name, t_boost, b_boost, term_boost in configs:
                q_metrics = []
                for item, p_query, d_cands, l_cands in cached_data:
                    d_c = [c.model_copy() for c in d_cands]
                    l_c = [c.model_copy() for c in l_cands]

                    # 1. RRF Fusion (0.3 Dense / 0.7 Lexical)
                    fused = HybridRetriever.fuse(d_c, l_c, dense_weight=0.30, lexical_weight=0.70)

                    # 2. Score using custom weights
                    scored = MetadataScorer.score_candidates(
                        fused,
                        p_query,
                        title_weight=t_boost,
                        breadcrumb_weight=b_boost,
                        tech_term_weight=term_boost
                    )

                    retrieved_sources = [c.source_id for c in scored if c.source_id is not None]
                    retrieved_docs = [c.document_id for c in scored]

                    m = RetrievalEvaluator.compute_question_metrics(
                        retrieved_source_ids=retrieved_sources,
                        expected_source_ids=item["expected_source_ids"],
                        retrieved_doc_ids=retrieved_docs,
                        expected_doc_ids=item.get("expected_document_ids", [])
                    )
                    q_metrics.append(m)

                avg_m = RetrievalEvaluator.aggregate_metrics(q_metrics)
                r5 = avg_m.get("recall@5", 0.0)
                r10 = avg_m.get("recall@10", 0.0)
                r20 = avg_m.get("recall@20", 0.0)
                mrr = avg_m.get("mrr", 0.0)
                print(f"{cfg_name:<40} | {r5:<9.4f} | {r10:<10.4f} | {r20:<10.4f} | {mrr:<8.4f}")

    finally:
        await DatabasePool.close()

if __name__ == "__main__":
    asyncio.run(run_pipeline_v2_experiments())
