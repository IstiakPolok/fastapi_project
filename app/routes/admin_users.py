from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional
from app.database import get_db
from app.models.user import User
from app.models.admin import Admin
from app.models.subscription import UserSubscription
from app.schemas.user_admin import UserListItem, UserListResponse, UserStatusUpdate, UserDetailResponse
from app.core.admin_dependencies import get_current_admin

router = APIRouter(prefix="/api/admin/users", tags=["Admin - User Management"])


@router.get("", response_model=UserListResponse)
async def list_users(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=100),
    search: Optional[str] = None,
    status_filter: Optional[str] = Query(default=None, description="active, inactive, or all"),
    db: Session = Depends(get_db),
    admin: Admin = Depends(get_current_admin)
):
    """Get paginated list of users with optional filtering"""
    query = db.query(User)
    
    # Apply search filter
    if search:
        query = query.filter(
            (User.name.ilike(f"%{search}%")) | 
            (User.email.ilike(f"%{search}%"))
        )
    
    # Apply status filter
    if status_filter == "active":
        query = query.filter(User.is_active == True)
    elif status_filter == "inactive":
        query = query.filter(User.is_active == False)
    
    # Get total count
    total_count = query.count()
    
    # Apply pagination
    offset = (page - 1) * page_size
    users = query.order_by(User.created_at.desc()).offset(offset).limit(page_size).all()
    
    # Build response with subscription status
    user_items = []
    for user in users:
        # Get latest subscription status
        subscription = db.query(UserSubscription).filter(
            UserSubscription.user_id == user.id
        ).order_by(UserSubscription.created_at.desc()).first()
        
        subscription_status = None
        if subscription:
            subscription_status = subscription.status
        
        user_items.append(UserListItem(
            id=user.id,
            name=user.name,
            email=user.email,
            is_active=user.is_active,
            created_at=user.created_at,
            subscription_status=subscription_status
        ))
    
    return UserListResponse(
        users=user_items,
        total_count=total_count,
        page=page,
        page_size=page_size
    )


@router.get("/{user_id}", response_model=UserDetailResponse)
async def get_user_details(
    user_id: int,
    db: Session = Depends(get_db),
    admin: Admin = Depends(get_current_admin)
):
    """Get detailed user information"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Get subscription info
    subscription = db.query(UserSubscription).filter(
        UserSubscription.user_id == user_id
    ).order_by(UserSubscription.created_at.desc()).first()
    
    subscription_info = None
    if subscription:
        subscription_info = {
            "plan_id": subscription.plan_id,
            "status": subscription.status,
            "start_date": subscription.start_date.isoformat() if subscription.start_date else None,
            "end_date": subscription.end_date.isoformat() if subscription.end_date else None
        }
    
    return UserDetailResponse(
        id=user.id,
        name=user.name,
        email=user.email,
        is_active=user.is_active,
        created_at=user.created_at,
        updated_at=user.updated_at,
        subscription=subscription_info
    )


@router.put("/{user_id}/status")
async def update_user_status(
    user_id: int,
    status_data: UserStatusUpdate,
    db: Session = Depends(get_db),
    admin: Admin = Depends(get_current_admin)
):
    """Activate or deactivate a user"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    user.is_active = status_data.is_active
    db.commit()
    
    status_text = "activated" if status_data.is_active else "deactivated"
    return {"message": f"User {status_text} successfully"}


@router.delete("/{user_id}")
async def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    admin: Admin = Depends(get_current_admin)
):
    """Delete a user"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Delete related subscriptions first
    db.query(UserSubscription).filter(UserSubscription.user_id == user_id).delete()
    
    # Delete user
    db.delete(user)
    db.commit()
    
    return {"message": "User deleted successfully"}
