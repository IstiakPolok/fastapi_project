"""
Chat Routes — Single-Thread Senior Companion.

There is only ONE continuous conversation per user.  No sessions, no
"new chat" — just a unified timeline.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.schemas.chat import ChatRequest, ChatResponse, ChatHistory
from app.models.user import User
from app.models.chat import Chat
from app.core.dependencies import get_current_user
from app.services.ai_service import get_ai_response, save_chat, check_moderation
from app.services.memory_service import soft_delete_memories

router = APIRouter(prefix="/api/chat", tags=["Chat"])


# --------------------------------------------------------------------------- #
#  POST /api/chat — Send a message (single-thread)
# --------------------------------------------------------------------------- #

@router.post("", response_model=ChatResponse)
async def send_message(
    chat_request: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Send a message to the AI companion and receive a response.

    The conversation is always one continuous thread per user.  The AI
    uses the user's name, long-term RAG memory, and the last 10 messages
    as context.
    """
    try:
        # 1. Get AI response (with RAG + sliding window + identity)
        ai_response = await get_ai_response(
            user_id=current_user.id,
            user_name=current_user.name,
            message=chat_request.message,
            db=db,
        )

        # 2. Save to PostgreSQL + ChromaDB
        chat = save_chat(
            db=db,
            user_id=current_user.id,
            message=chat_request.message,
            response=ai_response,
        )

        # 3. Moderation check (non-blocking — always returns the response)
        check_moderation(db, current_user.id, chat_request.message, ai_response)

        return ChatResponse(
            id=chat.id,
            message=chat.message,
            response=chat.response,
            created_at=chat.created_at,
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get AI response: {str(e)}",
        )


# --------------------------------------------------------------------------- #
#  GET /api/chat/history — Unified timeline
# --------------------------------------------------------------------------- #

@router.get("/history", response_model=ChatHistory)
async def get_chat_history(
    limit: int = 50,
    offset: int = 0,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Return the unified conversation history for the current user.
    Soft-deleted messages are **never** shown.
    """
    # Total count (non-deleted only)
    total = (
        db.query(Chat)
        .filter(Chat.user_id == current_user.id, Chat.is_deleted == False)
        .count()
    )

    # Paginated results (non-deleted, chronological)
    chats = (
        db.query(Chat)
        .filter(Chat.user_id == current_user.id, Chat.is_deleted == False)
        .order_by(Chat.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )

    chat_responses = [
        ChatResponse(
            id=chat.id,
            message=chat.message,
            response=chat.response,
            created_at=chat.created_at,
        )
        for chat in chats
    ]

    return ChatHistory(chats=chat_responses, total=total)


# --------------------------------------------------------------------------- #
#  DELETE /api/chat/history — Soft delete
# --------------------------------------------------------------------------- #

@router.delete("/history")
async def clear_chat_history(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Soft-delete all chat history for the current user.
    Sets ``is_deleted = True`` — records are kept but hidden from the AI
    and from history queries.  ChromaDB embeddings are also removed.
    """
    # Find all non-deleted chats
    chats_to_delete = (
        db.query(Chat)
        .filter(Chat.user_id == current_user.id, Chat.is_deleted == False)
        .all()
    )

    if not chats_to_delete:
        return {"message": "No chat messages to delete"}

    chat_ids = [chat.id for chat in chats_to_delete]

    # Soft-delete in PostgreSQL
    (
        db.query(Chat)
        .filter(Chat.id.in_(chat_ids))
        .update({Chat.is_deleted: True}, synchronize_session="fetch")
    )
    db.commit()

    # Remove embeddings from ChromaDB
    try:
        soft_delete_memories(current_user.id, chat_ids)
    except Exception:
        pass  # Non-critical

    return {"message": f"Soft-deleted {len(chat_ids)} chat messages"}
