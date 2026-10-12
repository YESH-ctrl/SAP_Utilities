"""
Structural parser that converts raw section content into structured semantic blocks:
- HEADING
- PARAGRAPH
- PROCEDURE (Numbered steps)
- LIST (Bullet lists)
- TABLE (Key-value formatted tables)
- NOTE (Warnings / Caution / Notes)
- EXAMPLE (Examples)
- CODE_CONFIG (Code / SAP Configuration blocks)
"""

import re
from typing import List, Dict, Any, Optional
from enum import Enum
from pydantic import BaseModel

class BlockType(str, Enum):
    HEADING = "HEADING"
    PARAGRAPH = "PARAGRAPH"
    PROCEDURE = "PROCEDURE"
    LIST = "LIST"
    TABLE = "TABLE"
    NOTE = "NOTE"
    EXAMPLE = "EXAMPLE"
    CODE_CONFIG = "CODE_CONFIG"

class SemanticBlock(BaseModel):
    block_type: BlockType
    content: str
    heading_context: Optional[str] = None
    token_count: int = 0
    is_atomic: bool = True  # True means should not be split across chunks if possible

class StructuralParser:
    """
    Parses section content into atomic semantic blocks.
    """

    @classmethod
    def parse_section(cls, text: str, default_heading: Optional[str] = None) -> List[SemanticBlock]:
        if not text or not text.strip():
            return []

        # Split into double-newline separated chunks first
        raw_chunks = [c.strip() for c in re.split(r"\n\s*\n", text) if c.strip()]
        blocks: List[SemanticBlock] = []
        current_heading = default_heading

        for raw in raw_chunks:
            # Check if block is a markdown heading
            if raw.startswith("#"):
                heading_text = raw.lstrip("#").strip()
                current_heading = heading_text
                blocks.append(SemanticBlock(
                    block_type=BlockType.HEADING,
                    content=raw,
                    heading_context=current_heading,
                    is_atomic=True
                ))
                continue

            # Check if block is a converted or raw Table
            if raw.startswith("TABLE:") or raw.startswith("|") or "<table" in raw.lower():
                blocks.append(SemanticBlock(
                    block_type=BlockType.TABLE,
                    content=raw,
                    heading_context=current_heading,
                    is_atomic=True
                ))
                continue

            # Check if block is a Note / Warning / Caution / Recommendation
            if re.match(r"(?i)^(Note|Important|Caution|Warning|Recommendation):", raw):
                blocks.append(SemanticBlock(
                    block_type=BlockType.NOTE,
                    content=raw,
                    heading_context=current_heading,
                    is_atomic=True
                ))
                continue

            # Check if block is an Example
            if re.match(r"(?i)^Example:", raw):
                blocks.append(SemanticBlock(
                    block_type=BlockType.EXAMPLE,
                    content=raw,
                    heading_context=current_heading,
                    is_atomic=True
                ))
                continue

            # Check if block is a numbered procedure (e.g. 1. Step, 2. Step)
            lines = raw.splitlines()
            if len(lines) > 1 and all(re.match(r"^\d+[\.\)]\s+", l.strip()) for l in lines if l.strip()):
                blocks.append(SemanticBlock(
                    block_type=BlockType.PROCEDURE,
                    content=raw,
                    heading_context=current_heading,
                    is_atomic=True
                ))
                continue

            # Check if block is a bullet list (e.g. - Item, * Item, • Item)
            if len(lines) > 1 and all(re.match(r"^[\-\*\•]\s+", l.strip()) for l in lines if l.strip()):
                blocks.append(SemanticBlock(
                    block_type=BlockType.LIST,
                    content=raw,
                    heading_context=current_heading,
                    is_atomic=True
                ))
                continue

            # Check if block is code / configuration block
            if raw.startswith("```") or "Transaction Code:" in raw or "SPRO >" in raw:
                blocks.append(SemanticBlock(
                    block_type=BlockType.CODE_CONFIG,
                    content=raw,
                    heading_context=current_heading,
                    is_atomic=True
                ))
                continue

            # Default: Paragraph
            blocks.append(SemanticBlock(
                block_type=BlockType.PARAGRAPH,
                content=raw,
                heading_context=current_heading,
                is_atomic=False
            ))

        return blocks
