"""
Experiment Script to evaluate Hybrid Fusion Strategies:
- Current Min-Max
- Non-negative Min-Max
- Reciprocal Rank Fusion (RRF k=20, 40, 60, 100)
- Weighted RRF
"""

import os
import json
import asyncio
import logging
from typing import List, Dict, Any, Optional

from sap_rag.database.connection import DatabasePool
from sap_rag.retrieval.models import ProcessedQuery, RetrievalCandidate
from sap_rag.retrieval.dense_retriever import DenseRetriever
from sap_rag.retrieval.lexical_retriever import LexicalRetriever
from sap_rag.retrieval.query_processor import QueryProcessor
from evaluation.metrics import RetrievalEvaluator

if os.sys.platform == "win32":
    os.sys.stdout.reconfigure(encoding="utf-8")

logging.basicConfig(level=logging.WARNING)

def rrf_fusion(
    dense_candidates: List[RetrievalCandidate],
    lexical_candidates: List[RetrievalCandidate],
    k: int = 60,
    w_dense: float = 0.5,
    w_lex: float = 0.5
) -> List[RetrievalCandidate]:
    merged: Dict[int, RetrievalCandidate] = {}
    
    dense_ranks = {c.chunk_id: rank for rank, c in enumerate(dense_candidates, start=1)}
    lex_ranks = {c.chunk_id: rank for rank, c in enumerate(lexical_candidates, start=1)}

    for cand in dense_candidates:
        merged[cand.chunk_id] = cand

    for cand in lexical_candidates:
        if cand.chunk_id in merged:
            merged[cand.chunk_id].lexical_score = cand.lexical_score
            merged[cand.chunk_id].retrieval_method = "hybrid"
        else:
            cand.retrieval_method = "lexical"
            merged[cand.chunk_id] = cand

    for cid, cand in merged.items():
        d_rank = dense_ranks.get(cid, 999)
        l_rank = lex_ranks.get(cid, 999)

        r_dense = 1.0 / (k + d_rank) if d_rank <= 100 else 0.0
        r_lex = 1.0 / (k + l_rank) if l_rank <= 100 else 0.0

        cand.hybrid_score = (w_dense * r_dense) + (w_lex * r_lex)

    all_cands = list(merged.values())
    all_cands.sort(key=lambda x: x.hybrid_score, reverse=True)
    return all_cands

def non_negative_minmax_fusion(
    dense_candidates: List[RetrievalCandidate],
    lexical_candidates: List[RetrievalCandidate],
    w_dense: float = 0.5,
    w_lex: float = 0.5
) -> List[RetrievalCandidate]:
    merged: Dict[int, RetrievalCandidate] = {}

    for cand in dense_candidates:
        merged[cand.chunk_id] = cand

    for cand in lexical_candidates:
        if cand.chunk_id in merged:
            merged[cand.chunk_id].lexical_score = cand.lexical_score
            merged[cand.chunk_id].retrieval_method = "hybrid"
        else:
            cand.retrieval_method = "lexical"
            merged[cand.chunk_id] = cand

    all_cands = list(merged.values())
    if not all_cands:
        return []

    d_scores = [c.dense_score for c in dense_candidates if c.dense_score > 0]
    max_d = max(d_scores) if d_scores else 1.0
    min_d = min(d_scores) if d_scores else 0.0
    d_span = (max_d - min_d) if (max_d - min_d) > 1e-6 else 1.0

    l_scores = [c.lexical_score for c in lexical_candidates if c.lexical_score > 0]
    max_l = max(l_scores) if l_scores else 1.0
    min_l = min(l_scores) if l_scores else 0.0
    l_span = (max_l - min_l) if (max_l - min_l) > 1e-6 else 1.0

    for c in all_cands:
        norm_d = ((c.dense_score - min_d) / d_span) if (c.dense_score > 0 and max_d > min_d) else 0.0
        norm_l = ((c.lexical_score - min_l) / l_span) if (c.lexical_score > 0 and max_l > min_l) else 0.0
        norm_d = max(0.0, norm_d)
        norm_l = max(0.0, norm_l)

        c.hybrid_score = (w_dense * norm_d) + (w_lex * norm_l)

    all_cands.sort(key=lambda x: x.hybrid_score, reverse=True)
    return all_cands

async def run_fusion_experiments():
    with open("evaluation/retrieval_dataset.json", "r", encoding="utf-8") as f:
        dataset = json.load(f)

    await DatabasePool.initialize(min_size=2, max_size=10)
    dense_retriever = DenseRetriever()
    lexical_retriever = LexicalRetriever()

    strategies = [
        ("Current MinMax (0.7/0.3)", lambda d, l: non_negative_minmax_fusion(d, l, 0.7, 0.3)), # corrected minmax
        ("RRF k=20 (0.5/0.5)", lambda d, l: rrf_fusion(d, l, k=20, w_dense=0.5, w_lex=0.5)),
        ("RRF k=40 (0.5/0.5)", lambda d, l: rrf_fusion(d, l, k=40, w_dense=0.5, w_lex=0.5)),
        ("RRF k=60 (0.5/0.5)", lambda d, l: rrf_fusion(d, l, k=60, w_dense=0.5, w_lex=0.5)),
        ("RRF k=60 (0.4D / 0.6L)", lambda d, l: rrf_fusion(d, l, k=60, w_dense=0.4, w_lex=0.6)),
        ("RRF k=60 (0.3D / 0.7L)", lambda d, l: rrf_fusion(d, l, k=60, w_dense=0.3, w_lex=0.7)),
        ("RRF k=100 (0.5/0.5)", lambda d, l: rrf_fusion(d, l, k=100, w_dense=0.5, w_lex=0.5)),
    ]

    try:
        async with DatabasePool.acquire() as conn:
            # Cache retrieval candidates per item
            cached_data = []
            for item in dataset:
                q_text = item["question"]
                exp_sources = item["expected_source_ids"]
                exp_docs = item.get("expected_document_ids", [])
                p_query = QueryProcessor.process(q_text)

                d_cands = await dense_retriever.search(conn, q_text, top_k=50)
                l_cands = await lexical_retriever.search(conn, p_query, top_k=50)
                cached_data.append((item, p_query, d_cands, l_cands))

            print(f"\n{'Fusion Strategy':<25} | {'Recall@5':<9} | {'Recall@10':<10} | {'Recall@20':<10} | {'MRR':<8}")
            print("-" * 75)

            for strat_name, strat_fn in strategies:
                q_metrics = []
                for item, p_query, d_cands, l_cands in cached_data:
                    # Deep copy candidate objects
                    d_c = [c.model_copy() for c in d_cands]
                    l_c = [c.model_copy() for c in l_cands]

                    fused = strat_fn(d_c, l_c)
                    retrieved_sources = [c.source_id for c in fused if c.source_id is not None]
                    retrieved_docs = [c.document_id for c in fused]

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
                print(f"{strat_name:<25} | {r5:<9.4f} | {r10:<10.4f} | {r20:<10.4f} | {mrr:<8.4f}")

    finally:
        await DatabasePool.close()

if __name__ == "__main__":
    asyncio.run(run_fusion_experiments())
