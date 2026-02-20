"""
Admin Companion Routes — Protected endpoints for admin oversight.

Admins can:
- View an AI-generated emotional-status summary of any user
- View all chats (active + soft-deleted)
- Soft-delete or permanently delete a user's chat data
Raw chat logs are shown only to admins, never to the AI after deletion.
"""

from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import Optional

from app.database import get_db
from app.models.admin import Admin
from app.models.user import User
from app.models.chat import Chat
from app.core.admin_dependencies import get_current_admin
from app.schemas.admin_companion import (
    AdminSummaryResponse,
    AdminChatResponse,
    AdminChatHistory,
)
from app.services.ai_service import generate_admin_summary
from app.services.memory_service import soft_delete_memories

router = APIRouter(prefix="/api/admin", tags=["Admin Companion"])


# --------------------------------------------------------------------------- #
#  GET /api/admin/summary/{user_id} — Emotional status summary
# --------------------------------------------------------------------------- #

@router.get("/summary/{user_id}", response_model=AdminSummaryResponse)
async def get_user_summary(
    user_id: int,
    admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """
    Get a 3-sentence AI-generated emotional-status summary for the
    specified user.  The admin **never** sees raw chat logs — only
    the synthesised summary.
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    try:
        summary = await generate_admin_summary(user_id, user.name, db)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate summary: {str(e)}",
        )

    message_count = (
        db.query(Chat)
        .filter(Chat.user_id == user_id, Chat.is_deleted == False)
        .count()
    )

    return AdminSummaryResponse(
        user_id=user_id,
        user_name=user.name,
        emotional_summary=summary,
        message_count=message_count,
        generated_at=datetime.now(timezone.utc),
    )


# --------------------------------------------------------------------------- #
#  GET /api/admin/chat/{user_id} — View ALL chats (active + soft-deleted)
# --------------------------------------------------------------------------- #

@router.get("/chat/{user_id}", response_model=AdminChatHistory)
async def admin_get_user_chats(
    user_id: int,
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    filter: Optional[str] = Query(
        default=None,
        description="Filter chats: 'active', 'deleted', or omit for all",
    ),
    admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """
    View a user's full chat history including soft-deleted messages.
    Admins can filter by 'active' or 'deleted', or see all.
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    # Base query
    query = db.query(Chat).filter(Chat.user_id == user_id)

    # Optional filter
    if filter == "active":
        query = query.filter(Chat.is_deleted == False)
    elif filter == "deleted":
        query = query.filter(Chat.is_deleted == True)

    total = query.count()

    chats = (
        query.order_by(Chat.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )

    # Counts
    active_count = (
        db.query(Chat)
        .filter(Chat.user_id == user_id, Chat.is_deleted == False)
        .count()
    )
    deleted_count = (
        db.query(Chat)
        .filter(Chat.user_id == user_id, Chat.is_deleted == True)
        .count()
    )

    chat_responses = [
        AdminChatResponse(
            id=chat.id,
            user_id=chat.user_id,
            message=chat.message,
            response=chat.response,
            is_deleted=chat.is_deleted,
            created_at=chat.created_at,
        )
        for chat in chats
    ]

    return AdminChatHistory(
        user_name=user.name,
        chats=chat_responses,
        total=total,
        active_count=active_count,
        deleted_count=deleted_count,
    )


# --------------------------------------------------------------------------- #
#  DELETE /api/admin/chat/{user_id} — Soft-delete or permanent delete
# --------------------------------------------------------------------------- #

@router.delete("/chat/{user_id}")
async def admin_delete_user_chat(
    user_id: int,
    permanent: bool = Query(
        default=False,
        description="If true, permanently removes chats from the database. "
                    "If false (default), performs a soft-delete.",
    ),
    admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """
    Delete a user's chat history.

    - **permanent=false** (default): soft-delete — sets `is_deleted = True`
      on active chats and removes ChromaDB embeddings.
    - **permanent=true**: permanently removes ALL chats (including already
      soft-deleted ones) from PostgreSQL and ChromaDB.
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    if permanent:
        # ── Permanent delete: remove ALL chats from DB ──
        all_chats = db.query(Chat).filter(Chat.user_id == user_id).all()

        if not all_chats:
            return {"message": f"No chat messages found for user {user.name}"}

        chat_ids = [chat.id for chat in all_chats]

        db.query(Chat).filter(Chat.id.in_(chat_ids)).delete(
            synchronize_session="fetch"
        )
        db.commit()

        # Remove all embeddings from ChromaDB
        try:
            soft_delete_memories(user_id, chat_ids)
        except Exception:
            pass

        return {
            "message": f"Permanently deleted {len(chat_ids)} chat messages for user {user.name}",
            "user_id": user_id,
            "deleted_count": len(chat_ids),
            "permanent": True,
        }

    else:
        # ── Soft-delete: set is_deleted = True on active chats ──
        active_chats = (
            db.query(Chat)
            .filter(Chat.user_id == user_id, Chat.is_deleted == False)
            .all()
        )

        if not active_chats:
            return {"message": f"No active chat messages found for user {user.name}"}

        chat_ids = [chat.id for chat in active_chats]

        db.query(Chat).filter(Chat.id.in_(chat_ids)).update(
            {Chat.is_deleted: True}, synchronize_session="fetch"
        )
        db.commit()

        try:
            soft_delete_memories(user_id, chat_ids)
        except Exception:
            pass

        return {
            "message": f"Soft-deleted {len(chat_ids)} chat messages for user {user.name}",
            "user_id": user_id,
            "deleted_count": len(chat_ids),
            "permanent": False,
        }

