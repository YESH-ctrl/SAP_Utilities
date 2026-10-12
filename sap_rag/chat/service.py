"""
Chat Service Orchestration for SAP Utilities RAG Pipeline.

Manages conversation state, bounds history growth, coordinates frozen V5.5.1 retrieval
and Gemini grounded answer generation, and packages source citations and latency breakdown.
"""

import os
import uuid
import time
import logging
from typing import Dict, List, Any, Optional, Tuple
from asyncpg import Connection

from sap_rag.retrieval.schemas import (
    ChatRequest,
    ChatResponse,
    ChatMessageSchema,
    SourceCitationSchema,
    CandidateResultSchema
)
from sap_rag.retrieval.retrieval_pipeline import RetrievalPipeline
from sap_rag.llm.service import LLMService

logger = logging.getLogger(__name__)

DEFAULT_MAX_MESSAGES = 20

class ConversationStore:
    """
    In-memory session-based conversation state manager with bounded history limit.
    """

    def __init__(self, max_messages: int = DEFAULT_MAX_MESSAGES):
        self.max_messages = max_messages
        self._conversations: Dict[str, List[Dict[str, str]]] = {}

    def get_history(self, conversation_id: str) -> List[Dict[str, str]]:
        return self._conversations.get(conversation_id, [])

    def add_message(self, conversation_id: str, role: str, content: str):
        if conversation_id not in self._conversations:
            self._conversations[conversation_id] = []

        history = self._conversations[conversation_id]
        history.append({"role": role, "content": content})

        if len(history) > self.max_messages:
            self._conversations[conversation_id] = history[-self.max_messages:]

    def clear(self, conversation_id: str):
        if conversation_id in self._conversations:
            del self._conversations[conversation_id]

