import anyio
from fastapi import APIRouter, HTTPException, status
from typing import List
from app.models.chat import ChatSessionResponse, ChatMessageResponse
from app.database.connection import supabase_db
from app.utils.logger import logger

router = APIRouter()

class CreateSessionRequest(anyio.abc.AsyncResource):
    pass # Empty helper if needed, but a simple schema is better:

from pydantic import BaseModel
class CreateSessionBody(BaseModel):
    title: str

@router.post("/sessions", response_model=ChatSessionResponse, status_code=status.HTTP_201_CREATED, tags=["Sessions"])
async def create_session(body: CreateSessionBody):
    """
    Creates a new chat session database record.
    """
    try:
        session = await anyio.to_thread.run_sync(
            supabase_db.create_chat_session,
            body.title
        )
        return session
    except Exception as e:
        logger.error(f"Failed to create session: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not create chat session."
        )

@router.get("/sessions", response_model=List[ChatSessionResponse], tags=["Sessions"])
async def get_sessions():
    """
    Lists all chat sessions.
    """
    try:
        sessions = await anyio.to_thread.run_sync(supabase_db.get_chat_sessions)
        return sessions
    except Exception as e:
        logger.error(f"Failed to retrieve sessions: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not retrieve chat sessions."
        )

@router.get("/sessions/{session_id}/messages", response_model=List[ChatMessageResponse], tags=["Sessions"])
async def get_session_messages(session_id: str):
    """
    Retrieves all chat messages associated with a session ID.
    """
    try:
        messages = await anyio.to_thread.run_sync(
            supabase_db.get_messages,
            session_id
        )
        return messages
    except Exception as e:
        logger.error(f"Failed to retrieve messages: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not retrieve messages for session."
        )
