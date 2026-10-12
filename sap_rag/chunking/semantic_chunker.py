"""
Deterministic, structure-aware Semantic Chunker for SAP Utilities Documentation.
"""

import hashlib
import logging
import re
from typing import List, Dict, Any, Optional

from sap_rag.chunking.config import chunking_settings
from sap_rag.chunking.tokenizer import SemanticTokenizer
from sap_rag.chunking.normalizer import TextNormalizer
from sap_rag.chunking.structural_parser import StructuralParser, SemanticBlock, BlockType

logger = logging.getLogger(__name__)

class GeneratedChunk(dict):
    """
    Data structure representing a generated chunk ready for persistence.
    """
    pass

class SemanticChunker:
    """
    Hierarchical, structure-aware semantic chunking algorithm.
    """

    def __init__(self, tokenizer: Optional[SemanticTokenizer] = None):
        self.tokenizer = tokenizer or SemanticTokenizer.get_instance()

    def chunk_section(
        self,
        doc_info: Dict[str, Any],
        section: Dict[str, Any],
        breadcrumb: str,
        chunking_version: str = chunking_settings.CHUNKING_VERSION
    ) -> List[Dict[str, Any]]:
        """
        Convert a single document section into one or more semantic chunks.
        """
        section_id = section.get("id")
        doc_id = doc_info.get("id")
        section_heading = section.get("heading") or doc_info.get("title") or "General"
        raw_content = section.get("content") or ""

        # Normalize content (tables, notes, whitespace)
        normalized_content = TextNormalizer.normalize_section_content(raw_content)
        if not normalized_content.strip():
            logger.debug(f"Skipping empty section_id={section_id} for doc_id={doc_id}")
            return []

        # Parse section into structural blocks
        blocks = StructuralParser.parse_section(normalized_content, default_heading=section_heading)
        if not blocks:
            return []

        # Calculate token counts for each block
        for b in blocks:
            b.token_count = self.tokenizer.count_tokens(b.content)

        # Build chunks from blocks
        raw_chunk_bodies = self._group_blocks_into_chunk_bodies(blocks)
        if not raw_chunk_bodies:
            return []

        chunks: List[Dict[str, Any]] = []

        for idx, body in enumerate(raw_chunk_bodies):
            # Construct contextual metadata header
            enriched_content = self._format_enriched_chunk_content(
                doc_title=doc_info.get("title", ""),
                breadcrumb=breadcrumb,
                section_heading=section_heading,
                body=body
            )

            token_count = self.tokenizer.count_tokens(enriched_content)
            char_count = len(enriched_content)

            # Deterministic Content Hash (document_id + section_id + index + content)
            hash_input = f"{doc_id}:{section_id}:{idx}:{normalized_content[:200]}:{body}"
            content_hash = hashlib.sha256(hash_input.encode("utf-8")).hexdigest()

            metadata = {
                "source_pdf": doc_info.get("source_pdf"),
                "document_id": doc_id,
                "document_title": doc_info.get("title"),
                "document_url": doc_info.get("url"),
                "canonical_url": doc_info.get("canonical_url"),
                "root_document_id": doc_info.get("root_document_id"),
                "parent_document_id": doc_info.get("parent_id"),
                "section_id": section_id,
                "section_title": section_heading,
                "breadcrumb": breadcrumb,
                "depth": doc_info.get("depth"),
                "chunk_index": idx,
                "chunking_version": chunking_version,
                "content_hash": content_hash,
                "character_count": char_count,
                "token_count": token_count
            }

            chunks.append({
                "document_id": doc_id,
                "section_id": section_id,
                "chunk_index": idx,
                "content": enriched_content,
                "token_count": token_count,
                "content_hash": content_hash,
                "metadata": metadata
            })

        return chunks

    def _group_blocks_into_chunk_bodies(self, blocks: List[SemanticBlock]) -> List[str]:
        """
        Group structural blocks into chunk bodies honoring token bounds & overlap.
        """
        total_section_tokens = sum(b.token_count for b in blocks)

        # Small Section Rule: If section is < TARGET_MAX_TOKENS, keep as 1 chunk body
        if total_section_tokens <= chunking_settings.TARGET_MAX_TOKENS:
            full_body = "\n\n".join(b.content for b in blocks)
            return [full_body]

        # Large Section Rule: Hierarchical block aggregation with overlap
        chunk_bodies: List[str] = []
        current_blocks: List[SemanticBlock] = []
        current_tokens = 0

        for block in blocks:
            # Handle oversized single block (e.g. huge paragraph > HARD_MAX_TOKENS)
            if block.token_count > chunking_settings.HARD_MAX_TOKENS:
                if current_blocks:
                    chunk_bodies.append("\n\n".join(b.content for b in current_blocks))
                    current_blocks = []
                    current_tokens = 0
                
                # Split oversized block by sentences
                sub_chunks = self._split_oversized_block(block)
                chunk_bodies.extend(sub_chunks)
                continue

            # If adding this block exceeds target max, finalize current chunk body
            if current_tokens + block.token_count > chunking_settings.TARGET_MAX_TOKENS and current_blocks:
                chunk_body = "\n\n".join(b.content for b in current_blocks)
                chunk_bodies.append(chunk_body)

                # Compute overlap blocks (75-100 tokens from end of current_blocks)
                overlap_blocks = self._extract_overlap_blocks(current_blocks)
                current_blocks = list(overlap_blocks)
                current_tokens = sum(b.token_count for b in current_blocks)

            current_blocks.append(block)
            current_tokens += block.token_count

        if current_blocks:
            chunk_bodies.append("\n\n".join(b.content for b in current_blocks))

        return chunk_bodies

    def _extract_overlap_blocks(self, blocks: List[SemanticBlock]) -> List[SemanticBlock]:
        """
        Extract recent blocks from the tail of current_blocks up to TARGET_OVERLAP_TOKENS.
        """
        overlap_blocks = []
        overlap_tokens = 0
        target = chunking_settings.TARGET_OVERLAP_TOKENS

        for b in reversed(blocks):
            # Do not overlap tables or oversized blocks
            if b.block_type in (BlockType.TABLE, BlockType.CODE_CONFIG):
                continue

            overlap_blocks.insert(0, b)
            overlap_tokens += b.token_count
            if overlap_tokens >= target:
                break

        return overlap_blocks

    def _split_oversized_block(self, block: SemanticBlock) -> List[str]:
        """
        Split a single oversized paragraph/block by sentences.
        """
        sentences = re.split(r"(?<=[.!?])\s+", block.content)
        sub_chunks = []
        current_sentences = []
        current_tokens = 0

        for s in sentences:
            s_tok = self.tokenizer.count_tokens(s)
            if current_tokens + s_tok > chunking_settings.TARGET_MAX_TOKENS and current_sentences:
                sub_chunks.append(" ".join(current_sentences))
                current_sentences = []
                current_tokens = 0

            current_sentences.append(s)
            current_tokens += s_tok

        if current_sentences:
            sub_chunks.append(" ".join(current_sentences))

        return sub_chunks

    def _format_enriched_chunk_content(
        self,
        doc_title: str,
        breadcrumb: str,
        section_heading: str,
        body: str
    ) -> str:
        """
        Format header enrichment prefix:
        [DOCUMENT]
        ...
        [PATH]
        ...
        [SECTION]
        ...
        [CONTENT]
        ...
        """
        header = (
            f"[DOCUMENT]\n{doc_title}\n\n"
            f"[PATH]\n{breadcrumb}\n\n"
            f"[SECTION]\n{section_heading}\n\n"
            f"[CONTENT]\n"
        )
        return header + body
