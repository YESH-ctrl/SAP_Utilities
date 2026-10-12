"""
Configuration settings for BAAI/bge-m3 Embedding Engine.
"""

import os
from pydantic_settings import BaseSettings

class EmbeddingSettings(BaseSettings):
    EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "BAAI/bge-m3")
    EMBEDDING_MODEL_VERSION: str = os.getenv("EMBEDDING_MODEL_VERSION", "1.0")
    EMBEDDING_DIMENSION: int = int(os.getenv("EMBEDDING_DIMENSION", "1024"))
    MAX_INPUT_TOKENS: int = int(os.getenv("MAX_INPUT_TOKENS", "8192"))
    BATCH_SIZE: int = int(os.getenv("EMBEDDING_BATCH_SIZE", os.getenv("BATCH_SIZE", "16")))
    DEVICE: str = os.getenv("EMBEDDING_DEVICE", "")
    MODEL_KEY: str = os.getenv("EMBEDDING_MODEL_KEY", "BGE-M3")

embedding_settings = EmbeddingSettings()

# Module-level exports for direct import compatibility
EMBEDDING_MODEL = embedding_settings.EMBEDDING_MODEL
EMBEDDING_MODEL_VERSION = embedding_settings.EMBEDDING_MODEL_VERSION
EMBEDDING_DIMENSION = embedding_settings.EMBEDDING_DIMENSION
MAX_INPUT_TOKENS = embedding_settings.MAX_INPUT_TOKENS
BATCH_SIZE = embedding_settings.BATCH_SIZE

