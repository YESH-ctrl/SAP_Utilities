"""
Data models and data structures for retrieval engine components (V4 Production Hardened).
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

class ProcessedQuery(BaseModel):
    original_query: str
    normalized_query: str
    expanded_query: str = ""
    keywords: List[str] = Field(default_factory=list)
    technical_terms: List[str] = Field(default_factory=list)
    acronyms: List[str] = Field(default_factory=list)
    entities: List[str] = Field(default_factory=list)
    actions: List[str] = Field(default_factory=list)
    objects: List[str] = Field(default_factory=list)
    intent: str = "general"
    domain: str = "general"
    retrieval_confidence: str = "HIGH"
    answerability: str = "ANSWERABLE"

class RetrievalCandidate(BaseModel):
    chunk_id: int
    document_id: int
    section_id: Optional[int] = None
    source_id: Optional[int] = None
    title: str = ""
    url: str = ""
    breadcrumb: str = ""
    content: str = ""
    token_count: int = 0
    content_hash: Optional[str] = None

    dense_score: float = 0.0
    lexical_score: float = 0.0
    hybrid_score: float = 0.0
    title_score: float = 0.0
    breadcrumb_score: float = 0.0
    technical_term_score: float = 0.0
    hierarchy_score: float = 0.0
    domain_match_score: float = 0.0
    intent_match_score: float = 0.0
    relevance_score: float = 0.0
    pre_rerank_score: float = 0.0
    rerank_score: Optional[float] = None
    rerank_delta: float = 0.0
    final_score: float = 0.0

    dense_rank: Optional[int] = None
    lexical_rank: Optional[int] = None
    is_protected: bool = False

    vector: Optional[List[float]] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    feature_breakdown: Dict[str, float] = Field(default_factory=dict)
    retrieval_method: str = "hybrid"
    is_neighbor: bool = False

    def to_summary_dict(self) -> Dict[str, Any]:
        return {
            "chunk_id": self.chunk_id,
            "document_id": self.document_id,
            "section_id": self.section_id,
            "source_id": self.source_id,
            "title": self.title,
            "url": self.url,
            "breadcrumb": self.breadcrumb,
            "content": self.content,
            "score": round(self.final_score, 4),
            "retrieval_method": self.retrieval_method,
            "is_protected": self.is_protected,
            "feature_breakdown": self.feature_breakdown or {
                "dense": round(self.dense_score, 4),
                "lexical": round(self.lexical_score, 4),
                "hybrid": round(self.hybrid_score, 4),
                "relevance": round(self.relevance_score, 4),
                "pre_rerank": round(self.pre_rerank_score, 4),
                "rerank": round(self.rerank_score, 4) if self.rerank_score is not None else None,
                "title_boost": round(self.title_score, 4),
                "breadcrumb_boost": round(self.breadcrumb_score, 4),
                "technical_term_boost": round(self.technical_term_score, 4),
            }
        }
