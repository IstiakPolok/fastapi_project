from sqlalchemy import Column, Integer, String, Text, Boolean, ForeignKey, DateTime
from sqlalchemy.sql import func
from app.database import Base


class UserMemory(Base):
    """Stores extracted facts/memories from user conversations for RAG retrieval."""
    __tablename__ = "user_memories"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    memory_key = Column(String(255), nullable=False)       # e.g. "granddaughter_name"
    memory_value = Column(Text, nullable=False)             # e.g. "Lily"
    source_message_id = Column(Integer, ForeignKey("chats.id"), nullable=True)
    is_deleted = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
