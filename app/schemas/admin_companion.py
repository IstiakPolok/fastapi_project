from pydantic import BaseModel
from datetime import datetime
from typing import List


class AdminSummaryResponse(BaseModel):
    """Schema for admin emotional-status summary of a user."""
    user_id: int
    user_name: str
    emotional_summary: str
    message_count: int
    generated_at: datetime


class AdminChatResponse(BaseModel):
    """Chat message visible to admin — includes soft-delete status."""
    id: int
    user_id: int
    message: str
    response: str
    is_deleted: bool
    created_at: datetime

    class Config:
        from_attributes = True


class AdminChatHistory(BaseModel):
    """Admin view of a user's full chat history (active + soft-deleted)."""
    user_name: str
    chats: List[AdminChatResponse]
    total: int
    active_count: int
    deleted_count: int

