"""
Lightweight, deterministic query processor for SAP Utilities RAG V3.
Performs text normalization, technical term extraction, linguistic query expansion, intent classification, and domain mapping.
"""

import re
import logging
from typing import List, Dict, Any, Set
from sap_rag.retrieval.models import ProcessedQuery

logger = logging.getLogger(__name__)

# Core SAP Utilities technical terms dictionary
SAP_TECHNICAL_TERMS: List[str] = [
    "FI-CA", "FI CA", "Contract Account", "Contract Accounts",
    "Clearing Control", "Clearing Types", "Clearing",
    "Incoming Payments", "Incoming Payment", "Payment Lot",
    "Dunning", "Dunning Procedure", "Dunning Notice",
    "Installment Plan", "Installment Plans",
    "Budget Billing Plan", "Budget Billing", "BBP",
    "Move-In", "Move-Out", "Move In", "Move Out", "Move-In/Out",
    "Meter Reading", "Meter Readings", "Meter Reading Results", "Meter Reading Estimation",
    "Billing", "Billing Procedure", "Automatic Billing", "Periodic Billing",
    "Invoicing", "Invoicing Procedure",
    "Disconnection", "Reconnection", "Utility Installation", "Utility Service",
    "Device Management", "Utilities Master Data", "Master Data",
    "Collection Agency", "Receivables", "BP", "Business Partner",
    "Point of Delivery", "POD", "Premise", "Connection Object"
]

# Generic linguistic & acronym expansion mappings (Phase 3 & 4)
EXPANSION_MAP: Dict[str, str] = {
    "pod": "point of delivery pod OR point of delivery OR pod",
    "point of delivery": "point of delivery pod OR point of delivery OR pod",
    "fi-ca": "fi-ca OR contract account OR fica",
    "fica": "fi-ca OR contract account",
    "bbp": "budget billing plan OR bbp",
    "budget billing": "budget billing OR budget billing plan OR bbp",
    "budget billing plan": "budget billing plan OR budget billing OR bbp",
    "reconnection": "reconnection OR reconnect OR \"disconnection reconnection\"",
    "reconnect": "reconnection OR reconnect OR \"disconnection reconnection\"",
    "installment plan": "installment plan OR installment plans",
    "installment": "installment plan OR installment plans",
    "estimation": "estimation procedure OR estimated meter reading",
    "estimated": "estimation procedure OR estimated meter reading",
    "dunning": "dunning procedure OR dunning notice",
    "clearing": "clearing control OR clearing types OR incoming payments",
    "clearing types": "clearing types OR clearing type OR clearing control",
    "move-in": "move-in OR move in OR movein",
    "move-out": "move-out OR move out OR moveout",
    "meter reading": "meter reading OR meter readings OR meter reading results",
    "billing": "billing OR billing procedure OR automatic billing",
    "invoicing": "invoicing OR invoicing procedure OR print document",
    "disconnection": "disconnection OR disconnection order OR disconnect",
    "collection agency": "collection agency OR receivables submission"
}

# Domain keywords map - Specific multi-word keywords MUST be evaluated before generic keywords
DOMAIN_KEYWORD_MAP: Dict[str, List[str]] = {
    "budget_billing": ["budget billing plan", "budget billing", "bbp"],
    "installment_plan": ["installment plan", "installment", "deferral", "payment plan"],
    "clearing": ["clearing control", "clearing type", "clearing types", "clearing", "incoming payment", "payment lot"],
    "collection_agency": ["collection agency", "submission of receivables", "receivables"],
    "device_management": ["device management", "device", "register", "equipment"],
    "meter_reading": ["meter reading", "meter", "reading", "estimation", "meter reading result"],
    "move_in_out": ["move-in", "move-out", "move in", "move out", "move in out"],
    "disconnection": ["disconnection order", "disconnection", "reconnection order", "reconnection", "utility installation", "utility service"],
    "invoicing": ["invoicing procedure", "invoicing", "invoice", "print document"],
    "contract_accounts": ["contract account", "contract accounts", "business partner", "fi-ca"],
    "dunning": ["fi-ca dunning", "dunning procedure", "dunning notice", "dunning", "overdue"],
    "billing": ["automatic billing", "periodic billing", "billing procedure", "billing", "rate"]
}

# Intent trigger patterns
INTENT_PATTERNS: Dict[str, List[str]] = {
    "procedure": ["how do i", "how to", "create", "process", "procedure", "steps", "execute", "change", "display", "perform"],
    "overview": ["overview", "what is", "what are", "concept", "introduction", "architecture", "explain"],
    "definition": ["define", "meaning of", "definition", "term", "specification"],
    "technical_api": ["api", "service", "interface", "enterprise service", "bapi", "table"]
}

class QueryProcessor:
    """
    Deterministic query preprocessing and term expansion engine.
    """

    @classmethod
    def process(cls, query: str) -> ProcessedQuery:
        if not query or not query.strip():
            return ProcessedQuery(
                original_query="",
                normalized_query="",
                expanded_query="",
                keywords=[],
                technical_terms=[],
                intent="general",
                domain="general",
                retrieval_confidence="HIGH"
            )

        original_query = query.strip()

        # 1. Normalize query
        normalized = original_query.lower()
        normalized = re.sub(r"[^\w\s\-\/]", " ", normalized)
        normalized = re.sub(r"\s+", " ", normalized).strip()

        # 2. Extract technical terms
        found_terms: Set[str] = set()
        for term in SAP_TECHNICAL_TERMS:
            pattern = r"\b" + re.escape(term.lower()) + r"\b"
            if re.search(pattern, normalized):
                found_terms.add(term)

        # 3. Extract keywords (words longer than 2 chars excluding stop words)
        stopwords = {"how", "do", "i", "the", "a", "an", "in", "on", "for", "to", "is", "what", "are", "and", "or", "of", "with", "can", "perform"}
        tokens = normalized.split()
        keywords = [t for t in tokens if len(t) > 2 and t not in stopwords]

        # 4. Construct expanded query for retrieval miss recovery
        expansions = set()
        matched_phrase_tokens = set()

        for term in found_terms:
            t_lower = term.lower()
            if t_lower in EXPANSION_MAP:
                expansions.add(EXPANSION_MAP[t_lower])
                for tok in t_lower.split():
                    matched_phrase_tokens.add(tok)

        for token in tokens:
            if token not in matched_phrase_tokens and token in EXPANSION_MAP:
                expansions.add(EXPANSION_MAP[token])

        expanded_query = " OR ".join(sorted(list(expansions))) if expansions else normalized

        # 5. Classify intent
        query_lower = original_query.lower()
        detected_intent = "general"
        for intent, patterns in INTENT_PATTERNS.items():
            if any(p in query_lower for p in patterns):
                detected_intent = intent
                break

        # 6. Classify domain
        detected_domain = "general"
        for domain, domain_kws in DOMAIN_KEYWORD_MAP.items():
            if any(dkw in query_lower for dkw in domain_kws):
                detected_domain = domain
                break

        return ProcessedQuery(
            original_query=original_query,
            normalized_query=normalized,
            expanded_query=expanded_query,
            keywords=keywords,
            technical_terms=sorted(list(found_terms)),
            intent=detected_intent,
            domain=detected_domain,
            retrieval_confidence="HIGH"
        )
