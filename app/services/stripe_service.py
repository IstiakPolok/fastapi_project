import stripe
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import Optional
from app.config import settings
from app.models.subscription import SubscriptionPlan, UserSubscription
from fastapi import HTTPException

# Initialize Stripe
stripe.api_key = settings.STRIPE_SECRET_KEY


class StripeService:
    """Service for handling Stripe payment operations"""
    
    @staticmethod
    async def create_checkout_session(
        plan_id: int,
        user_id: int,
        user_email: str,
        db: Session
    ) -> dict:
        """
        Create a Stripe checkout session for a subscription plan
        
        Args:
            plan_id: ID of the subscription plan
            user_id: ID of the user making the purchase
            user_email: Email of the user
            db: Database session
            
        Returns:
            dict with checkout_url and session_id
        """
        # Fetch the subscription plan
        plan = db.query(SubscriptionPlan).filter(
            SubscriptionPlan.id == plan_id,
            SubscriptionPlan.is_active == True
        ).first()
        
        if not plan:
            raise HTTPException(status_code=404, detail="Subscription plan not found or inactive")
        
        try:
            # Create Stripe checkout session
            checkout_session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=[
                    {
                        'price_data': {
                            'currency': 'usd',
                            'unit_amount': int(plan.price * 100),  # Convert to cents
                            'product_data': {
                                'name': plan.name,
                                'description': plan.description or f"{plan.duration_days} days subscription",
                            },
                        },
                        'quantity': 1,
                    },
                ],
                mode='payment',
                success_url=f"{settings.FRONTEND_URL}/payment/success?session_id={{CHECKOUT_SESSION_ID}}",
                cancel_url=f"{settings.FRONTEND_URL}/payment/cancel",
                customer_email=user_email,
                metadata={
                    'user_id': str(user_id),
                    'plan_id': str(plan_id),
                    'plan_name': plan.name,
                    'duration_days': str(plan.duration_days),
                },
            )
            
            # Calculate subscription end date
            end_date = datetime.utcnow() + timedelta(days=plan.duration_days)
            
            # Create a pending subscription record
            subscription = UserSubscription(
                user_id=user_id,
                plan_id=plan_id,
                start_date=datetime.utcnow(),
                end_date=end_date,
                status="pending",
                payment_amount=plan.price,
                stripe_session_id=checkout_session.id,
                payment_status="pending"
            )
            
            db.add(subscription)
            db.commit()
            db.refresh(subscription)
            
            return {
                "checkout_url": checkout_session.url,
                "session_id": checkout_session.id
            }
            
        except stripe.error.StripeError as e:
            raise HTTPException(status_code=400, detail=f"Stripe error: {str(e)}")
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=f"Error creating checkout session: {str(e)}")
    
    
    @staticmethod
    async def handle_webhook_event(
        payload: bytes,
        signature: str,
        db: Session
    ) -> dict:
        """
        Handle Stripe webhook events
        
        Args:
            payload: Raw request payload
            signature: Stripe signature header
            db: Database session
            
        Returns:
            dict with status message
        """
        if not settings.STRIPE_WEBHOOK_SECRET:
            # If no webhook secret is configured, skip verification (not recommended for production)
            event = stripe.Event.construct_from(
                stripe.util.json.loads(payload), stripe.api_key
            )
        else:
            try:
                event = stripe.Webhook.construct_event(
                    payload, signature, settings.STRIPE_WEBHOOK_SECRET
                )
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid payload")
            except stripe.error.SignatureVerificationError:
                raise HTTPException(status_code=400, detail="Invalid signature")
        
        # Handle the event
        if event['type'] == 'checkout.session.completed':
            session = event['data']['object']
            await StripeService._handle_successful_payment(session, db)
        
        elif event['type'] == 'checkout.session.expired':
            session = event['data']['object']
            await StripeService._handle_expired_session(session, db)
        
        elif event['type'] == 'payment_intent.succeeded':
            payment_intent = event['data']['object']
            await StripeService._handle_payment_intent_succeeded(payment_intent, db)
        
        return {"status": "success"}
    
    
    @staticmethod
    async def _handle_successful_payment(session: dict, db: Session):
        """Handle successful payment completion"""
        session_id = session.get('id')
        payment_intent_id = session.get('payment_intent')
        
        # Find the subscription by session ID
        subscription = db.query(UserSubscription).filter(
            UserSubscription.stripe_session_id == session_id
        ).first()
        
        if subscription:
            subscription.status = "active"
            subscription.payment_status = "completed"
            subscription.stripe_payment_intent_id = payment_intent_id
            db.commit()
    
    
    @staticmethod
    async def _handle_expired_session(session: dict, db: Session):
        """Handle expired checkout session"""
        session_id = session.get('id')
        
        # Find the subscription by session ID
        subscription = db.query(UserSubscription).filter(
            UserSubscription.stripe_session_id == session_id
        ).first()
        
        if subscription:
            subscription.status = "cancelled"
            subscription.payment_status = "failed"
            db.commit()
    
    
    @staticmethod
    async def _handle_payment_intent_succeeded(payment_intent: dict, db: Session):
        """Handle payment intent succeeded event"""
        payment_intent_id = payment_intent.get('id')
        
        # Find the subscription by payment intent ID
        subscription = db.query(UserSubscription).filter(
            UserSubscription.stripe_payment_intent_id == payment_intent_id
        ).first()
        
        if subscription and subscription.payment_status != "completed":
            subscription.payment_status = "completed"
            subscription.status = "active"
            db.commit()
    
    
    @staticmethod
    async def verify_session(session_id: str, db: Session) -> Optional[UserSubscription]:
        """
        Verify a Stripe checkout session and return the subscription
        
        Args:
            session_id: Stripe checkout session ID
            db: Database session
            
        Returns:
            UserSubscription if found and verified, None otherwise
        """
        try:
            # Retrieve session from Stripe
            session = stripe.checkout.Session.retrieve(session_id)
            
            # Find subscription in database
            subscription = db.query(UserSubscription).filter(
                UserSubscription.stripe_session_id == session_id
            ).first()
            
            if subscription and session.payment_status == 'paid':
                # Update subscription if payment is confirmed
                if subscription.payment_status != "completed":
                    subscription.payment_status = "completed"
                    subscription.status = "active"
                    subscription.stripe_payment_intent_id = session.payment_intent
                    db.commit()
                    db.refresh(subscription)
                
                return subscription
            
            return None
            
        except stripe.error.StripeError:
            return None
