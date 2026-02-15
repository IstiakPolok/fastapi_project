from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


# Subscription Plan Schemas
class PlanCreate(BaseModel):
    name: str
    description: Optional[str] = None
    price: float
    duration_days: int
    features: Optional[List[str]] = None


class PlanUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    duration_days: Optional[int] = None
    features: Optional[List[str]] = None
    is_active: Optional[bool] = None


class PlanResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    price: float
    duration_days: int
    features: Optional[List[str]]
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class PlanListResponse(BaseModel):
    plans: List[PlanResponse]
    total_count: int


# User Subscription Schemas
class UserSubscriptionResponse(BaseModel):
    id: int
    user_id: int
    plan_id: int
    plan_name: str
    start_date: datetime
    end_date: datetime
    status: str
    payment_amount: Optional[float]

    class Config:
        from_attributes = True


# Payment Schemas
class PaymentCheckoutRequest(BaseModel):
    plan_id: int


class PaymentCheckoutResponse(BaseModel):
    checkout_url: str
    session_id: str


class PaymentWebhookEvent(BaseModel):
    type: str
    data: dict
