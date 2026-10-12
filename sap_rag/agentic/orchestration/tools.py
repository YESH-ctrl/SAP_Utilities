"""
Narrow Typed CrewAI Tools for Agentic Knowledge Platform.
Invokes deterministic SemanticRetrievalService and GraphTraversalService.
Returns strictly typed structured JSON data.
"""

import json
import asyncio
from typing import List, Dict, Any, Optional
from crewai.tools import tool

from sap_rag.agentic.retrieval.service import SemanticRetrievalService
from sap_rag.agentic.retrieval.traversal import GraphTraversalService
from sap_rag.agentic.schemas.contracts import EvidenceItem


# Reusable service instances
_retrieval_service = SemanticRetrievalService()
_traversal_service = GraphTraversalService()


@tool("search_sap_documentation")
def search_sap_documentation(query: str, subquery_id: str = "SQ-1", top_k: int = 5) -> str:
    """
    Direct semantic vector search over SAP Utilities documentation chunks.
    Use this tool to find authoritative SAP Utilities documentation passages.
    Args:
        query: Specific semantic search question or keywords.
        subquery_id: ID of the subquestion e.g. SQ-1.
        top_k: Number of evidence items to return (max 8).
    Returns:
        JSON string containing list of evidence items with chunk_id, title, url, and content.
    """
    clean_k = min(8, max(1, int(top_k)))
    
    # Run async retrieval within synchronous tool call
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            import nest_asyncio
            nest_asyncio.apply()
            hits = loop.run_until_complete(
                _retrieval_service.search(query=query, subquery_id=subquery_id, top_k=clean_k)
            )
        else:
            hits = asyncio.run(
                _retrieval_service.search(query=query, subquery_id=subquery_id, top_k=clean_k)
            )
    except Exception as e:
        # Fallback to direct thread runner
        from concurrent.futures import ThreadPoolExecutor
        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(
                lambda: asyncio.run(_retrieval_service.search(query=query, subquery_id=subquery_id, top_k=clean_k))
            )
            hits = future.result()

    return json.dumps([h.model_dump() for h in hits], default=str)


@tool("expand_document_relationships")
def expand_document_relationships(seed_evidence_json: str, max_items: int = 3) -> str:
    """
    Traverse parent-child hierarchy and internal hyperlinks from discovered seed evidence.
    Use this tool when finding prerequisites, parent section overviews, or cross-document dependencies.
    Args:
        seed_evidence_json: JSON string of seed EvidenceItem records.
        max_items: Maximum related passages to retrieve (max 5).
    Returns:
        JSON string of related evidence passages.
    """
    try:
        data = json.loads(seed_evidence_json)
        items = [EvidenceItem(**d) for d in data] if isinstance(data, list) else []
    except Exception:
        items = []

    if not items:
        return json.dumps([])

    clean_max = min(5, max(1, int(max_items)))
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            import nest_asyncio
            nest_asyncio.apply()
            expanded = loop.run_until_complete(
                _traversal_service.expand_evidence_graph(items, max_additional_chunks=clean_max)
            )
        else:
            expanded = asyncio.run(
                _traversal_service.expand_evidence_graph(items, max_additional_chunks=clean_max)
            )
    except Exception:
        from concurrent.futures import ThreadPoolExecutor
        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(
                lambda: asyncio.run(_traversal_service.expand_evidence_graph(items, max_additional_chunks=clean_max))
            )
            expanded = future.result()

    return json.dumps([e.model_dump() for e in expanded], default=str)
