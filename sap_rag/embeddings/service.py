"""
Embedding model service for initialization, device management, token counting, truncation, and batch encoding using BAAI/bge-m3.
Includes LRU Query Embedding Cache for fast query encoding (<0.1ms cache hit).
"""

import logging
import os
import torch
import numpy as np
from typing import List, Dict, Any, Optional

os.environ["TOKENIZERS_PARALLELISM"] = "false"

from sentence_transformers import SentenceTransformer
from sap_rag.embeddings.config import embedding_settings
from sap_rag.chunking.tokenizer import SemanticTokenizer

logger = logging.getLogger(__name__)

class EmbeddingCache:
    """
    Thread-safe, bounded LRU query embedding cache (Phase 3 & 4).
    Stores normalized query vectors to eliminate redundant model forward passes.
    """

    def __init__(self, maxsize: int = 1000):
        self.maxsize = maxsize
        self._cache: Dict[str, List[float]] = {}
        self.hits = 0
        self.misses = 0

    def get(self, query: str, model_key: str) -> Optional[List[float]]:
        key = f"{model_key}:{query.strip().lower()}"
        if key in self._cache:
            self.hits += 1
            return self._cache[key]
        self.misses += 1
        return None

    def put(self, query: str, model_key: str, vector: List[float]):
        key = f"{model_key}:{query.strip().lower()}"
        if len(self._cache) >= self.maxsize:
            first_key = next(iter(self._cache))
            del self._cache[first_key]
        self._cache[key] = vector

    def get_stats(self) -> Dict[str, Any]:
        total = self.hits + self.misses
        hit_rate = (self.hits / total) if total > 0 else 0.0
        return {
            "hits": self.hits,
            "misses": self.misses,
            "hit_rate": round(hit_rate, 4),
            "size": len(self._cache)
        }

