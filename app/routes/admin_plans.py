from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models.admin import Admin
from app.models.subscription import SubscriptionPlan
from app.schemas.subscription import PlanCreate, PlanUpdate, PlanResponse, PlanListResponse
from app.core.admin_dependencies import get_current_admin

router = APIRouter(prefix="/api/admin/plans", tags=["Admin - Subscription Plans"])


@router.get("", response_model=PlanListResponse)
async def list_plans(
    include_inactive: bool = False,
    db: Session = Depends(get_db),
    admin: Admin = Depends(get_current_admin)
):
    """Get all subscription plans"""
    query = db.query(SubscriptionPlan)
    
    if not include_inactive:
        query = query.filter(SubscriptionPlan.is_active == True)
    
    plans = query.order_by(SubscriptionPlan.price.asc()).all()
    total_count = query.count()
    
    return PlanListResponse(
        plans=[PlanResponse.model_validate(plan) for plan in plans],
        total_count=total_count
    )


@router.get("/{plan_id}", response_model=PlanResponse)
async def get_plan(
    plan_id: int,
    db: Session = Depends(get_db),
    admin: Admin = Depends(get_current_admin)
):
    """Get a specific subscription plan"""
    plan = db.query(SubscriptionPlan).filter(SubscriptionPlan.id == plan_id).first()
    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Plan not found"
        )
    return plan


@router.post("", response_model=PlanResponse, status_code=status.HTTP_201_CREATED)
async def create_plan(
    plan_data: PlanCreate,
    db: Session = Depends(get_db),
    admin: Admin = Depends(get_current_admin)
):
    """Create a new subscription plan"""
    # Check if plan with same name exists
    existing_plan = db.query(SubscriptionPlan).filter(
        SubscriptionPlan.name == plan_data.name
    ).first()
    if existing_plan:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Plan with this name already exists"
        )
    
    new_plan = SubscriptionPlan(
        name=plan_data.name,
        description=plan_data.description,
        price=plan_data.price,
        duration_days=plan_data.duration_days,
        features=plan_data.features,
        is_active=True
    )
    
    db.add(new_plan)
    db.commit()
    db.refresh(new_plan)
    
    return new_plan


@router.put("/{plan_id}", response_model=PlanResponse)
async def update_plan(
    plan_id: int,
    plan_data: PlanUpdate,
    db: Session = Depends(get_db),
    admin: Admin = Depends(get_current_admin)
):
    """Update a subscription plan"""
    plan = db.query(SubscriptionPlan).filter(SubscriptionPlan.id == plan_id).first()
    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Plan not found"
        )
    
    # Update only provided fields
    update_data = plan_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(plan, field, value)
    
    db.commit()
    db.refresh(plan)
    
    return plan


@router.delete("/{plan_id}")
async def delete_plan(
    plan_id: int,
    db: Session = Depends(get_db),
    admin: Admin = Depends(get_current_admin)
):
    """Delete a subscription plan (soft delete - sets inactive)"""
    plan = db.query(SubscriptionPlan).filter(SubscriptionPlan.id == plan_id).first()
    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Plan not found"
        )
    
    # Soft delete - just mark as inactive
    plan.is_active = False
    db.commit()
    
    return {"message": "Plan deleted successfully"}
