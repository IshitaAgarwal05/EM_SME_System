"""
AI and Chatbot API endpoints.
"""

from typing import Annotated, List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

import structlog
from app.db.session import get_db
from app.dependencies import CurrentUser
from app.services.ai.vector_store import VectorStoreService
from app.services.ai.chatbot import ChatbotService

logger = structlog.get_logger()

router = APIRouter(prefix="/ai", tags=["AI"])

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    message: str
    history: List[ChatMessage] = []

class ChatResponse(BaseModel):
    response: str


@router.post("/chat", response_model=ChatResponse)
async def chat_interaction(
    request: ChatRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: CurrentUser,
):
    """
    Chat with the AI assistant.
    The AI uses RAG (Retrieval Augmented Generation) to answer based on your organization's data.
    """
    try:
        # Initialize services
        # In a real app, VectorStoreService would be a singleton injected dependency
        vector_store = VectorStoreService() 
        chatbot = ChatbotService(current_user.organization_id, vector_store, db)
        
        # Convert Pydantic models to dicts for service
        history_dicts = [{"role": m.role, "content": m.content} for m in request.history]
        
        # Get response
        response = await chatbot.chat(request.message, history_dicts)
        
        return ChatResponse(response=response)
        
    except Exception as e:
        logger.error("chatbot_error", error=str(e), user_id=str(current_user.id), exc_info=True)
        error_msg = f"AI Error: {str(e)}" if settings.debug else "I encountered an issue while processing your request. Please ensure the AI service is configured correctly or try again later."
        return ChatResponse(response=error_msg)


@router.post("/index/sync")
async def trigger_indexing(
    current_user: CurrentUser,
    # In real world would accept filtering params or Entity IDs
):
    """
    Manually trigger indexing of organization data.
    (Debug/Admin endpoint - ideally this happens via background worker on data changes)
    """
    # TODO: Implement bulk indexing of current_user.organization_id data
    # This would iterate Tasks, Meetings, etc., and call vector_store.index_entity()
    return {"message": "Indexing triggered (Not implemented yet)"}
