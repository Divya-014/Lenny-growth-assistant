from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

class ChatRequest(BaseModel):
    """
    Schema for incoming chat query requests.
    """
    session_id: str = Field(
        ..., 
        description="The unique identifier for the user session.",
        examples=["session_123"]
    )
    message: str = Field(
        ..., 
        description="The query/question text written by the user.",
        examples=["How do I set up a growth loop?"]
    )
    provider: str = Field(
        default="openai", 
        description="The LLM provider to handle the inference (e.g. 'openai', 'anthropic', 'ollama').",
        examples=["openai"]
    )

class ChatResponse(BaseModel):
    """
    Schema for chat response payloads.
    """
    response: str = Field(
        ..., 
        description="The generated markdown assistant answer response.",
        examples=["Backend working."]
    )
    answer: Optional[str] = Field(
        None,
        description="The generated markdown assistant answer response (equivalent to response)."
    )
    retrieved_sources: Optional[List[Dict[str, Any]]] = Field(
        default=[],
        description="The metadata and contents of retrieved transcript source chunks used to generate the answer."
    )
    session_id: Optional[str] = Field(
        None,
        description="The session identifier associated with this chat response."
    )
    type: Optional[str] = Field(
        None,
        description="The type of response (e.g. 'artifact' or None for standard)"
    )
    language: Optional[str] = Field(
        None,
        description="The programming language or file extension of the artifact"
    )
    content: Optional[str] = Field(
        None,
        description="The raw code or text content of the artifact"
    )



class ChatSessionResponse(BaseModel):
    """
    Schema for a chat session.
    """
    id: str
    title: str
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

class ChatMessageResponse(BaseModel):
    """
    Schema for a chat message record.
    """
    id: str
    session_id: str
    role: str
    content: str
    model_used: str
    created_at: Optional[str] = None

    model_config = {
        "protected_namespaces": ()
    }

