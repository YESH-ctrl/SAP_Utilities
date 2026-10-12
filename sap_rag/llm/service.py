"""
LLM Generation & Grounded Context Service for SAP Utilities RAG Pipeline (V5.5.1 Integration Layer).

Delegates answer generation to GeminiService using official google-genai SDK
or deterministic fallback synthesizer when API keys are not configured.
"""

import os
import logging
from typing import List, Dict, Any, Optional, Tuple, Union
from sap_rag.retrieval.schemas import CandidateResultSchema
from sap_rag.llm.gemini_service import (
    GeminiService,
    GROUNDING_SYSTEM_PROMPT as SYSTEM_PROMPT,
    NO_CONTEXT_FALLBACK,
    ERROR_FALLBACK
)

logger = logging.getLogger(__name__)

class LLMService:
    """
    LLM Service abstraction for grounded answer generation.
    Wraps GeminiService with automatic fallback to deterministic grounded synthesizer.
    """

    def __init__(self, gemini_service: Optional[GeminiService] = None):
        self.provider = os.getenv("LLM_PROVIDER", "auto").lower()
        self.gemini_service = gemini_service or GeminiService()
        self.groq_api_key = (os.getenv("GROQ_API_KEY") or "").strip()
        self.groq_model = os.getenv("GROQ_MODEL", "qwen/qwen3.8-27b")
        logger.info(f"LLMService initialized with provider: '{self.provider}' (Gemini configured: {self.gemini_service.is_configured()}, Groq: {bool(self.groq_api_key)})")

    def format_context(self, candidates: List[CandidateResultSchema]) -> str:
        """
        Format retrieved candidate chunks into a structured grounded context string.
        """
        context_str, _ = self.gemini_service.format_grounding_context(candidates)
        return context_str

    async def generate_answer(
        self,
        query: str,
        candidates: List[CandidateResultSchema],
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> str:
        """
        Generate a grounded answer string based on query, candidate chunks, and conversation history.
        """
        ans, _ = await self.generate_answer_with_metadata(query, candidates, conversation_history)
        return ans

    async def _generate_groq(
        self,
        query: str,
        candidates: List[CandidateResultSchema],
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> Tuple[str, Dict[str, Any]]:
        """Generate answer via Groq LPU inference."""
        import time
        from openai import AsyncOpenAI

        t0 = time.perf_counter()
        context_str, chunks_used = self.gemini_service.format_grounding_context(candidates)
        t_ctx = (time.perf_counter() - t0) * 1000

        messages = [
            {"role": "system", "content": f"{SYSTEM_PROMPT}\n\nCONTEXT:\n{context_str}"}
        ]
        if conversation_history:
            for m in conversation_history:
                messages.append({"role": m.get("role", "user"), "content": m.get("content", "")})
        messages.append({"role": "user", "content": query})

        client = AsyncOpenAI(base_url="https://api.groq.com/openai/v1", api_key=self.groq_api_key)
        t1 = time.perf_counter()
        resp = await client.chat.completions.create(
            model=self.groq_model,
            messages=messages,
            temperature=0.2,
            max_tokens=2048
        )
        gen_ms = (time.perf_counter() - t1) * 1000
        ans = resp.choices[0].message.content or ""
        return ans, {
            "context_build_ms": t_ctx,
            "generation_ms": gen_ms,
            "chunks_used": chunks_used,
            "status": "success",
            "provider": "groq",
            "model": self.groq_model
        }

    async def generate_answer_with_metadata(
        self,
        query: str,
        candidates: List[CandidateResultSchema],
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> Tuple[str, Dict[str, Any]]:
        """
        Generate a grounded answer and return latency and context metadata.
        """
        if not candidates:
            return NO_CONTEXT_FALLBACK, {"context_build_ms": 0.0, "generation_ms": 0.0, "chunks_used": 0, "status": "no_candidates"}

        # Use Groq if provider is groq or if Groq is available and Gemini is not configured
        if self.groq_api_key and (self.provider == "groq" or not self.gemini_service.is_configured()):
            try:
                return await self._generate_groq(query, candidates, conversation_history)
            except Exception as e:
                logger.error(f"Groq answer generation failed: {e}. Falling back...")

        # Use GeminiService if configured
        if self.gemini_service.is_configured():
            ans, meta = await self.gemini_service.generate_answer(query, candidates, conversation_history)
            if meta.get("status") in ("api_error", "error"):
                logger.warning("Gemini call failed during generation. Returning fallback answer with sources preserved.")
            return ans, meta

        # Fallback synthesizer when all API keys are missing or failed
        logger.info("External LLM service is unconfigured. Using deterministic synthesizer fallback.")
        ans = self._generate_synthesizer(query, candidates, conversation_history)
        return ans, {"context_build_ms": 0.0, "generation_ms": 0.0, "chunks_used": len(candidates), "status": "synthesizer_fallback"}

    def _extract_body_text(self, content: str) -> str:
        """
        Extract clean body text from chunk content by stripping metadata headers.
        """
        if not content:
            return ""
        if "[CONTENT]" in content:
            body = content.split("[CONTENT]", 1)[1].strip()
        else:
            lines = []
            for line in content.split("\n"):
                s = line.strip()
                if s.startswith(("[DOCUMENT]", "[PATH]", "[SECTION]")):
                    continue
                lines.append(s)
            body = "\n".join(lines).strip()

        import re
        body = re.sub(r"[\uE000-\uF8FF\uFFF0-\uFFFF]", "", body)
        return body

    def _generate_synthesizer(
        self,
        query: str,
        candidates: List[CandidateResultSchema],
        history: Optional[List[Dict[str, str]]] = None
    ) -> str:
        """
        Deterministic grounded synthesizer when no external LLM API key is configured.
        Extracts key sentences and grounded procedures from retrieved SAP documentation chunks.
        """
        top_candidates = candidates[:3]
        if not top_candidates:
            return NO_CONTEXT_FALLBACK

        paragraphs = []
        titles_used = set()

        for c in top_candidates:
            title = c.title or c.document_id
            if title in titles_used:
                continue
            titles_used.add(title)

            body_text = self._extract_body_text(c.content)
            if not body_text or len(body_text) < 20:
                continue

            body_lines = [line.strip() for line in body_text.split("\n") if line.strip()]
            formatted_body = "\n".join(body_lines[:8])

            paragraphs.append(f"**From {title}**:\n{formatted_body}")

        if not paragraphs:
            return NO_CONTEXT_FALLBACK

        response_text = f"Based on the retrieved SAP Utilities documentation:\n\n"
        response_text += "\n\n".join(paragraphs)
        response_text += "\n\n*This answer is synthesized directly from verified SAP Utilities documentation sources.*"

        return response_text
