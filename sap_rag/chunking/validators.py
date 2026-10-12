"""
Validation module for quality assurance of generated semantic chunks.
"""

from typing import List, Dict, Any, Tuple
import logging

logger = logging.getLogger(__name__)

class ChunkValidator:
    """
    Automated chunk quality validation checks.
    """

    @classmethod
    def validate_chunks(cls, chunks: List[Dict[str, Any]]) -> Tuple[bool, List[str]]:
        """
        Run validation checks on a set of generated chunk dictionaries.
        Returns (is_valid, error_messages).
        """
        errors = []

        if not chunks:
            return True, []

        seen_section_hashes = set()

        for idx, chk in enumerate(chunks):
            chunk_id_repr = f"doc={chk.get('document_id')}, sec={chk.get('section_id')}, index={chk.get('chunk_index')}"

            content = chk.get("content")
            if content is None:
                errors.append(f"Null chunk content at {chunk_id_repr}")
                continue
            if not content.strip():
                errors.append(f"Empty chunk content at {chunk_id_repr}")

            if not chk.get("document_id"):
                errors.append(f"Missing document_id at index {idx}")

            if not chk.get("section_id"):
                errors.append(f"Missing section_id at index {idx}")

            token_count = chk.get("token_count", 0)
            if token_count <= 0:
                errors.append(f"Invalid token count ({token_count}) at {chunk_id_repr}")

            content_hash = chk.get("content_hash")
            if not content_hash:
                errors.append(f"Missing content_hash at {chunk_id_repr}")

            metadata = chk.get("metadata") or {}
            if not metadata.get("breadcrumb"):
                errors.append(f"Missing breadcrumb metadata at {chunk_id_repr}")

            if not metadata.get("canonical_url") and not metadata.get("document_url"):
                errors.append(f"Missing URL provenance metadata at {chunk_id_repr}")

            # Check duplicate hash for same section & version
            sec_hash_key = (chk.get("section_id"), metadata.get("chunking_version"), content_hash)
            if sec_hash_key in seen_section_hashes:
                errors.append(f"Duplicate content hash within same section/version at {chunk_id_repr}")
            seen_section_hashes.add(sec_hash_key)

        is_valid = len(errors) == 0
        return is_valid, errors
