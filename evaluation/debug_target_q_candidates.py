"""
Detailed candidate pool diagnostic for Q9, Q10, Q41, Q43, Q50.
"""

import json
import asyncio
from sap_rag.database.connection import DatabasePool
from sap_rag.retrieval.dense_retriever import DenseRetriever
from sap_rag.retrieval.lexical_retriever import LexicalRetriever
from sap_rag.retrieval.hybrid_retriever import HybridRetriever
from sap_rag.retrieval.query_processor import QueryProcessor

BENCHMARK_FILE = "evaluation/datasets/retrieval_benchmark_v5_1.json"
TARGET_QIDS = ["9", "10", "41", "43", "50"]

async def debug_pool():
    await DatabasePool.initialize(min_size=2, max_size=5)
    dense_retriever = DenseRetriever()
    lexical_retriever = LexicalRetriever()

    with open(BENCHMARK_FILE, "r", encoding="utf-8") as f:
        dataset = json.load(f)

    target_items = [item for item in dataset if item["query_id"] in TARGET_QIDS]

    async with DatabasePool.acquire() as conn, DatabasePool.acquire() as conn_lex:
        for item in target_items:
            q_id = item["query_id"]
            q_text = item["query"]
            exp_sources = set(item["expected_source_ids"])

            p_query = QueryProcessor.process(q_text)

            d_cands = await dense_retriever.search(conn, query=q_text, top_k=40)
            l_cands = await lexical_retriever.search(conn_lex, processed_query=p_query, top_k=40, use_expanded=True)
            fused = HybridRetriever.fuse(d_cands, l_cands, dense_weight=0.5, lexical_weight=0.5)

            print(f"=========================================================")
            print(f"QID {q_id} | Query: '{q_text}'")
            print(f"Expected Sources: {list(exp_sources)}")
            print(f"Dense contains GT  : {bool({c.source_id for c in d_cands if c.source_id is not None}.intersection(exp_sources))}")
            print(f"Lexical contains GT: {bool({c.source_id for c in l_cands if c.source_id is not None}.intersection(exp_sources))}")
            print(f"Fused pool contains GT: {bool({c.source_id for c in fused if c.source_id is not None}.intersection(exp_sources))}")

            print("\nPositions of Expected Sources in Fused Pool:")
            found_any = False
            for rank, c in enumerate(fused, 1):
                if c.source_id in exp_sources:
                    found_any = True
                    print(f"  Rank #{rank:2d} | Src {c.source_id:2d} | Doc {c.document_id:4d} | DenseRank: {c.dense_rank} | LexRank: {c.lexical_rank} | RRF: {c.hybrid_score:.4f} | Title: {c.title[:50]}")
            if not found_any:
                print("  -> GT Sources NOT FOUND in Fused 40 pool!")
            print()

    await DatabasePool.close()

if __name__ == "__main__":
    asyncio.run(debug_pool())
