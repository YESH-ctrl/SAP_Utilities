"""
Live Integration Test Script for SAP Utilities RAG Gemini Answer Generation V5.5.1 Integration.

Verifies end-to-end functionality using Gemini LLM service and V5.5.1 retrieval engine.
"""

import os
import sys
import asyncio
import logging

from dotenv import load_dotenv
load_dotenv()

# Ensure root directory is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sap_rag.database.connection import DatabasePool
from sap_rag.chat.service import ChatService
from sap_rag.retrieval.schemas import ChatRequest

if os.name == "nt" or sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("live_integration_test")

async def run_live_test():
    print("=================================================================")
    print("   SAP UTILITIES RAG V5.5.1 — GEMINI LIVE INTEGRATION TEST      ")
    print("=================================================================")

    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    model_name = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

    if not api_key:
        print("\n⚠️  GEMINI_API_KEY environment variable is not set.")
        print("    Running test in fallback synthesizer mode...")
    else:
        print(f"\n✓ Found GEMINI_API_KEY (Model: '{model_name}')")

    await DatabasePool.initialize(min_size=2, max_size=5)
    chat_service = ChatService()

    question = "How do I perform the reconnection?"
    print(f"\nSending Query: '{question}'...\n")

    request = ChatRequest(
        message=question,
        conversation_id="live-test-session-001",
        top_k=8
    )

    async with DatabasePool.acquire() as conn:
        response = await chat_service.process_chat(conn=conn, request=request)

    print("=================================================================")
    print("                      ASSISTANT RESPONSE                         ")
    print("=================================================================")
    print(response.message.content)
    print("\n=================================================================")
    print("                     SUPPORTING SOURCES                          ")
    print("=================================================================")
    for src in response.sources:
        print(f"Rank {src.rank}: [{src.title}] (Doc ID: {src.document_id}) - URL: {src.url}")
        print(f"        Excerpt: {src.excerpt[:120]}...\n")

    print("=================================================================")
    print("                     METRICS & LATENCY                           ")
    print("=================================================================")
    for k, v in response.metadata.items():
        print(f" - {k}: {v}")

    await DatabasePool.close()
    print("\n✓ Live Integration Test Complete.")

if __name__ == "__main__":
    asyncio.run(run_live_test())
