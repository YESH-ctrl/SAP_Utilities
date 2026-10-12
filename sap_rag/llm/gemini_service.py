"""
Dedicated Google Gemini Generation Service for SAP Utilities RAG Pipeline (V5.5.1 Integration).

Provides grounded answer generation using the official google-genai SDK,
strict anti-hallucination prompts, context budget enforcement, robust error handling,
and automatic model fallback on temporary 503 capacity errors.
"""

import os
import time
import logging
from typing import List, Dict, Any, Optional, Tuple, Union

try:
    from google import genai
    from google.genai import types
    from google.genai.errors import APIError
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False
    genai = None
    types = None
    APIError = Exception

logger = logging.getLogger(__name__)

GROUNDING_SYSTEM_PROMPT = """You are an SAP Utilities documentation assistant.

Your job is to answer the user's question using ONLY the retrieved SAP Utilities documentation supplied in the context.

The retrieved documents are authoritative.

IMPORTANT ANSWERING RULES:

1. Answer the user's question directly. Do not begin answers with "Based on the retrieved documentation".
2. Do NOT simply summarize each document separately or write "From Document A...".
3. Synthesize information from multiple retrieved documents into one coherent answer whenever they describe different parts of the same process.
4. Identify the logical workflow or sequence described by the documentation.
5. If the question asks "how", "how do I", "steps", "procedure", "process", or similar wording, organize the answer as numbered steps whenever the retrieved documentation supports a sequence.
6. Preserve SAP terminology exactly where appropriate.
7. Do not invent missing steps, configuration values, transaction codes, or prerequisites.
8. Do not infer undocumented SAP behavior or rely on unsupported general knowledge.
9. Every procedural statement must be supported by the retrieved documentation.
10. If multiple documents describe different stages of the same process, combine them into a single end-to-end explanation.
11. If the retrieved documentation is insufficient to establish the complete procedure, clearly state: "The retrieved SAP Utilities documentation does not provide enough information to answer this completely."
12. Do not mention RRF, embeddings, retrieval scores, ranking, candidate generation, or internal system architecture.
13. Avoid unnecessary repetition and use concise technical language.

FOR PROCEDURAL QUESTIONS:
First determine whether the retrieved documents describe multiple stages of a workflow. If they do:
- Arrange the stages logically.
- Explain prerequisites before actions where the documentation supports them.
- Explain triggering events where applicable.
- Explain the actual operational action.
- Explain confirmation/completion steps.
- Include relevant SAP-specific activities."""

NO_CONTEXT_FALLBACK = "I couldn't find sufficient supporting SAP Utilities documentation to answer this confidently."
ERROR_FALLBACK = "Answer generation is temporarily unavailable. The retrieved SAP documentation is still available below."

DEFAULT_FALLBACK_MODELS = ["gemini-3.5-flash", "gemini-3.6-flash", "gemini-3.1-flash-lite", "gemini-flash-latest"]

