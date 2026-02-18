from pydantic import BaseModel, Field
from datetime import datetime
from typing import List, Optional


class ChatRequest(BaseModel):
    """Schema for chat message request"""
    message: str = Field(..., min_length=1)


class ChatResponse(BaseModel):
    """Schema for chat response"""
    id: int
    message: str
    response: str
    created_at: datetime
    
    class Config:
        from_attributes = True


class ChatHistory(BaseModel):
    """Schema for chat history"""
    chats: List[ChatResponse]
    total: int

