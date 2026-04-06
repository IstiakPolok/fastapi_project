from sqlalchemy.orm import Session
from fastapi import Request
from app.models.activity import ActivityLog
from typing import Optional

class ActivityService:
    @staticmethod
    def log_activity(
        db: Session,
        user_id: Optional[int] = None,
        admin_id: Optional[int] = None,
        action: str = "",
        description: Optional[str] = None,
        request: Optional[Request] = None
    ):
        """
        Log an activity to the database.
        
        Args:
            db: Database session
            user_id: ID of the user performing the action
            admin_id: ID of the admin performing the action
            action: Type of action (e.g., 'login', 'signup', 'chat_message')
            description: Detailed description of the action
            request: FastAPI Request object to extract IP and User-Agent
        """
        ip_address = None
        user_agent = None
        
        if request:
            ip_address = request.client.host if request.client else None
            user_agent = request.headers.get("user-agent")
            
        activity = ActivityLog(
            user_id=user_id,
            admin_id=admin_id,
            action=action,
            description=description,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        db.add(activity)
        db.commit()
        db.refresh(activity)
        return activity
