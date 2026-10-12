"""
FastAPI Router for SAP Utilities RAG Chatbot endpoints.
"""

import logging
from fastapi import APIRouter, HTTPException, status, Depends
from sap_rag.database.connection import DatabasePool
from sap_rag.retrieval.schemas import ChatRequest, ChatResponse
from sap_rag.chat.service import ChatService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/chat", tags=["chat"])
chat_service_instance = ChatService()

@router.post("", response_model=ChatResponse, status_code=status.HTTP_200_OK)
@router.post("/", response_model=ChatResponse, status_code=status.HTTP_200_OK)
async def chat_with_sap_utilities(req: ChatRequest):
    """
    Conversational RAG endpoint for SAP Utilities questions.
    Retrieves grounded context via frozen V5.5.1 Retrieval Engine and generates an answer with sources.
    """
    user_msg = req.message
    if not user_msg and req.messages:
        last = req.messages[-1]
        user_msg = last.get("content", "") if isinstance(last, dict) else getattr(last, "content", "")

    if not user_msg or not str(user_msg).strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Chat request must contain a non-empty 'message' or 'messages' payload."
        )

    try:
        async with DatabasePool.acquire() as conn:
            response = await chat_service_instance.process_chat(
                conn=conn,
                request=req
            )
            return response
    except Exception as e:
        logger.error(f"Error during chat processing for query '{req.message}': {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Chat orchestration failure: {str(e)}"
        )
