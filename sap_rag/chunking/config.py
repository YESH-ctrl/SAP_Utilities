"""
Configuration settings for the SAP Utilities Semantic Chunking Engine.
"""

from pydantic import BaseModel, Field

class ChunkingConfig(BaseModel):
    # Chunking Version
    CHUNKING_VERSION: str = "semantic-v1"

    # Token Targets (Guidelines)
    TARGET_MIN_TOKENS: int = 500
    TARGET_MAX_TOKENS: int = 800
    PREFERRED_TOKENS: int = 650
    HARD_MAX_TOKENS: int = 900
    MIN_SECTION_TOKENS: int = 30

    # Overlap Target
    TARGET_OVERLAP_TOKENS: int = 85  # Range: 75-100

    # Tokenizer Model Name
    TOKENIZER_MODEL_NAME: str = "BAAI/bge-m3"

    # Content Format
    ENABLE_METADATA_HEADER: bool = True

chunking_settings = ChunkingConfig()
