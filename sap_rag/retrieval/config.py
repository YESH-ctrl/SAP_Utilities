"""
Configuration settings for SAP Utilities RAG Retrieval Engine.
"""

import os
from pydantic_settings import BaseSettings

class RetrievalSettings(BaseSettings):
    DENSE_TOP_K: int = int(os.getenv("RETRIEVAL_DENSE_TOP_K", "40"))
    LEXICAL_TOP_K: int = int(os.getenv("RETRIEVAL_LEXICAL_TOP_K", "40"))
    RERANK_TOP_K: int = int(os.getenv("RETRIEVAL_RERANK_TOP_K", "15"))
    FINAL_TOP_K: int = int(os.getenv("RETRIEVAL_FINAL_TOP_K", "8"))

    DENSE_WEIGHT: float = float(os.getenv("RETRIEVAL_DENSE_WEIGHT", "0.30"))
    LEXICAL_WEIGHT: float = float(os.getenv("RETRIEVAL_LEXICAL_WEIGHT", "0.70"))

    FUSION_STRATEGY: str = os.getenv("RETRIEVAL_FUSION_STRATEGY", "rrf")
    RRF_K: int = int(os.getenv("RETRIEVAL_RRF_K", "60"))

    RERANK_ENABLED: bool = os.getenv("RETRIEVAL_RERANK_ENABLED", "true").lower() == "true"
    HIERARCHY_ENABLED: bool = os.getenv("RETRIEVAL_HIERARCHY_ENABLED", "true").lower() == "true"
    MMR_ENABLED: bool = os.getenv("RETRIEVAL_MMR_ENABLED", "true").lower() == "true"

    MMR_LAMBDA: float = float(os.getenv("RETRIEVAL_MMR_LAMBDA", "0.75"))
    NEIGHBOR_WINDOW: int = int(os.getenv("RETRIEVAL_NEIGHBOR_WINDOW", "1"))
    SIMILARITY_THRESHOLD: float = float(os.getenv("RETRIEVAL_SIMILARITY_THRESHOLD", "0.0"))

    TITLE_BOOST: float = float(os.getenv("RETRIEVAL_TITLE_BOOST", "0.20"))
    BREADCRUMB_BOOST: float = float(os.getenv("RETRIEVAL_BREADCRUMB_BOOST", "0.20"))
    TECHNICAL_TERM_BOOST: float = float(os.getenv("RETRIEVAL_TECHNICAL_TERM_BOOST", "0.10"))
    HIERARCHY_BOOST: float = float(os.getenv("RETRIEVAL_HIERARCHY_BOOST", "0.05"))

    V55_RANKING_ENABLED: bool = os.getenv("RETRIEVAL_V55_RANKING_ENABLED", "true").lower() == "true"
    V55_Q50_RECOVERY_ENABLED: bool = os.getenv("RETRIEVAL_V55_Q50_RECOVERY_ENABLED", "true").lower() == "true"

retrieval_settings = RetrievalSettings()
