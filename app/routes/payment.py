from fastapi import APIRouter, Depends, HTTPException, Request, Header
from sqlalchemy.orm import Session
from typing import Optional
from app.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.models.subscription import SubscriptionPlan, UserSubscription
from app.schemas.subscription import (
    PaymentCheckoutRequest, 
    PaymentCheckoutResponse,
    UserPlanResponse,
    UserPlanListResponse
)
from app.services.stripe_service import StripeService
from app.services.activity_service import ActivityService

router = APIRouter(prefix="/api/payment", tags=["Payment"])


@router.get("/plans", response_model=UserPlanListResponse)
async def list_user_plans(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get all active subscription plans with the current user's purchase status
    """
    # 1. Fetch all active subscription plans
    plans = db.query(SubscriptionPlan).filter(SubscriptionPlan.is_active == True).order_by(SubscriptionPlan.price.asc()).all()
    
    # 2. Fetch all active subscriptions for the current user
    user_subscriptions = db.query(UserSubscription).filter(
        UserSubscription.user_id == current_user.id,
        UserSubscription.status == "active",
        UserSubscription.payment_status == "completed"
    ).all()
    
    # 3. Create a map of plan_id to active subscription for quick lookup
    sub_map = {sub.plan_id: sub for sub in user_subscriptions}
    
    # 4. Map plans to UserPlanResponse
    result_plans = []
    for plan in plans:
        active_sub = sub_map.get(plan.id)
        
        user_plan = UserPlanResponse(
            id=plan.id,
            name=plan.name,
            description=plan.description,
            price=plan.price,
            duration_days=plan.duration_days,
            features=plan.features,
            is_active=plan.is_active,
            created_at=plan.created_at,
            is_purchased=active_sub is not None,
            subscription_id=active_sub.id if active_sub else None,
            expiry_date=active_sub.end_date if active_sub else None
        )
        result_plans.append(user_plan)
        
    return UserPlanListResponse(
        plans=result_plans,
        total_count=len(result_plans)
    )


@router.post("/create-checkout", response_model=PaymentCheckoutResponse)
async def create_checkout_session(
    request: PaymentCheckoutRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a Stripe checkout session for a subscription plan
    
    Requires authentication via Bearer token
    
    Args:
        request: Contains plan_id
        current_user: Authenticated user from token
        db: Database session
        
    Returns:
        PaymentCheckoutResponse with checkout_url and session_id
    """
    result = await StripeService.create_checkout_session(
        plan_id=request.plan_id,
        user_id=current_user.id,
        user_email=current_user.email,
        db=db
    )
    
    return PaymentCheckoutResponse(
        checkout_url=result["checkout_url"],
        session_id=result["session_id"]
    )


@router.post("/webhook")
async def stripe_webhook(
    request: Request,
    stripe_signature: Optional[str] = Header(None, alias="stripe-signature"),
    db: Session = Depends(get_db)
):
    """
    Handle Stripe webhook events
    
    This endpoint is called by Stripe to notify about payment events.
    No authentication required as it's verified by Stripe signature.
    
    Args:
        request: Raw request from Stripe
        stripe_signature: Stripe signature header for verification
        db: Database session
        
    Returns:
        Success status
    """
    payload = await request.body()
    
    if not stripe_signature:
        raise HTTPException(status_code=400, detail="Missing stripe-signature header")
    
    result = await StripeService.handle_webhook_event(
        payload=payload,
        signature=stripe_signature,
        db=db
    )
    
    return result


@router.get("/success")
async def payment_success(
    session_id: str,
    db: Session = Depends(get_db)
):
    """
    Payment success callback endpoint
    
    This endpoint is called after successful payment.
    Verifies the payment and returns subscription details.
    
    Args:
        session_id: Stripe checkout session ID
        db: Database session
        
    Returns:
        Success message with subscription details
    """
    subscription = await StripeService.verify_session(session_id, db)
    
    if not subscription:
        raise HTTPException(
            status_code=404,
            detail="Payment session not found or not completed"
        )
    
    # Log activity
    ActivityService.log_activity(
        db=db,
        user_id=subscription.user_id,
        action="subscription_success",
        description=f"User subscribed to plan {subscription.plan_id}",
        # Request is not easily available here without changing signature, but verify_session is usually called from client redirect
        # We'll skip request for now or add it to signature if needed.
    )
    
    return {
        "status": "success",
        "message": "Payment completed successfully",
        "subscription": {
            "id": subscription.id,
            "plan_id": subscription.plan_id,
            "status": subscription.status,
            "payment_status": subscription.payment_status,
            "start_date": subscription.start_date,
            "end_date": subscription.end_date
        }
    }


@router.get("/cancel")
async def payment_cancel():
    """
    Payment cancellation callback endpoint
    
    This endpoint is called when user cancels the payment.
    
    Returns:
        Cancellation message
    """
    return {
        "status": "cancelled",
        "message": "Payment was cancelled. You can try again anytime."
    }
