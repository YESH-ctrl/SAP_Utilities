from sap_rag.embeddings.config import embedding_settings
from sap_rag.embeddings.service import EmbeddingModelService

__all__ = ["embedding_settings", "EmbeddingModelService", "EmbeddingPipeline"]

def __getattr__(name: str):
    if name == "EmbeddingPipeline":
        from sap_rag.embeddings.pipeline import EmbeddingPipeline
        return EmbeddingPipeline
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

