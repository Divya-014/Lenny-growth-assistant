from fastapi import APIRouter, HTTPException, status
from app.models.chat import ChatRequest, ChatResponse
from app.services.chat_service import chat_service
from app.utils.logger import logger

router = APIRouter()

@router.post("/chat", response_model=ChatResponse, status_code=status.HTTP_200_OK, tags=["Conversational Agent"])
async def post_chat(request: ChatRequest):
    """
    Submit user queries to trigger chat saves and responses.
    """
    try:
        response = await chat_service.process_message(request)
        return response
    except Exception as e:
        logger.error(f"Failed to process chat: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while processing the chat session."
        )
