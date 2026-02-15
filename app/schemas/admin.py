from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime


# Admin Schemas
class AdminCreate(BaseModel):
    name: str
    email: EmailStr
    password: str
    confirm_password: str


class AdminLogin(BaseModel):
    email: EmailStr
    password: str


class AdminResponse(BaseModel):
    id: int
    name: str
    email: str
    profile_image_url: Optional[str] = None
    is_superadmin: bool
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class AdminToken(BaseModel):
    access_token: str
    token_type: str = "bearer"


# Dashboard Stats Schemas
class DashboardStats(BaseModel):
    total_users: int
    active_users: int
    inactive_users: int
    engagement_rate: float  # Percentage
    monthly_revenue: float
    total_subscriptions: int
    active_subscriptions: int


class RevenueDataPoint(BaseModel):
    month: str  # e.g., "Jan", "Feb"
    revenue: float


class RevenueChartData(BaseModel):
    data: List[RevenueDataPoint]
    total_revenue: float
    growth_percentage: float


class ActivityItem(BaseModel):
    id: int
    action: str
    description: Optional[str]
    user_email: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class RecentActivityResponse(BaseModel):
    activities: List[ActivityItem]
    total_count: int
