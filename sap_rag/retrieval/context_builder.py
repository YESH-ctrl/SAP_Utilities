"""
Context Builder component formatting retrieval candidates into structured LLM context blocks with provenance.
Also provides RAG system prompt contract templates.
"""

from typing import List
from sap_rag.retrieval.models import RetrievalCandidate, ProcessedQuery

RAG_SYSTEM_PROMPT_TEMPLATE = """You are an expert SAP Utilities documentation assistant.

Answer the user's question using ONLY the retrieved SAP Utilities documentation context provided below.

STRICT RAG CONSTRAINTS:
1. Do not invent or hallucinate SAP transaction codes, configuration steps, APIs, parameters, business rules, or technical procedures.
2. If the retrieved documentation does not contain enough information to answer the question completely, explicitly state that the indexed SAP Utilities documentation does not provide enough information.
3. Always cite supporting SAP documentation sources (e.g., Document Title, Section, or SAP Help URL) when providing answers.

RETRIEVED SAP UTILITIES DOCUMENTATION CONTEXT:
{context_text}
"""

class ContextBuilder:
    """
    Formats retrieval candidates into clean, structured prompt context blocks for RAG LLM generation.
    """

    @classmethod
    def build_context(cls, candidates: List[RetrievalCandidate]) -> str:
        if not candidates:
            return "No relevant SAP Utilities documentation chunks retrieved."

        blocks = []
        for i, c in enumerate(candidates, 1):
            block_lines = [
                f"--- SOURCE ITEM [{i}] ---",
                f"Source ID: #{c.source_id}" if c.source_id else "Source: Reference Documentation",
                f"Document Title: {c.title}",
                f"Breadcrumb: {c.breadcrumb}" if c.breadcrumb else f"Document ID: {c.document_id}",
                f"SAP Help URL: {c.url}" if c.url else "",
                f"Chunk ID: #{c.chunk_id}",
                f"Relevance Score: {round(c.final_score, 4)}",
                "Content:",
                c.content.strip(),
                ""
            ]
            blocks.append("\n".join(line for line in block_lines if line is not None))

        return "\n".join(blocks)

    @classmethod
    def build_rag_prompt(cls, query: str, candidates: List[RetrievalCandidate]) -> str:
        context_text = cls.build_context(candidates)
        return RAG_SYSTEM_PROMPT_TEMPLATE.format(context_text=context_text) + f"\nUSER QUESTION: {query}\nANSWER:"