class ChatService:
    """
    Chat Service orchestrator connecting V5.5.1 RAG retrieval engine, LLM generation,
    and session conversation state.
    """

    def __init__(
        self,
        pipeline: Optional[RetrievalPipeline] = None,
        llm_service: Optional[LLMService] = None,
        max_conversation_messages: Optional[int] = None
    ):
        self.pipeline = pipeline or RetrievalPipeline()
        self.llm_service = llm_service or LLMService()

        max_msg = max_conversation_messages or int(os.getenv("MAX_CONVERSATION_MESSAGES", DEFAULT_MAX_MESSAGES))
        self.store = ConversationStore(max_messages=max_msg)
        logger.info(f"ChatService initialized with max_conversation_messages={max_msg}")

    @staticmethod
    def clean_unicode_artifacts(text: str) -> str:
        """
        Strip Private Use Area Unicode characters (U+E000 to U+F8FF, U+FFF0 to U+FFFF)
        such as SAP Help Portal icon font symbols (\ue088) that render as square boxes.
        """
        if not text:
            return ""
        import re
        cleaned = re.sub(r"[\uE000-\uF8FF\uFFF0-\uFFFF]", "", text)
        return cleaned.strip()

    @classmethod
    def build_smart_excerpt(cls, body_text: str, max_chars: int = 280) -> str:
        """
        Build a clean excerpt preview truncated cleanly at natural word boundaries.
        """
        if not body_text:
            return ""
        cleaned = cls.clean_unicode_artifacts(body_text)
        if len(cleaned) <= max_chars:
            return cleaned

        truncated = cleaned[:max_chars]
        min_cutoff = max(20, int(max_chars * 0.6))
        last_space = truncated.rfind(' ')
        if last_space >= min_cutoff:
            truncated = truncated[:last_space]

        truncated = truncated.rstrip(' ,;-:–—')
        return truncated + "..."

    def extract_unique_sources(self, candidates: List[CandidateResultSchema]) -> List[SourceCitationSchema]:
        """
        Extract unique sources from retrieval candidates, preserving top rank order.
        Source metadata is strictly owned by the backend retrieval engine.
        """
        seen_keys = set()
        sources = []

        for idx, c in enumerate(candidates, 1):
            key = c.document_id or c.title or c.source_id
            if key not in seen_keys:
                seen_keys.add(key)
                
                full_text = c.content or ""
                # Strip metadata header prefix to get clean body excerpt preview
                if "[CONTENT]" in full_text:
                    body_text = full_text.split("[CONTENT]", 1)[1].strip()
                else:
                    body_text = full_text

                excerpt = self.build_smart_excerpt(body_text, max_chars=280)
                clean_bc = self.clean_unicode_artifacts(c.breadcrumb or "")
                clean_title = self.clean_unicode_artifacts(c.title or f"SAP Document {c.document_id}")

                sources.append(
                    SourceCitationSchema(
                        rank=len(sources) + 1,
                        title=clean_title,
                        document_id=c.document_id,
                        source_id=c.source_id,
                        url=c.url or "",
                        breadcrumb=clean_bc,
                        excerpt=excerpt,
                        content=full_text,
                        score=round(c.score, 4)
                    )
                )

        return sources

    async def process_chat(
        self,
        conn: Connection,
        request: ChatRequest
    ) -> ChatResponse:
        """
        Orchestrate a complete chat turn with latency breakdown:
        1. Validate & normalize query
        2. Retrieve context via frozen V5.5.1 Retrieval Engine
        3. Format conversation history
        4. Generate grounded answer via Gemini LLM Service
        5. Append to conversation state
        6. Package sources & latency metadata
        """
        total_start = time.perf_counter()

        # 1. Query Validation
        v_start = time.perf_counter()
        user_message = request.message
        if not user_message and request.messages:
            last_msg = request.messages[-1]
            if isinstance(last_msg, dict):
                user_message = last_msg.get("content", "")
            elif hasattr(last_msg, "content"):
                user_message = getattr(last_msg, "content", "")

        user_message = (user_message or "").strip()
        query_validation_ms = round((time.perf_counter() - v_start) * 1000, 2)

        # 2. Conversation ID & History
        conv_id = request.conversation_id or str(uuid.uuid4())
        history = self.store.get_history(conv_id)

        # 3. Query Normalization & V5.5.1 Retrieval
        retrieval_start = time.perf_counter()
        candidates, context_str, processed_query, metrics = await self.pipeline.execute(
            conn=conn,
            query=user_message,
            top_k=request.top_k
        )
        retrieval_latency_ms = round((time.perf_counter() - retrieval_start) * 1000, 2)
        query_normalization_ms = round(getattr(metrics, "normalization_ms", 0.1), 2)

        # Map internal Candidates to Pydantic Schemas
        candidate_schemas = []
        for c in candidates:
            summary = c.to_summary_dict()
            breakdown = summary.get("scores_breakdown") or summary.get("feature_breakdown") or {}
            candidate_schemas.append(
                CandidateResultSchema(
                    chunk_id=c.chunk_id,
                    document_id=c.document_id,
                    section_id=c.section_id,
                    source_id=c.source_id,
                    title=c.title,
                    url=c.url,
                    breadcrumb=c.breadcrumb,
                    content=c.content,
                    score=round(c.final_score, 4),
                    retrieval_method=c.retrieval_method,
                    scores_breakdown=breakdown
                )
            )

        # 4. Grounded Gemini Generation
        gen_start = time.perf_counter()
        answer_text, gen_meta = await self.llm_service.generate_answer_with_metadata(
            query=user_message,
            candidates=candidate_schemas,
            conversation_history=history
        )
        total_gen_ms = round((time.perf_counter() - gen_start) * 1000, 2)

        context_build_ms = gen_meta.get("context_build_ms", 0.0)
        gemini_generation_ms = gen_meta.get("generation_ms", total_gen_ms)

        # 5. Update Bounded Session History
        self.store.add_message(conv_id, "user", user_message)
        self.store.add_message(conv_id, "assistant", answer_text)

        # 6. Source Attribution (Backend-owned)
        sources = self.extract_unique_sources(candidate_schemas)

        s_start = time.perf_counter()
        # Pre-serialization phase
        serialization_ms = round((time.perf_counter() - s_start) * 1000, 2)

        total_latency_ms = round((time.perf_counter() - total_start) * 1000, 2)

        metadata = {
            "retrieval_version": "5.5.1",
            "query_validation_ms": query_validation_ms,
            "query_normalization_ms": query_normalization_ms,
            "retrieval_latency_ms": retrieval_latency_ms,
            "context_build_ms": context_build_ms,
            "generation_latency_ms": gemini_generation_ms,
            "gemini_generation_ms": gemini_generation_ms,
            "serialization_ms": serialization_ms,
            "total_latency_ms": total_latency_ms,
            "candidate_count": len(candidates),
            "processed_query": processed_query.to_dict() if hasattr(processed_query, "to_dict") else str(processed_query),
            "model": gen_meta.get("model", os.getenv("GEMINI_MODEL", "gemini-2.5-flash"))
        }

        return ChatResponse(
            conversation_id=conv_id,
            message=ChatMessageSchema(
                role="assistant",
                content=answer_text
            ),
            sources=sources,
            metadata=metadata
        )
