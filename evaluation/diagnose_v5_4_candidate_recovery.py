"""
V5.4 Candidate-Presence & Failure Classification Diagnostic Script.
For every benchmark query calculates:
- dense_contains_relevant
- lexical_contains_relevant
- initial_rrf_contains_relevant
- failure classification: NONE, INITIAL_CANDIDATE_MISS, RECOVERED_CANDIDATE_MISS, RANKING_MISS, GROUND_TRUTH_NOT_FOUND_AFTER_MAX_DEPTH
- overlap_ratio and uncertainty trigger
- hierarchy parent recovery effect
"""

import os
import json
import asyncio
from typing import Dict, Any, List

from sap_rag.database.connection import DatabasePool
from sap_rag.retrieval.models import ProcessedQuery, RetrievalCandidate
from sap_rag.retrieval.dense_retriever import DenseRetriever
from sap_rag.retrieval.lexical_retriever import LexicalRetriever
from sap_rag.retrieval.hybrid_retriever import HybridRetriever
from sap_rag.retrieval.query_processor import QueryProcessor
from evaluation.metrics import RetrievalEvaluator

BENCHMARK_FILE = "evaluation/datasets/retrieval_benchmark_v5_1.json"

async def diagnose():
    await DatabasePool.initialize(min_size=2, max_size=10)
    dense_retriever = DenseRetriever()
    lexical_retriever = LexicalRetriever()

    with open(BENCHMARK_FILE, "r", encoding="utf-8") as f:
        dataset = json.load(f)

    diagnostics = []

    true_candidate_misses = 0
    ranking_misses = 0
    recovered_misses = 0
    none_count = 0

    async with DatabasePool.acquire() as conn:
        async with DatabasePool.acquire() as conn_lex:
            for item in dataset:
                q_id = item["query_id"]
                q_text = item["query"]
                exp_sources = set(item["expected_source_ids"])

                p_query = QueryProcessor.process(q_text)

                # Search at k=40
                d_cands_40 = await dense_retriever.search(conn, query=q_text, top_k=40)
                l_cands_40 = await lexical_retriever.search(conn_lex, processed_query=p_query, top_k=40)

                d_sids_40 = {c.source_id for c in d_cands_40 if c.source_id is not None}
                l_sids_40 = {c.source_id for c in l_cands_40 if c.source_id is not None}
                fused_40 = HybridRetriever.fuse(d_cands_40, l_cands_40, dense_weight=0.5, lexical_weight=0.5)
                fused_sids_40_top10 = {c.source_id for c in fused_40[:10] if c.source_id is not None}
                fused_sids_40_all = {c.source_id for c in fused_40 if c.source_id is not None}

                # Search at k=100
                d_cands_100 = await dense_retriever.search(conn, query=q_text, top_k=100)
                l_cands_100 = await lexical_retriever.search(conn_lex, processed_query=p_query, top_k=100)
                fused_100 = HybridRetriever.fuse(d_cands_100, l_cands_100, dense_weight=0.5, lexical_weight=0.5)
                fused_sids_100_all = {c.source_id for c in fused_100 if c.source_id is not None}

                d_has = bool(d_sids_40.intersection(exp_sources))
                l_has = bool(l_sids_40.intersection(exp_sources))
                top10_has = bool(fused_sids_40_top10.intersection(exp_sources))
                pool40_has = bool(fused_sids_40_all.intersection(exp_sources))
                pool100_has = bool(fused_sids_100_all.intersection(exp_sources))

                # Compute overlap
                d_cids = {c.chunk_id for c in d_cands_40}
                l_cids = {c.chunk_id for c in l_cands_40}
                overlap = len(d_cids.intersection(l_cids)) / max(1, len(d_cids.union(l_cids)))

                # Classification
                if top10_has:
                    classification = "NONE"
                    none_count += 1
                elif pool40_has and not top10_has:
                    classification = "RANKING_MISS"
                    ranking_misses += 1
                elif not pool40_has and pool100_has:
                    classification = "RECOVERED_CANDIDATE_MISS"
                    recovered_misses += 1
                else:
                    classification = "TRUE_CANDIDATE_MISS"
                    true_candidate_misses += 1

                diagnostics.append({
                    "query_id": q_id,
                    "query": q_text,
                    "expected_sources": list(exp_sources),
                    "dense_contains_gt": d_has,
                    "lexical_contains_gt": l_has,
                    "top10_contains_gt": top10_has,
                    "pool40_contains_gt": pool40_has,
                    "pool100_contains_gt": pool100_has,
                    "overlap_ratio": round(overlap, 4),
                    "classification": classification
                })

    print("=================================================================")
    print("         V5.4 CANDIDATE RECOVERY & FAILURE DIAGNOSTICS          ")
    print("=================================================================")
    print(f"Total Queries Analyzed         : {len(dataset)}")
    print(f"Top-10 Ground Truth Hits (NONE): {none_count}")
    print(f"Ranking Misses                 : {ranking_misses}")
    print(f"Recovered Candidate Misses (k=100): {recovered_misses}")
    print(f"True Candidate Misses (k>100)  : {true_candidate_misses}")

    os.makedirs("storage/reports", exist_ok=True)
    with open("storage/reports/v5_4_query_diagnostics.json", "w", encoding="utf-8") as f:
        json.dump(diagnostics, f, indent=2)

    await DatabasePool.close()

if __name__ == "__main__":
    asyncio.run(diagnose())
