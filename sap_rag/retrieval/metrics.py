"""
Performance timing and execution metrics tracker for retrieval operations.
"""

from typing import Dict, Any
from pydantic import BaseModel

class RetrievalMetrics(BaseModel):
    query_embedding_ms: float = 0.0
    dense_search_ms: float = 0.0
    lexical_search_ms: float = 0.0
    fusion_ms: float = 0.0
    metadata_scoring_ms: float = 0.0
    reranking_ms: float = 0.0
    hierarchy_expansion_ms: float = 0.0
    recovery_ms: float = 0.0
    mmr_ms: float = 0.0
    context_building_ms: float = 0.0
    total_retrieval_ms: float = 0.0

    dense_candidates_count: int = 0
    lexical_candidates_count: int = 0
    merged_candidates_count: int = 0
    reranked_candidates_count: int = 0
    expanded_candidates_count: int = 0
    final_results_count: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "timing_ms": {
                "query_embedding": round(self.query_embedding_ms, 2),
                "dense_search": round(self.dense_search_ms, 2),
                "lexical_search": round(self.lexical_search_ms, 2),
                "fusion": round(self.fusion_ms, 2),
                "metadata_scoring": round(self.metadata_scoring_ms, 2),
                "reranking": round(self.reranking_ms, 2),
                "hierarchy_expansion": round(self.hierarchy_expansion_ms, 2),
                "mmr": round(self.mmr_ms, 2),
                "context_building": round(self.context_building_ms, 2),
                "total_retrieval": round(self.total_retrieval_ms, 2),
            },
            "counts": {
                "dense_candidates": self.dense_candidates_count,
                "lexical_candidates": self.lexical_candidates_count,
                "merged_candidates": self.merged_candidates_count,
                "reranked_candidates": self.reranked_candidates_count,
                "expanded_candidates": self.expanded_candidates_count,
                "final_results": self.final_results_count,
            }
        }