class GeminiService:
    """
    Service abstraction for Google Gemini answer generation using google-genai SDK.
    Reuses a single client instance for performance and provides strict grounding & bounds.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: Optional[str] = None,
        temperature: Optional[float] = None,
        max_output_tokens: Optional[int] = None,
        max_context_chunks: Optional[int] = None,
        max_context_chars: Optional[int] = None
    ):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        self.model_name = model_name or os.getenv("GEMINI_MODEL", "gemini-3.5-flash")

        try:
            temp_env = os.getenv("GEMINI_TEMPERATURE", "0.2")
            self.temperature = float(temperature if temperature is not None else temp_env)
        except ValueError:
            self.temperature = 0.2

        try:
            tokens_env = os.getenv("GEMINI_MAX_OUTPUT_TOKENS", "2048")
            self.max_output_tokens = int(max_output_tokens if max_output_tokens is not None else tokens_env)
        except ValueError:
            self.max_output_tokens = 2048

        try:
            chunks_env = os.getenv("MAX_CONTEXT_CHUNKS", "10")
            self.max_context_chunks = int(max_context_chunks if max_context_chunks is not None else chunks_env)
        except ValueError:
            self.max_context_chunks = 10

        try:
            chars_env = os.getenv("MAX_CONTEXT_CHARACTERS", "12000")
            self.max_context_chars = int(max_context_chars if max_context_chars is not None else chars_env)
        except ValueError:
            self.max_context_chars = 12000

        self._client = None
        self._init_client()

    def _init_client(self):
        """Initialize Google GenAI client without making any network calls at startup."""
        if not GENAI_AVAILABLE:
            logger.warning("google-genai package is not installed. GeminiService disabled.")
            return

        if not self.api_key or not self.api_key.strip():
            logger.warning("GEMINI_API_KEY is not configured. Gemini answer generation disabled.")
            return

        try:
            self._client = genai.Client(api_key=self.api_key)
            logger.info(f"GeminiService client initialized cleanly with model '{self.model_name}'.")
        except Exception as e:
            logger.error(f"Failed to initialize Gemini Client: {e}")
            self._client = None

    def is_configured(self) -> bool:
        """Check if Gemini API key and client are configured."""
        return bool(self.api_key and self._client is not None)

    def format_grounding_context(self, retrieved_context: List[Any]) -> Tuple[str, int]:
        """
        Construct formatted grounding context from retrieved candidate chunks.
        Respects MAX_CONTEXT_CHUNKS and MAX_CONTEXT_CHARACTERS budget without altering V5.5.1 retrieval.
        Returns Tuple[formatted_context_string, chunks_included_count].
        """
        if not retrieved_context:
            return "", 0

        chunks = retrieved_context[:self.max_context_chunks]
        context_blocks = []
        total_chars = 0
        chunks_included = 0

        for idx, item in enumerate(chunks, 1):
            if isinstance(item, dict):
                title = item.get("title") or f"Document {item.get('document_id', idx)}"
                doc_id = item.get("document_id", "N/A")
                path = item.get("breadcrumb") or item.get("path") or ""
                url = item.get("url", "")
                content = (item.get("content") or "").strip()
            else:
                title = getattr(item, "title", None) or f"Document {getattr(item, 'document_id', idx)}"
                doc_id = getattr(item, "document_id", "N/A")
                path = getattr(item, "breadcrumb", "") or getattr(item, "path", "")
                url = getattr(item, "url", "")
                content = (getattr(item, "content", "") or "").strip()

            if not content:
                continue

            block = (
                f"[DOCUMENT {idx}]\n"
                f"Title: {title}\n"
                f"Document ID: {doc_id}\n"
                f"Path: {path}\n"
                f"URL: {url}\n"
                f"Content:\n{content}\n"
            )

            if total_chars + len(block) > self.max_context_chars and chunks_included > 0:
                logger.info(f"Context character budget limit reached ({total_chars} chars). Truncating remaining chunks.")
                break

            context_blocks.append(block)
            total_chars += len(block)
            chunks_included += 1

        formatted_str = "\n----------------------------------------\n".join(context_blocks)
        return formatted_str, chunks_included

    async def generate_answer(
        self,
        question: str,
        retrieved_context: List[Any],
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> Tuple[str, Dict[str, Any]]:
        """
        Generate grounded answer from retrieved context and conversation history using Gemini LLM.

        Returns Tuple[answer_text, latency_metadata].
        """
        build_start = time.perf_counter()

        if not retrieved_context:
            build_ms = round((time.perf_counter() - build_start) * 1000, 2)
            return NO_CONTEXT_FALLBACK, {
                "context_build_ms": build_ms,
                "generation_ms": 0.0,
                "chunks_used": 0,
                "status": "no_context"
            }

        context_str, chunks_used = self.format_grounding_context(retrieved_context)
        build_ms = round((time.perf_counter() - build_start) * 1000, 2)

        if not context_str.strip():
            return NO_CONTEXT_FALLBACK, {
                "context_build_ms": build_ms,
                "generation_ms": 0.0,
                "chunks_used": 0,
                "status": "empty_context"
            }

        if not self.is_configured():
            logger.warning("Gemini API Key missing or client unconfigured. Returning error fallback.")
            return ERROR_FALLBACK, {
                "context_build_ms": build_ms,
                "generation_ms": 0.0,
                "chunks_used": chunks_used,
                "status": "unconfigured"
            }

        gen_start = time.perf_counter()

        # Format conversation history string
        hist_str = ""
        if conversation_history:
            recent_hist = [m for m in conversation_history if m.get("content") != question][-6:]
            if recent_hist:
                formatted_msgs = []
                for m in recent_hist:
                    role_name = "User" if m.get("role") == "user" else "Assistant"
                    formatted_msgs.append(f"{role_name}: {m.get('content')}")
                hist_str = "PREVIOUS CONVERSATION:\n" + "\n".join(formatted_msgs) + "\n\n"

        prompt = (
            f"{hist_str}"
            f"RETRIEVED SAP UTILITIES DOCUMENTATION CONTEXT:\n\n{context_str}\n\n"
            f"USER QUESTION:\n{question}"
        )

        config = types.GenerateContentConfig(
            system_instruction=GROUNDING_SYSTEM_PROMPT,
            temperature=self.temperature,
            max_output_tokens=self.max_output_tokens
        )

        # Candidates to try: primary configured model first, followed by fallbacks
        candidate_models = [self.model_name]
        for m in DEFAULT_FALLBACK_MODELS:
            if m not in candidate_models:
                candidate_models.append(m)

        last_error = None
        for target_model in candidate_models:
            try:
                response = await self._client.aio.models.generate_content(
                    model=target_model,
                    contents=prompt,
                    config=config
                )

                gen_ms = round((time.perf_counter() - gen_start) * 1000, 2)

                if response and response.text and response.text.strip():
                    return response.text.strip(), {
                        "context_build_ms": build_ms,
                        "generation_ms": gen_ms,
                        "chunks_used": chunks_used,
                        "status": "success",
                        "model": target_model
                    }
                else:
                    logger.warning(f"Gemini model '{target_model}' returned empty text or safety-blocked response.")
            except APIError as e:
                last_error = e
                code = getattr(e, "code", 0)
                logger.warning(f"Gemini APIError ({code}) with model '{target_model}': {getattr(e, 'message', str(e))}")
                if code in (503, 429, 404):
                    logger.info(f"Retrying generation with alternate Gemini model...")
                    continue
                break
            except Exception as e:
                last_error = e
                logger.error(f"Gemini generation exception with model '{target_model}': {e}")
                break

        gen_ms = round((time.perf_counter() - gen_start) * 1000, 2)
        return ERROR_FALLBACK, {
            "context_build_ms": build_ms,
            "generation_ms": gen_ms,
            "chunks_used": chunks_used,
            "status": "api_error" if isinstance(last_error, APIError) else "error",
            "error": str(last_error) if last_error else "Unknown error"
        }
