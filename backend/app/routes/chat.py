from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from app.services.gemini_service import gemini_service
from app.db import db
from datetime import datetime
import uuid

router = APIRouter()

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    message: str
    history: Optional[List[ChatMessage]] = []

@router.post("/message")
async def chat_message(payload: ChatRequest):
    """
    Processes a chat message using Gemini with tool-calling capabilities.
    """
    try:
        # Convert Pydantic history to dict list for gemini_service
        history_dicts = [m.dict() for m in payload.history] if payload.history else []
        
        # Use chat_with_tools to allow AI to perform actions if requested
        response = await gemini_service.chat_with_tools(
            prompt=payload.message,
            chat_history=history_dicts
        )
        
        # Log the chat event in the DB for persistence
        chat_event = {
            "_id": f"chat_{uuid.uuid4().hex[:8]}",
            "user_message": payload.message,
            "ai_response": response,
            "timestamp": datetime.utcnow().isoformat(),
        }
        await db.prompt_history.insert_one(chat_event)
        
        return {
            "response": response,
            "timestamp": chat_event["timestamp"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/history")
async def get_chat_history(limit: int = 20):
    """Retrieves recent chat history."""
    cursor = db.prompt_history.find().sort("timestamp", -1).limit(limit)
    history = await cursor.to_list(length=limit)
    return history
