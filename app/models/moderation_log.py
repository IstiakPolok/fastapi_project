from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime
from sqlalchemy.sql import func
from app.database import Base


class ModerationLog(Base):
    """Logs AI responses flagged by the content moderation filter."""
    __tablename__ = "moderation_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    message_content = Column(Text, nullable=False)   # The user's message
    ai_response = Column(Text, nullable=True)         # The AI's response (if generated)
    reason = Column(String(500), nullable=False)       # Why it was flagged
    created_at = Column(DateTime(timezone=True), server_default=func.now())
