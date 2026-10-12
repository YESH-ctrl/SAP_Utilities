"""
Tokenizer component for accurate token counting using BAAI/bge-m3.
"""

import logging
from typing import Optional
from sap_rag.chunking.config import chunking_settings

logger = logging.getLogger(__name__)

import functools

@functools.lru_cache(maxsize=32768)
def _fast_encode_count(tokenizer, text: str) -> int:
    return len(tokenizer.encode(text, add_special_tokens=False, verbose=False))

class SemanticTokenizer:
    """
    Tokenizer wrapper for counting tokens with BAAI/bge-m3 tokenizer.
    Falls back to a word ratio estimator if HuggingFace tokenizer fails to load.
    """
    _instance: Optional["SemanticTokenizer"] = None

    def __init__(self, model_name: str = chunking_settings.TOKENIZER_MODEL_NAME):
        self.model_name = model_name
        self.tokenizer = None
        self._load_tokenizer()

    def _load_tokenizer(self):
        try:
            from transformers import AutoTokenizer
            logger.info(f"Loading tokenizer: {self.model_name}")
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name, trust_remote_code=True)
            self.tokenizer.model_max_length = 8192
            self.tokenizer.truncation_side = "right"
            logger.info("Tokenizer loaded successfully.")
        except Exception as e:
            logger.warning(f"Could not load HuggingFace tokenizer '{self.model_name}': {e}. Using word-ratio fallback estimation.")
            self.tokenizer = None

    @classmethod
    def get_instance(cls, model_name: str = chunking_settings.TOKENIZER_MODEL_NAME) -> "SemanticTokenizer":
        if cls._instance is None:
            cls._instance = SemanticTokenizer(model_name=model_name)
        return cls._instance

    def count_tokens(self, text: str) -> int:
        """
        Count tokens in a text string.
        """
        if not text:
            return 0

        if self.tokenizer:
            try:
                return _fast_encode_count(self.tokenizer, text)
            except Exception as e:
                logger.debug(f"Tokenization error: {e}. Falling back to estimate.")

        # Fallback estimation: 1 word ~ 1.3 tokens for English/SAP technical text
        words = text.split()
        return max(1, int(len(words) * 1.3))

    def truncate_tokens(self, text: str, max_tokens: int) -> str:
        """
        Truncate text to fit within max_tokens.
        """
        if self.count_tokens(text) <= max_tokens:
            return text

        if self.tokenizer:
            tokens = self.tokenizer.encode(text, add_special_tokens=False)[:max_tokens]
            return self.tokenizer.decode(tokens)

        # Fallback word-level truncation
        words = text.split()
        max_words = int(max_tokens / 1.3)
        return " ".join(words[:max_words])

TokenizerWrapper = SemanticTokenizer
