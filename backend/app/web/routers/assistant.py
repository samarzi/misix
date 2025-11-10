from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
from pydantic import BaseModel
import logging

from app.shared.config import settings
from app.shared.supabase import get_supabase_client
from app.bot.yandex_gpt import get_yandex_gpt_client

router = APIRouter()
logger = logging.getLogger(__name__)

# Pydantic models
class MessageBase(BaseModel):
    content: str
    role: str = "user"

class MessageCreate(MessageBase):
    pass

class Message(MessageBase):
    id: str
    session_id: Optional[str]
    user_id: str
    created_at: str

    class Config:
        from_attributes = True

class AssistantSessionBase(BaseModel):
    title: Optional[str] = None

class AssistantSessionCreate(AssistantSessionBase):
    pass

class AssistantSession(AssistantSessionCreate):
    id: str
    user_id: str
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True

class ChatRequest(BaseModel):
    message: str
    user_id: str

    class Config:
        allow_population_by_field_name = True

# Mock authentication for now - in real app, this would validate JWT token
def get_current_user_id() -> str:
    # TODO: Implement proper JWT authentication
    # For now, return a mock user ID
    return "550e8400-e29b-41d4-a716-446655440000"

@router.post("/assistant/chat", response_model=Message)
async def send_message(
    message: MessageCreate,
    session_id: Optional[str] = Query(None, description="Session ID for conversation context"),
    user_id: str = Depends(get_current_user_id)
):
    """Send a message to the AI assistant and get a response."""
    try:
        supabase = get_supabase_client()

        # Save user message
        user_message_data = {
            "user_id": user_id,
            "session_id": session_id,
            "role": "user",
            "content": message.content
        }

        user_response = supabase.table("assistant_messages").insert(user_message_data).execute()

        if not user_response.data:
            raise HTTPException(status_code=500, detail="Failed to save user message")

        # Get conversation history for context
        conversation_history = []
        if session_id:
            history_response = supabase.table("assistant_messages").select("*").eq("session_id", session_id).order("created_at").execute()
            conversation_history = [
                {"role": msg["role"], "text": msg["content"]}
                for msg in history_response.data[-10:]  # Last 10 messages for context
            ]
        else:
            # Use just the current message if no session
            conversation_history = [{"role": "user", "text": message.content}]

        # Get AI response
        try:
            ai_client = get_yandex_gpt_client()
            ai_response_text = await ai_client.chat(conversation_history)
        except Exception as ai_error:
            logger.error(f"AI service error: {ai_error}")
            ai_response_text = "Извините, но AI-ассистент временно недоступен. Попробуйте позже."

        # Save AI response
        ai_message_data = {
            "user_id": user_id,
            "session_id": session_id,
            "role": "assistant",
            "content": ai_response_text
        }

        ai_response = supabase.table("assistant_messages").insert(ai_message_data).execute()

        if not ai_response.data:
            raise HTTPException(status_code=500, detail="Failed to save AI response")

        return Message(**ai_response.data[0])

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in assistant chat: {e}")
        raise HTTPException(status_code=500, detail="Failed to process message")

@router.get("/assistant/messages", response_model=List[Message])
async def get_messages(
    session_id: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    user_id: str = Depends(get_current_user_id)
):
    """Get assistant messages with optional session filter."""
    try:
        supabase = get_supabase_client()

        query = supabase.table("assistant_messages").select("*").eq("user_id", user_id)

        if session_id:
            query = query.eq("session_id", session_id)

        query = query.order("created_at").range(skip, skip + limit - 1)

        response = query.execute()

        return [Message(**msg) for msg in response.data]
    except Exception as e:
        logger.error(f"Error fetching messages: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch messages")

@router.post("/assistant/sessions", response_model=AssistantSession)
async def create_session(
    session: AssistantSessionCreate,
    user_id: str = Depends(get_current_user_id)
):
    """Create a new assistant session."""
    try:
        supabase = get_supabase_client()

        session_data = {
            "user_id": user_id,
            "title": session.title
        }

        response = supabase.table("assistant_sessions").insert(session_data).execute()

        if not response.data:
            raise HTTPException(status_code=500, detail="Failed to create session")

        return AssistantSession(**response.data[0])
    except Exception as e:
        logger.error(f"Error creating session: {e}")
        raise HTTPException(status_code=500, detail="Failed to create session")

@router.get("/assistant/sessions", response_model=List[AssistantSession])
async def get_sessions(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    user_id: str = Depends(get_current_user_id)
):
    """Get user's assistant sessions."""
    try:
        supabase = get_supabase_client()

        response = supabase.table("assistant_sessions").select("*").eq("user_id", user_id).order("updated_at", desc=True).range(skip, skip + limit - 1).execute()

        return [AssistantSession(**session) for session in response.data]
    except Exception as e:
        logger.error(f"Error fetching sessions: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch sessions")

@router.delete("/assistant/sessions/{session_id}")
async def delete_session(
    session_id: str,
    user_id: str = Depends(get_current_user_id)
):
    """Delete an assistant session."""
    try:
        supabase = get_supabase_client()

        # Delete the session (messages will be cascade deleted due to foreign key constraint)
        response = supabase.table("assistant_sessions").delete().eq("id", session_id).eq("user_id", user_id).execute()

        if not response.data:
            raise HTTPException(status_code=404, detail="Session not found")

        return {"message": "Session deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting session {session_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete session")


@router.post("/send-message")
async def chat_with_assistant(request: dict):
    """Send a message to the AI assistant."""
    try:
        message = request.get("message")
        user_id = request.get("user_id")

        if not message or not user_id:
            return {"error": "Message and user_id are required"}

        # Simple response for now
        return {
            "status": "Message received",
            "message": f"Вы сказали: {message}",
            "user_id": user_id
        }

    except Exception as e:
        logger.error(f"Chat error: {e}")
        return {"error": "Failed to process message"}
