from fastapi import APIRouter, Depends, HTTPException, Request, Header
from sqlalchemy.orm import Session
from typing import Optional
from app.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.schemas.subscription import PaymentCheckoutRequest, PaymentCheckoutResponse
from app.services.stripe_service import StripeService

router = APIRouter(prefix="/api/payment", tags=["Payment"])


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
