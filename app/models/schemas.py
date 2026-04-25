"""
Pydantic schemas for the application.
"""
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    """Schema for a single chat message."""

    role: str = Field(..., description="Role of the sender: 'user' or 'model'")
    content: str = Field(..., description="Content of the message")


class ChatRequest(BaseModel):
    """Schema for an incoming chat request."""

    session_id: str = Field(..., description="Unique session ID for the user")
    message: str = Field(..., description="The user's query")
    language: str = Field(
        default="en", description="Target language code (e.g., 'en', 'hi')"
    )


class ChatResponse(BaseModel):
    """Schema for the outgoing chat response."""

    response: str = Field(..., description="The assistant's reply")
    suggested_actions: List[str] = Field(
        default_factory=list, description="Follow-up suggestions"
    )
    timeline_event: Optional[Dict[str, Any]] = Field(
        default=None, description="Structured election timeline step if applicable"
    )
