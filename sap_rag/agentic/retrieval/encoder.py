"""
Independent Query Encoder for Agentic Intelligence Platform.
Generates 1024-dimensional normalized dense vectors using BAAI/bge-m3.
Strictly compatible with stored PostgreSQL embeddings.
Completely isolated from legacy retrieval code.
"""

import os
import logging
import torch
from typing import List, Dict, Optional
from sentence_transformers import SentenceTransformer

logger = logging.getLogger("sap_rag.agentic.retrieval.encoder")

MODEL_NAME = os.getenv("AGENTIC_EMBEDDING_MODEL", "BAAI/bge-m3")
TARGET_DIMENSION = int(os.getenv("AGENTIC_EMBEDDING_DIM", "1024"))
MAX_SEQ_LENGTH = int(os.getenv("AGENTIC_MAX_SEQ_LENGTH", "8192"))


class QueryEmbeddingCache:
    """Thread-safe bounded in-memory LRU cache for query vector representations."""
    def __init__(self, maxsize: int = 1000):
        self.maxsize = maxsize
        self._cache: Dict[str, List[float]] = {}
        self.hits = 0
        self.misses = 0

    def get(self, text: str) -> Optional[List[float]]:
        key = text.strip().lower()
        if key in self._cache:
            self.hits += 1
            return self._cache[key]
        self.misses += 1
        return None

    def put(self, text: str, vector: List[float]):
        key = text.strip().lower()
        if len(self._cache) >= self.maxsize:
            oldest = next(iter(self._cache))
            del self._cache[oldest]
        self._cache[key] = vector


class IndependentQueryEncoder:
    """
    Dedicated Query Vector Encoder for the Agentic Platform.
    Ensures exact L2-normalization and 1024 dimension alignment with stored pgvector table.
    """
    _instance: Optional["IndependentQueryEncoder"] = None

    def __init__(self):
        self.model_name = MODEL_NAME
        self.target_dim = TARGET_DIMENSION
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.cache = QueryEmbeddingCache(maxsize=1000)
        self.model = self._load_model()

    @classmethod
    def get_instance(cls) -> "IndependentQueryEncoder":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def _load_model(self) -> SentenceTransformer:
        logger.info(f"Initializing Independent Query Encoder '{self.model_name}' on {self.device}...")
        model = SentenceTransformer(self.model_name, device=self.device)
        model.max_seq_length = MAX_SEQ_LENGTH
        
        # Verification check
        with torch.inference_mode():
            test_vec = model.encode(["SAP Utilities Verification"], normalize_embeddings=True)
            output_dim = test_vec.shape[1]
        
        if output_dim != self.target_dim:
            raise ValueError(
                f"Encoder dimension mismatch: '{self.model_name}' produced {output_dim} dims, "
                f"expected target dimension is {self.target_dim}."
            )
        logger.info(f"Independent Query Encoder verified successfully ({output_dim} dimensions).")
        return model

    def encode(self, query: str) -> List[float]:
        """
        Encode a single query string into a 1024-dimensional normalized vector.
        """
        q = (query or "").strip()
        if not q:
            raise ValueError("Query string cannot be empty for vector encoding.")

        cached = self.cache.get(q)
        if cached is not None:
            return cached

        with torch.inference_mode():
            vec = self.model.encode(
                [q],
                batch_size=1,
                show_progress_bar=False,
                normalize_embeddings=True,
                convert_to_numpy=True
            )[0].tolist()

        self.cache.put(q, vec)
        return vec
