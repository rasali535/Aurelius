from fastapi import APIRouter
from pydantic import BaseModel
from app.services.gemini_service import gemini_service
from typing import List, Optional

router = APIRouter()

class ChatMessage(BaseModel):
    role: str
    parts: List[str]

class ChatRequest(BaseModel):
    message: str
    history: Optional[List[ChatMessage]] = None

@router.post("/chat")
async def agent_chat(payload: ChatRequest):
    """
    Agent-driven workflow for commerce and coordination.
    Uses Gemini to handle reasoning and Circle tools for value settlement.
    """
    # Convert history back to Gemini format if provided
    history = []
    if payload.history:
        for msg in payload.history:
            history.append({
                "role": msg.role,
                "parts": msg.parts
            })
            
    response = await gemini_service.chat_with_tools(payload.message, history)
    return {"response": response}
