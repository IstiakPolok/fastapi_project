from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime


# User management schemas for admin
class UserListItem(BaseModel):
    id: int
    name: str
    email: str
    is_active: bool
    created_at: datetime
    subscription_status: Optional[str] = None

    class Config:
        from_attributes = True


class UserListResponse(BaseModel):
    users: List[UserListItem]
    total_count: int
    page: int
    page_size: int


class UserStatusUpdate(BaseModel):
    is_active: bool


class UserDetailResponse(BaseModel):
    id: int
    name: str
    email: str
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime]
    subscription: Optional[dict] = None

    class Config:
        from_attributes = True
