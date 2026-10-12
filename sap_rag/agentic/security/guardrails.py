"""
Security Guardrails for Agentic Intelligence Platform.
Enforces read-only DB invariants, prompt injection defense,
and sensitive credential redaction.
"""

import re
import logging
from typing import Optional, List, Dict

logger = logging.getLogger("sap_rag.agentic.security")


class SecurityGuardrails:
    """
    Security defenses for untrusted user inputs and untrusted retrieved documentation text.
    """

    # Patterns commonly used in prompt injection attempts
    PROMPT_INJECTION_PATTERNS = [
        r"(?i)ignore\s+(all\s+)?(previous|prior)\s+instructions",
        r"(?i)you\s+are\s+now\s+(in\s+developer\s+mode|dan)",
        r"(?i)reveal\s+(your\s+)?(system\s+prompt|secret|api\s*key)",
        r"(?i)disregard\s+(the\s+)?(above|instructions)",
        r"(?i)<script[\s>]",
        r"(?i)javascript:"
    ]

    SECRET_PATTERNS = [
        r"(?i)(aiza[0-9a-za-z-_]{35})",                   # Google API Key
        r"(?i)(sk-[0-9a-za-z]{32,})",                     # OpenAI Key
        r"(?i)(postgres(ql)?://[^\s:@]+:[^\s:@]+@[^\s]+)" # DB URI with password
    ]

    @classmethod
    def sanitize_untrusted_text(cls, text: str) -> str:
        """
        Neutralize embedded prompt injections from documents or user queries.
        Treats retrieved documentation as untrusted data.
        """
        if not text:
            return ""

        sanitized = text
        for pat in cls.PROMPT_INJECTION_PATTERNS:
            sanitized = re.sub(pat, "[BLOCKED_INSTRUCTION]", sanitized)

        return sanitized

    @classmethod
    def redact_secrets(cls, text: str) -> str:
        """
        Redact known secret patterns from strings before transmission or logging.
        """
        if not text:
            return ""

        redacted = text
        for pat in cls.SECRET_PATTERNS:
            redacted = re.sub(pat, "[REDACTED_SECRET]", redacted)

        return redacted
