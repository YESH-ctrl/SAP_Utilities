"""
API Pydantic Request and Response schemas for retrieval and chat endpoints (V5.5.1 Integration Layer).
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field, ConfigDict
from sap_rag.retrieval.models import ProcessedQuery

class RetrievalRequest(BaseModel):
    query: str = Field(..., min_length=1, description="User search query string")
    top_k: int = Field(default=8, ge=1, le=50, description="Final number of top chunks to return")
    dense_candidate_k: int = Field(default=40, ge=1, le=100, description="Number of dense vector candidates")
    lexical_candidate_k: int = Field(default=40, ge=1, le=100, description="Number of lexical candidates")
    rerank: bool = Field(default=True, description="Enable second-stage re-ranking")
    include_neighbors: bool = Field(default=True, description="Enable neighbor chunk expansion")
    source_ids: Optional[List[int]] = Field(default=None, description="Filter by specific source IDs")
    document_ids: Optional[List[int]] = Field(default=None, description="Filter by specific document IDs")
    dense_weight: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    lexical_weight: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    mmr_lambda: Optional[float] = Field(default=None, ge=0.0, le=1.0)

class CandidateResultSchema(BaseModel):
    rank: Optional[int] = None
    chunk_id: int
    document_id: int
    section_id: Optional[int] = None
    source_id: Optional[int] = None
    title: str
    url: str
    breadcrumb: str
    content: str
    score: float
    retrieval_method: str
    scores_breakdown: Dict[str, Any] = Field(default_factory=dict)

class RetrievalResponse(BaseModel):
    query: str
    processed_query: Optional[ProcessedQuery] = None
    results: List[CandidateResultSchema]
    formatted_context: str
    metadata: Dict[str, Any]

    model_config = ConfigDict(arbitrary_types_allowed=True)

class ChatRequest(BaseModel):
    message: Optional[str] = Field(default=None, description="User question or chat message")
    messages: Optional[List[Dict[str, Any]]] = Field(default=None, description="Optional list of conversation messages")
    conversation_id: Optional[str] = Field(default=None, description="Optional conversation ID for history tracking")
    top_k: int = Field(default=8, ge=1, le=50, description="Number of top retrieved context chunks for LLM grounding")

class ChatMessageSchema(BaseModel):
    role: str = Field(..., description="Role of message sender (user or assistant)")
    content: str = Field(..., description="Content of the message")

class SourceCitationSchema(BaseModel):
    rank: Optional[int] = None
    title: str
    document_id: int
    source_id: Optional[int] = None
    url: str
    breadcrumb: str = ""
    excerpt: str = ""
    content: str = ""
    score: float = 0.0

class ChatResponse(BaseModel):
    conversation_id: str
    message: ChatMessageSchema
    sources: List[SourceCitationSchema]
    metadata: Dict[str, Any]
