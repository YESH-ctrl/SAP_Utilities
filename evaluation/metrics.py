"""
Information Retrieval (IR) evaluation metrics calculation for RAG Retrieval Benchmark (V4 Hardened).
Calculates 3-Level Evaluation Metrics:
- Level 1: Source Level (Recall@K, Precision@K, MRR)
- Level 2: Document Level (Document Recall@K, Document MRR)
- Level 3: Chunk Level (Chunk Recall@K, Chunk MRR, NDCG@5, NDCG@10)
"""

import math
from typing import List, Dict, Any, Set

class RetrievalEvaluator:
    """
    Computes 3-Level IR evaluation metrics across benchmark test questions.
    """

    @staticmethod
    def compute_question_metrics(
        retrieved_source_ids: List[int],
        expected_source_ids: List[int],
        retrieved_doc_ids: List[int],
        expected_doc_ids: List[int],
        retrieved_chunk_ids: List[int] = [],
        expected_chunk_ids: List[int] = [],
        k_values: List[int] = [5, 10, 20]
    ) -> Dict[str, float]:
        exp_sources: Set[int] = set(expected_source_ids)
        exp_docs: Set[int] = set(expected_doc_ids)
        exp_chunks: Set[int] = set(expected_chunk_ids)

        metrics: Dict[str, float] = {}

        # ------------------------------------------------------------
        # LEVEL 1 — SOURCE LEVEL EVALUATION
        # ------------------------------------------------------------
        source_mrr = 0.0
        for rank, sid in enumerate(retrieved_source_ids, 1):
            if sid in exp_sources:
                source_mrr = 1.0 / rank
                break
        metrics["source_mrr"] = source_mrr
        metrics["mrr"] = source_mrr  # Backward compatibility

        for k in k_values:
            top_k_sources = retrieved_source_ids[:k]
            matched_sources = sum(1 for sid in top_k_sources if sid in exp_sources)

            recall_k = matched_sources / max(1, len(exp_sources)) if exp_sources else 1.0
            precision_k = matched_sources / max(1, len(top_k_sources)) if top_k_sources else 0.0

            metrics[f"source_recall@{k}"] = min(1.0, recall_k)
            metrics[f"source_precision@{k}"] = min(1.0, precision_k)
            metrics[f"recall@{k}"] = min(1.0, recall_k)        # Backward compatibility
            metrics[f"precision@{k}"] = min(1.0, precision_k)    # Backward compatibility

        # ------------------------------------------------------------
        # LEVEL 2 — DOCUMENT LEVEL EVALUATION
        # ------------------------------------------------------------
        doc_mrr = 0.0
        for rank, did in enumerate(retrieved_doc_ids, 1):
            if did in exp_docs:
                doc_mrr = 1.0 / rank
                break
        metrics["doc_mrr"] = doc_mrr

        for k in k_values:
            top_k_docs = retrieved_doc_ids[:k]
            matched_docs = sum(1 for did in top_k_docs if did in exp_docs)
            doc_recall_k = matched_docs / max(1, len(exp_docs)) if exp_docs else 1.0
            metrics[f"doc_recall@{k}"] = min(1.0, doc_recall_k)

        # ------------------------------------------------------------
        # LEVEL 3 — CHUNK LEVEL & NDCG EVALUATION
        # ------------------------------------------------------------
        chunk_mrr = 0.0
        for rank, cid in enumerate(retrieved_chunk_ids, 1):
            if cid in exp_chunks:
                chunk_mrr = 1.0 / rank
                break
        metrics["chunk_mrr"] = chunk_mrr

        for k in k_values:
            top_k_chunks = retrieved_chunk_ids[:k]
            matched_chunks = sum(1 for cid in top_k_chunks if cid in exp_chunks)
            chunk_recall_k = matched_chunks / max(1, len(exp_chunks)) if exp_chunks else 1.0
            metrics[f"chunk_recall@{k}"] = min(1.0, chunk_recall_k)

        # Compute NDCG@5 and NDCG@10
        for ndcg_k in [5, 10]:
            top_k_chunks = retrieved_chunk_ids[:ndcg_k]
            dcg = 0.0
            for rank, cid in enumerate(top_k_chunks, 1):
                rel = 1.0 if cid in exp_chunks else 0.0
                dcg += rel / math.log2(rank + 1)

            idcg = 0.0
            max_rel = min(ndcg_k, len(exp_chunks)) if exp_chunks else 1
            for rank in range(1, max_rel + 1):
                idcg += 1.0 / math.log2(rank + 1)

            ndcg = (dcg / idcg) if idcg > 0 else 0.0
            metrics[f"ndcg@{ndcg_k}"] = min(1.0, ndcg)

        return metrics

    @staticmethod
    def aggregate_metrics(all_question_metrics: List[Dict[str, float]]) -> Dict[str, float]:
        if not all_question_metrics:
            return {}

        avg_metrics: Dict[str, float] = {}
        keys = all_question_metrics[0].keys()
        n = len(all_question_metrics)

        for key in keys:
            total_val = sum(m.get(key, 0.0) for m in all_question_metrics)
            avg_metrics[key] = round(total_val / n, 4)

        return avg_metrics
