"""
Evidence Context Builder for Agentic Intelligence Platform.
Enforces model context budgets, stable chunk ID deduplication, and safe request-time excerpts.
Preserves exact character and token offsets without database mutation.
"""

import os
import re
import logging
from typing import List, Tuple, Dict, Any
from sap_rag.agentic.schemas.contracts import EvidenceItem

logger = logging.getLogger("sap_rag.agentic.retrieval.context_builder")

# Maximum token budget for context assembly (configurable via env)
DEFAULT_MAX_CONTEXT_TOKENS = int(os.getenv("AGENTIC_MAX_CONTEXT_TOKENS", "6000"))
DEFAULT_MAX_CHUNK_CHARS = int(os.getenv("AGENTIC_MAX_CHUNK_CHARS", "2400"))



def parse_chunk_components(raw_text: str) -> Dict[str, str]:
    """
    Parses SAP Utilities stored chunk metadata headers:
    [DOCUMENT], [PATH], [SECTION], and [CONTENT].
    Extracts clean body text without losing stored content.
    """
    if not raw_text:
        return {"document": "", "path": "", "section": "", "body": ""}

    text = re.sub(r"[\uE000-\uF8FF\uFFF0-\uFFFF]", "", raw_text).strip()
    components = {"document": "", "path": "", "section": "", "body": text}

    if "[CONTENT]" in text:
        header_part, body_part = text.split("[CONTENT]", 1)
        components["body"] = body_part.strip()

        if "[DOCUMENT]" in header_part:
            doc_part = header_part.split("[DOCUMENT]", 1)[1]
            if "[PATH]" in doc_part:
                components["document"] = doc_part.split("[PATH]", 1)[0].strip()
            elif "[SECTION]" in doc_part:
                components["document"] = doc_part.split("[SECTION]", 1)[0].strip()
            else:
                components["document"] = doc_part.strip()

        if "[PATH]" in header_part:
            path_part = header_part.split("[PATH]", 1)[1]
            if "[SECTION]" in path_part:
                components["path"] = path_part.split("[SECTION]", 1)[0].strip()
            else:
                components["path"] = path_part.strip()

        if "[SECTION]" in header_part:
            sec_part = header_part.split("[SECTION]", 1)[1]
            components["section"] = sec_part.strip()

    return components


def create_clean_excerpt(body: str, max_chars: int = 400) -> Tuple[str, int, int, bool]:
    """
    Derive safe, clean excerpt on word/sentence boundaries.
    Never slices mid-word, never includes incomplete structural tags like [CONT.
    Returns: (excerpt_text, char_offset_start, char_offset_end, is_excerpted)
    """
    if not body:
        return "", 0, 0, False

    clean = body.strip()
    if len(clean) <= max_chars:
        return clean, 0, len(clean), False

    cut = clean[:max_chars]
    last_break = cut.rfind("\n\n")
    if last_break < int(max_chars * 0.6):
        last_break = cut.rfind(". ")
        if last_break != -1:
            last_break += 1  # include the period
    if last_break < int(max_chars * 0.6):
        last_break = cut.rfind(" ")

    if last_break > int(max_chars * 0.5):
        excerpt = clean[:last_break].rstrip(" ,;-:–—") + "..."
        return excerpt, 0, last_break, True
    else:
        excerpt = cut.rstrip(" ,;-:–—") + "..."
        return excerpt, 0, len(cut), True


