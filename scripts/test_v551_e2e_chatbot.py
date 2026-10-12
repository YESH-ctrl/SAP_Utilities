"""
End-to-End Acceptance Test for SAP Utilities RAG Chatbot (Release V5.5.1 Integration Layer).

Tests full flow:
User Question -> FastAPI /api/v1/chat -> V5.5.1 Retrieval Engine -> Database -> Grounded LLM Generation -> Sources
"""

import sys
import os
import asyncio
import logging

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sap_rag.database.connection import DatabasePool
from sap_rag.retrieval.schemas import ChatRequest
from sap_rag.chat.service import ChatService

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("e2e_test")

async def run_e2e_test():
    logger.info("Starting V5.5.1 Chatbot E2E Acceptance Test...")
    logger.info("Initializing database connection pool...")

    await DatabasePool.initialize(min_size=2, max_size=10)

    try:
        chat_service = ChatService()
        test_query = "How do I perform a reconnection?"

        logger.info(f"Submitting query: '{test_query}'")

        request = ChatRequest(message=test_query, top_k=10)

        async with DatabasePool.acquire() as conn:
            response = await chat_service.process_chat(conn=conn, request=request)

        logger.info("=" * 60)
        logger.info("E2E ACCEPTANCE TEST RESULT:")
        logger.info("=" * 60)
        logger.info(f"Conversation ID: {response.conversation_id}")
        logger.info(f"Role: {response.message.role}")
        logger.info(f"Generated Answer:\n{response.message.content}")
        logger.info("-" * 60)
        logger.info(f"Sources Count: {len(response.sources)}")
        for idx, src in enumerate(response.sources, 1):
            logger.info(f"Source {idx}: {src.title} (Doc ID: {src.document_id}) - Score: {src.score}")
        logger.info("-" * 60)
        logger.info(f"Metadata: {response.metadata}")
        logger.info("=" * 60)

        # Verification assertions
        assert response.conversation_id is not None, "Conversation ID must be generated"
        assert response.message.content and len(response.message.content) > 20, "Answer content must not be empty"
        assert len(response.sources) > 0, "At least one source must be returned"
        assert response.metadata.get("retrieval_version") == "5.5.1", "Version must be 5.5.1"
        assert "retrieval_latency_ms" in response.metadata, "Retrieval latency must be present"

        logger.info("✅ SUCCESS: V5.5.1 Chatbot E2E Acceptance Test PASSED cleanly!")

    finally:
        await DatabasePool.close()

if __name__ == "__main__":
    asyncio.run(run_e2e_test())
