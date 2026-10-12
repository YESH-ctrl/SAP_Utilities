"""
Diagnostic Script for Failure Analysis across 50 SAP Utilities Retrieval Benchmark Questions.
Performs stage-by-stage tracking to identify exact failure points.
"""

import os
import json
import asyncio
import logging
from typing import List, Dict, Any

from sap_rag.database.connection import DatabasePool
from sap_rag.retrieval.models import ProcessedQuery
from sap_rag.retrieval.dense_retriever import DenseRetriever
from sap_rag.retrieval.lexical_retriever import LexicalRetriever
from sap_rag.retrieval.hybrid_retriever import HybridRetriever
from sap_rag.retrieval.metadata_scorer import MetadataScorer
from sap_rag.retrieval.reranker import RetrievalReranker
from sap_rag.retrieval.hierarchy_expander import HierarchyExpander
from sap_rag.retrieval.mmr import MMRSelector
from sap_rag.retrieval.query_processor import QueryProcessor

if os.sys.platform == "win32":
    os.sys.stdout.reconfigure(encoding="utf-8")

logging.basicConfig(level=logging.WARNING)

def find_first_rank(candidates: List[Any], expected_sources: List[int]) -> int:
    for rank, c in enumerate(candidates, start=1):
        if c.source_id in expected_sources:
            return rank
    return 999  # Not found in candidate set

async def run_diagnostics():
    with open("evaluation/retrieval_dataset.json", "r", encoding="utf-8") as f:
        dataset = json.load(f)

    await DatabasePool.initialize(min_size=2, max_size=10)
    dense_retriever = DenseRetriever()
    lexical_retriever = LexicalRetriever()
    reranker = RetrievalReranker()

    matrix = []

    try:
        async with DatabasePool.acquire() as conn:
            for item in dataset:
                q_id = item["id"]
                q_text = item["question"]
                exp_sources = item["expected_source_ids"]

                p_query = QueryProcessor.process(q_text)

                # Step 1: Dense search (top 50)
                d_cands = await dense_retriever.search(conn, q_text, top_k=50)
                dense_rank = find_first_rank(d_cands, exp_sources)

                # Step 2: Lexical search (top 50)
                l_cands = await lexical_retriever.search(conn, p_query, top_k=50)
                lex_rank = find_first_rank(l_cands, exp_sources)

                # Step 3: Hybrid min-max fusion
                fused_cands = HybridRetriever.fuse(d_cands, l_cands)
                hybrid_rank = find_first_rank(fused_cands, exp_sources)

                # Step 4: Metadata scoring
                meta_cands = MetadataScorer.score_candidates([c.copy() for c in fused_cands], p_query)
                meta_rank = find_first_rank(meta_cands, exp_sources)

                # Step 5: Reranking (top 20)
                reranked_cands = reranker.rerank(p_query, [c.copy() for c in meta_cands], top_k=20)
                rerank_rank = find_first_rank(reranked_cands, exp_sources)

                # Step 6: Hierarchy expansion
                expanded_cands = await HierarchyExpander.expand(conn, [c.copy() for c in reranked_cands], window=1)

                # Step 7: Final MMR 8
                final_cands = MMRSelector.select(expanded_cands, top_k=8, mmr_lambda=0.75)
                final_rank = find_first_rank(final_cands, exp_sources)

                # Determine failure stage if final rank > 5
                failure_stage = "SUCCESS"
                if final_rank > 10:
                    if dense_rank > 50 and lex_rank > 50:
                        failure_stage = "INITIAL_RETRIEVAL_MISS"
                    elif (lex_rank <= 10 or dense_rank <= 10) and hybrid_rank > 10:
                        failure_stage = "HYBRID_FUSION_PENALTY"
                    elif hybrid_rank <= 10 and meta_rank > 10:
                        failure_stage = "METADATA_SCORE_DEMOTION"
                    elif meta_rank <= 10 and rerank_rank > 10:
                        failure_stage = "RERANKER_DEMOTION"
                    else:
                        failure_stage = "RANK_SLIPPAGE"
                elif final_rank > 5:
                    failure_stage = "SUB_TOP_5"

                matrix.append({
                    "id": q_id,
                    "question": q_text,
                    "expected_sources": exp_sources,
                    "dense_rank": dense_rank if dense_rank <= 50 else None,
                    "lexical_rank": lex_rank if lex_rank <= 50 else None,
                    "hybrid_rank": hybrid_rank if hybrid_rank <= 50 else None,
                    "metadata_rank": meta_rank if meta_rank <= 50 else None,
                    "reranker_rank": rerank_rank if rerank_rank <= 20 else None,
                    "final_rank": final_rank if final_rank <= 8 else None,
                    "failure_stage": failure_stage
                })

        # Output matrix
        print(f"\n{'ID':<3} | {'Dense':<5} | {'Lex':<5} | {'Hybrd':<5} | {'Meta':<5} | {'Rerank':<6} | {'Final':<5} | {'Failure Stage':<22} | Question")
        print("-" * 115)
        for row in matrix:
            d_s = str(row['dense_rank']) if row['dense_rank'] else "-"
            l_s = str(row['lexical_rank']) if row['lexical_rank'] else "-"
            h_s = str(row['hybrid_rank']) if row['hybrid_rank'] else "-"
            m_s = str(row['metadata_rank']) if row['metadata_rank'] else "-"
            r_s = str(row['reranker_rank']) if row['reranker_rank'] else "-"
            f_s = str(row['final_rank']) if row['final_rank'] else "-"
            print(f"{row['id']:<3} | {d_s:<5} | {l_s:<5} | {h_s:<5} | {m_s:<5} | {r_s:<6} | {f_s:<5} | {row['failure_stage']:<22} | {row['question'][:40]}")

        os.makedirs("storage/reports", exist_ok=True)
        with open("storage/reports/failure_matrix.json", "w", encoding="utf-8") as f:
            json.dump(matrix, f, indent=2)
        print("\nSaved failure matrix to storage/reports/failure_matrix.json")

    finally:
        await DatabasePool.close()

if __name__ == "__main__":
    asyncio.run(run_diagnostics())