class EvidenceContextBuilder:
    """
    Deterministic context assembly and safe request-time excerpt manager.
    """

    def __init__(
        self,
        max_context_tokens: int = DEFAULT_MAX_CONTEXT_TOKENS,
        max_chunk_chars: int = DEFAULT_MAX_CHUNK_CHARS
    ):
        self.max_context_tokens = max_context_tokens
        self.max_chunk_chars = max_chunk_chars

    @staticmethod
    def clean_unicode(text: str) -> str:
        """Strip SAP Help Portal icon font symbols and unprintable private use characters."""
        if not text:
            return ""
        return re.sub(r"[\uE000-\uF8FF\uFFF0-\uFFFF]", "", text).strip()

    def create_safe_excerpt(self, item: EvidenceItem) -> EvidenceItem:
        """
        Derive request-time excerpt from stored chunk if oversized.
        Preserves original stable chunk ID, source metadata, and sets exact char_offset_start/end.
        Extracts clean body text stripped of metadata headers.
        """
        raw_content = item.content or ""
        cleaned = self.clean_unicode(raw_content)
        comp = parse_chunk_components(cleaned)

        clean_body = comp["body"] or cleaned
        clean_exc, off_start, off_end, is_exc = create_clean_excerpt(clean_body, max_chars=360)

        # Update metadata if not present on item
        path = item.section_path
        if (not path or path.startswith("Depth")) and comp["path"]:
            path = comp["path"]

        heading = item.section_heading
        if not heading and comp["section"]:
            heading = comp["section"]

        if len(cleaned) <= self.max_chunk_chars:
            return item.model_copy(update={
                "content": cleaned,
                "clean_body": clean_body,
                "clean_excerpt": clean_exc,
                "section_path": path,
                "section_heading": heading,
                "char_offset_start": 0,
                "char_offset_end": len(cleaned),
                "is_excerpted": False
            })

        # Excerpting needed for oversized chunk
        target_body_len = max(300, self.max_chunk_chars)
        bounded_body, _, cut_end, _ = create_clean_excerpt(clean_body, max_chars=target_body_len)
        excerpt_text = bounded_body + " [Passage excerpted for context budget]"
        token_estimate = int(len(excerpt_text.split()) * 1.3)

        return item.model_copy(update={
            "content": excerpt_text,
            "clean_body": clean_body,
            "clean_excerpt": clean_exc,
            "section_path": path,
            "section_heading": heading,
            "char_offset_start": 0,
            "char_offset_end": cut_end,
            "is_excerpted": True,
            "token_count": token_estimate
        })

    def deduplicate_and_build(
        self,
        evidence_items: List[EvidenceItem]
    ) -> Tuple[List[EvidenceItem], str, Dict[str, Any]]:
        """
        Deduplicate candidates by stable chunk ID, generate safe excerpts, and assemble formatted context.
        Returns:
            - Deduplicated EvidenceItem list
            - Assembled grounded prompt context string
            - Context metrics dictionary
        """
        seen_chunk_ids = set()
        deduped_items: List[EvidenceItem] = []
        total_tokens = 0
        excerpt_count = 0

        # Prioritize procedural, prerequisite, use, and results chunks first
        def _evidence_priority(itm: EvidenceItem) -> Tuple[int, float]:
            h = (itm.section_heading or "").lower()
            is_proc = any(k in h for k in ("procedure", "prerequisite", "scope", "result", "use", "feature", "how to", "activit"))
            # Sort primary by procedural relevance (0 before 1), secondary by similarity score (descending)
            return (0 if is_proc else 1, -float(itm.similarity_score or 0.0))

        sorted_candidates = sorted(evidence_items, key=_evidence_priority)

        for raw_item in sorted_candidates:
            if raw_item.chunk_id in seen_chunk_ids:
                continue
            seen_chunk_ids.add(raw_item.chunk_id)

            safe_item = self.create_safe_excerpt(raw_item)
            if safe_item.is_excerpted:
                excerpt_count += 1

            est_tokens = safe_item.token_count or int(len(safe_item.content.split()) * 1.3)
            if total_tokens + est_tokens > self.max_context_tokens and len(deduped_items) >= 4:
                # Stop adding chunks once budget is exceeded, ensuring at least 4 chunks
                logger.info(f"Context budget reached ({total_tokens} tokens). Capped at {len(deduped_items)} items.")
                break

            total_tokens += est_tokens
            deduped_items.append(safe_item)

        # Assemble clean structured context
        context_blocks = []
        for idx, itm in enumerate(deduped_items, 1):
            body_text = itm.clean_body or itm.content
            block = (
                f"--- EVIDENCE [{idx}] ---\n"
                f"EVIDENCE_ID: {itm.evidence_id}\n"
                f"CHUNK_ID: {itm.chunk_id}\n"
                f"DOCUMENT_ID: {itm.document_id}\n"
                f"TITLE: {itm.title}\n"
                f"PATH: {itm.section_path or 'General'}\n"
                f"HEADING: {itm.section_heading or 'General'}\n"
                f"CANONICAL_URL: {itm.canonical_url}\n"
                f"SIMILARITY: {itm.similarity_score}\n"
                f"CONTENT:\n{body_text}\n"
            )
            context_blocks.append(block)

        assembled_str = "\n".join(context_blocks)
        metrics = {
            "total_items": len(deduped_items),
            "total_estimated_tokens": total_tokens,
            "excerpted_items_count": excerpt_count,
            "context_char_length": len(assembled_str),
            "max_budget_tokens": self.max_context_tokens
        }

        return deduped_items, assembled_str, metrics
