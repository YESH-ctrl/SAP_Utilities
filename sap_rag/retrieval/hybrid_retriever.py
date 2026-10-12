"""
Hybrid retrieval fusion component combining dense vector and lexical FTS candidate results using Reciprocal Rank Fusion (RRF) with missing-channel neutrality and exact-match candidate protection.
"""

import logging
from typing import List, Dict, Optional
from sap_rag.retrieval.config import retrieval_settings
from sap_rag.retrieval.models import RetrievalCandidate

logger = logging.getLogger(__name__)

class HybridRetriever:
    """
    Hybrid retriever combining and fusing dense vector and lexical search candidates.
    Supports Missing-Channel Neutral Reciprocal Rank Fusion (RRF) and Exact Match Protection.
    """

    @classmethod
    def fuse(
        cls,
        dense_candidates: List[RetrievalCandidate],
        lexical_candidates: List[RetrievalCandidate],
        dense_weight: float = retrieval_settings.DENSE_WEIGHT,
        lexical_weight: float = retrieval_settings.LEXICAL_WEIGHT,
        strategy: str = retrieval_settings.FUSION_STRATEGY,
        rrf_k: int = retrieval_settings.RRF_K
    ) -> List[RetrievalCandidate]:
        """
        Merge dense and lexical candidate lists by chunk_id and calculate hybrid scores with protection.
        """
        return cls.fuse_rrf(
            dense_candidates=dense_candidates,
            lexical_candidates=lexical_candidates,
            k=rrf_k,
            dense_weight=dense_weight,
            lexical_weight=lexical_weight
        )

    @classmethod
    def fuse_rrf(
        cls,
        dense_candidates: List[RetrievalCandidate],
        lexical_candidates: List[RetrievalCandidate],
        k: int = 60,
        dense_weight: float = 0.30,
        lexical_weight: float = 0.70
    ) -> List[RetrievalCandidate]:
        """
        Reciprocal Rank Fusion (RRF) with missing-channel neutrality and exact match protection (Phase 1 & 2).
        Formula: RRF_score = w_dense / (k + dense_rank) + w_lex / (k + lexical_rank)
        """
        merged: Dict[int, RetrievalCandidate] = {}

        # 1. Map ranks (1-based)
        for rank, cand in enumerate(dense_candidates, start=1):
            cand.dense_rank = rank
            merged[cand.chunk_id] = cand

        for rank, cand in enumerate(lexical_candidates, start=1):
            if cand.chunk_id in merged:
                merged[cand.chunk_id].lexical_score = cand.lexical_score
                merged[cand.chunk_id].lexical_rank = rank
                merged[cand.chunk_id].retrieval_method = "hybrid"
            else:
                cand.lexical_rank = rank
                cand.retrieval_method = "lexical"
                merged[cand.chunk_id] = cand

        if not merged:
            return []

        # Weights calculation
        tot_w = dense_weight + lexical_weight
        w_d = dense_weight / tot_w if tot_w > 0 else 0.30
        w_l = lexical_weight / tot_w if tot_w > 0 else 0.70

        # 2. Score candidates with missing-channel neutrality & exact match protection
        for cid, cand in merged.items():
            d_rank = cand.dense_rank
            l_rank = cand.lexical_rank

            r_dense = 1.0 / (k + d_rank) if d_rank is not None and d_rank <= 100 else 0.0
            r_lex = 1.0 / (k + l_rank) if l_rank is not None and l_rank <= 100 else 0.0

            # Base RRF score
            base_rrf = (w_d * r_dense) + (w_l * r_lex)

            # Phase 2: Lexical Exact Match Protection
            # If candidate is rank 1-3 in lexical search, mark as protected
            if l_rank is not None and l_rank <= 3:
                cand.is_protected = True
                protection_boost = 0.005  # Ensures top lexical results stay competitive
            else:
                protection_boost = 0.0

            cand.hybrid_score = base_rrf + protection_boost

        all_candidates = list(merged.values())
        all_candidates.sort(key=lambda x: x.hybrid_score, reverse=True)
        return all_candidates
