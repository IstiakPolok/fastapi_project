from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.schemas.chat import ChatRequest, ChatResponse, ChatHistory
from app.models.user import User
from app.models.chat import Chat
from app.core.dependencies import get_current_user
from app.services.ai_service import get_ai_response, save_chat

router = APIRouter(prefix="/api/chat", tags=["Chat"])


@router.post("", response_model=ChatResponse)
async def send_message(
    chat_request: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Send a message to AI and get response"""
    try:
        # Get AI response
        ai_response = await get_ai_response(
            user_id=current_user.id,
            message=chat_request.message,
            db=db
        )
        
        # Save chat to database
        chat = save_chat(
            db=db,
            user_id=current_user.id,
            message=chat_request.message,
            response=ai_response
        )
        
        return ChatResponse(
            message=chat.message,
            response=chat.response,
            created_at=chat.created_at
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get AI response: {str(e)}"
        )


@router.get("/history", response_model=ChatHistory)
async def get_chat_history(
    limit: int = 50,
    offset: int = 0,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get chat history for current user"""
    # Get total count
    total = db.query(Chat).filter(Chat.user_id == current_user.id).count()
    
    # Get chats with pagination
    chats = db.query(Chat).filter(
        Chat.user_id == current_user.id
    ).order_by(Chat.created_at.desc()).offset(offset).limit(limit).all()
    
    chat_responses = [
        ChatResponse(
            message=chat.message,
            response=chat.response,
            created_at=chat.created_at
        )
        for chat in chats
    ]
    
    return ChatHistory(chats=chat_responses, total=total)


@router.delete("/history")
async def clear_chat_history(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Clear all chat history for current user"""
    deleted_count = db.query(Chat).filter(Chat.user_id == current_user.id).delete()
    db.commit()
    
    return {"message": f"Deleted {deleted_count} chat messages"}
