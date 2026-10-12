"""
Main FastAPI Web Application entry point for SAP Utilities RAG Pipeline & Retrieval Engine.
"""

import os
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from sap_rag.database.connection import DatabasePool
from sap_rag.retrieval.schemas import ChatRequest
from sap_rag.api.retrieval_router import router as retrieval_router
from sap_rag.api.chat_router import router as chat_router
from sap_rag.api.evaluation_router import router as evaluation_router
from sap_rag.api.sources_router import router as sources_router
from sap_rag.agentic.api.router import router as agentic_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("sap_rag")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manage application startup and shutdown events cleanly.
    Validates Gemini API configuration without making external network calls.
    """
    logger.info("Initializing SAP Utilities RAG database connection pool...")
    await DatabasePool.initialize(min_size=2, max_size=15)

    groq_key = os.getenv("GROQ_API_KEY")
    if groq_key and groq_key.strip():
        logger.info(f"✓ GROQ_API_KEY is configured. Groq model: '{os.getenv('GROQ_MODEL', 'qwen/qwen3.8-27b')}'")

    gemini_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not gemini_key or not gemini_key.strip():
        logger.warning("⚠️  GEMINI_API_KEY is not configured. Retrieval Engine V5.5.1 remains fully functional in retrieval-only / fallback mode.")
    else:
        logger.info(f"✓ GEMINI_API_KEY is configured. Gemini model: '{os.getenv('GEMINI_MODEL', 'gemini-3.5-flash')}'")

    yield
    logger.info("Shutting down SAP Utilities RAG database connection pool...")
    await DatabasePool.close()

app = FastAPI(
    title="SAP Utilities RAG Chatbot & Retrieval API",
    description="Enterprise-grade Retrieval Augmented Generation (RAG) Conversational API for SAP Utilities Documentation (V5.5.1)",
    version="5.5.1",
    lifespan=lifespan
)

raw_origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173,http://localhost:8501,http://127.0.0.1:8501,http://localhost:8000,http://127.0.0.1:8000")
allowed_origins = [o.strip() for o in raw_origins.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(retrieval_router)
app.include_router(chat_router)
app.include_router(evaluation_router)
app.include_router(sources_router)
app.include_router(agentic_router)

@app.get("/")
async def root():
    return {
        "service": "SAP Utilities Knowledge Intelligence API",
        "legacy_version": "5.5.1",
        "agentic_version": "2.0.0",
        "docs_url": "/docs",
        "legacy_endpoints": {
            "query_endpoint": "/api/v1/retrieval/query",
            "chat_endpoint": "/api/v1/chat",
            "search_endpoint": "/api/v1/retrieval/search",
            "sources_endpoint": "/api/v1/sources",
            "evaluation_endpoint": "/api/v1/evaluation",
            "health_endpoint": "/api/v1/retrieval/health"
        },
        "agentic_endpoints": {
            "chat_endpoint": "/api/v2/agentic/chat",
            "search_endpoint": "/api/v2/agentic/search",
            "health_endpoint": "/api/v2/agentic/health"
        }
    }

@app.get("/health")
@app.get("/api/v1/health")
async def top_level_health():
    from sap_rag.api.retrieval_router import retrieval_health_check
    return await retrieval_health_check()

@app.post("/chat")
@app.post("/api/v1/chat")
async def top_level_chat(req: ChatRequest):
    from sap_rag.api.chat_router import chat_with_sap_utilities
    return await chat_with_sap_utilities(req)

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "8000"))
    logger.info(f"Starting SAP Utilities RAG API server on port {port}...")
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