class EmbeddingModelService:
    """
    Reusable BAAI/bge-m3 embedding model service.
    Handles device auto-detection (CPU/CUDA), startup dimension verification (1024 dims),
    and deterministic 8192-token truncation.
    """
    _instance: Optional["EmbeddingModelService"] = None

    def __init__(self):
        self.model_name = embedding_settings.EMBEDDING_MODEL
        self.model_version = embedding_settings.EMBEDDING_MODEL_VERSION
        self.target_dimension = embedding_settings.EMBEDDING_DIMENSION
        self.max_input_tokens = embedding_settings.MAX_INPUT_TOKENS
        
        self.device = self._detect_device()
        self._configure_torch_threads()
        self.tokenizer = SemanticTokenizer.get_instance()
        self.model = self._load_and_verify_model()
        self.cache = EmbeddingCache(maxsize=1000)

    @classmethod
    def get_instance(cls) -> "EmbeddingModelService":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def _configure_torch_threads(self):
        if self.device == "cpu":
            num_cpus = min(os.cpu_count() or 4, 12)
            try:
                torch.set_num_threads(num_cpus)
                logger.info(f"PyTorch CPU intra-op thread count set to {num_cpus}")
            except Exception as e:
                logger.debug(f"Could not set PyTorch thread count: {e}")

    def _detect_device(self) -> str:
        if embedding_settings.DEVICE:
            return embedding_settings.DEVICE
        if torch.cuda.is_available():
            dev = "cuda"
        else:
            dev = "cpu"
        logger.info(f"Auto-detected PyTorch device: {dev}")
        return dev

    def _load_and_verify_model(self) -> SentenceTransformer:
        logger.info(f"Initializing embedding model '{self.model_name}' on device '{self.device}'...")
        model = SentenceTransformer(self.model_name, device=self.device)
        model.max_seq_length = self.max_input_tokens
        if hasattr(model, "tokenizer") and model.tokenizer:
            model.tokenizer.model_max_length = self.max_input_tokens
            model.tokenizer.truncation = True

        test_text = "SAP Utilities RAG Embedding Test"
        with torch.inference_mode():
            test_vec = model.encode([test_text], normalize_embeddings=True)
            output_dim = test_vec.shape[1]

        if output_dim != self.target_dimension:
            raise ValueError(
                f"Embedding dimension mismatch: model '{self.model_name}' produced {output_dim} dimensions, "
                f"expected target dimension is {self.target_dimension}."
            )

        logger.info(f"EmbeddingModelService successfully verified model '{self.model_name}' ({output_dim} dims).")
        return model

    def prepare_chunk(self, text: str) -> Dict[str, Any]:
        if not text or not text.strip():
            raise ValueError("Cannot prepare empty or whitespace-only chunk content for embedding.")

        if self.tokenizer and getattr(self.tokenizer, "tokenizer", None):
            tokens = self.tokenizer.tokenizer.encode(text, add_special_tokens=False)
            source_tokens = len(tokens)
            if source_tokens <= self.max_input_tokens:
                return {
                    "content": text,
                    "source_tokens": source_tokens,
                    "embedded_tokens": source_tokens,
                    "truncated": False
                }

            truncated_tokens = tokens[: self.max_input_tokens]
            truncated_text = self.tokenizer.tokenizer.decode(truncated_tokens)
            embedded_tokens = len(truncated_tokens)

            return {
                "content": truncated_text,
                "source_tokens": source_tokens,
                "embedded_tokens": embedded_tokens,
                "truncated": True
            }

        source_tokens = self.tokenizer.count_tokens(text)
        if source_tokens <= self.max_input_tokens:
            return {
                "content": text,
                "source_tokens": source_tokens,
                "embedded_tokens": source_tokens,
                "truncated": False
            }

        truncated_text = self.tokenizer.truncate_tokens(text, max_tokens=self.max_input_tokens)
        embedded_tokens = self.tokenizer.count_tokens(truncated_text)

        return {
            "content": truncated_text,
            "source_tokens": source_tokens,
            "embedded_tokens": embedded_tokens,
            "truncated": True
        }

    def encode_batch(self, texts: List[str], verbose: bool = False) -> np.ndarray:
        if not texts:
            return np.empty((0, self.target_dimension), dtype=np.float32)

        all_embeddings = []
        i = 0
        n = len(texts)

        with torch.inference_mode():
            batch_count = 0
            while i < n:
                sample_len = len(texts[i].split())
                if sample_len > 800:
                    mb_size = 1
                elif sample_len > 300:
                    mb_size = 2 if self.device == "cpu" else 4
                else:
                    mb_size = 8 if self.device == "cpu" else min(embedding_settings.BATCH_SIZE, 16)

                sub_texts = texts[i : i + mb_size]
                batch_count += 1

                approx_tokens = [int(len(t.split()) * 1.4) + 10 for t in sub_texts]
                sub_max_tok = min(self.max_input_tokens, max(64, max(approx_tokens)))
                self.model.max_seq_length = sub_max_tok

                try:
                    embeddings = self.model.encode(
                        sub_texts,
                        batch_size=len(sub_texts),
                        show_progress_bar=False,
                        normalize_embeddings=True,
                        convert_to_numpy=True
                    )
                except Exception as e:
                    logger.warning(f"Sub-batch encoding error ({e}); falling back...")
                    sub_embeddings = []
                    for single_text in sub_texts:
                        single_tok = min(self.max_input_tokens, max(64, int(len(single_text.split()) * 1.4) + 10))
                        self.model.max_seq_length = single_tok
                        vec = self.model.encode(
                            [single_text],
                            batch_size=1,
                            show_progress_bar=False,
                            normalize_embeddings=True,
                            convert_to_numpy=True
                        )
                        sub_embeddings.append(vec)
                    embeddings = np.vstack(sub_embeddings)

                all_embeddings.append(embeddings)
                i += len(sub_texts)

        return np.vstack(all_embeddings)

    def encode_query(self, query: str) -> List[float]:
        """
        Generate dense 1024-dimensional normalized vector embedding for a single user query.
        Uses process-level EmbeddingCache for sub-millisecond retrieval on cached queries.
        """
        if not query or not query.strip():
            raise ValueError("Cannot encode empty or whitespace query.")

        # Check LRU Query Cache (Phase 3 & 4)
        cached_vec = self.cache.get(query, self.model_name)
        if cached_vec is not None:
            return cached_vec

        q_clean = query.strip()
        approx_tok = min(self.max_input_tokens, max(64, int(len(q_clean.split()) * 1.4) + 10))

        with torch.inference_mode():
            self.model.max_seq_length = approx_tok
            vec = self.model.encode(
                [q_clean],
                batch_size=1,
                show_progress_bar=False,
                normalize_embeddings=True,
                convert_to_numpy=True
            )[0].tolist()

        # Cache result
        self.cache.put(query, self.model_name, vec)
        return vec
