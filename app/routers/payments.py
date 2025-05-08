from typing import Any, Dict
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy.orm import Session
import stripe
import json
from datetime import datetime

from app.auth.jwt import get_current_active_user
from app.db.database import get_db
from app.models.user import User, UserSubscription
from app.core.config import settings

router = APIRouter()

# Initialize Stripe
stripe.api_key = settings.STRIPE_API_KEY

# Subscription plans with pricing information
PLANS = {
    "basic": {
        "id": settings.BASIC_PLAN_ID,
        "name": "Basic",
        "description": "Access to basic stock prediction features",
        "price_monthly_usd": 9.99,
        "features": [
            "Up to 20 predictions per day",
            "Up to 14 days forecast",
            "LinearRegression and RandomForest models"
        ]
    },
    "pro": {
        "id": settings.PRO_PLAN_ID,
        "name": "Professional",
        "description": "Enhanced prediction capabilities for serious traders",
        "price_monthly_usd": 19.99,
        "features": [
            "Up to 50 predictions per day",
            "Up to 30 days forecast",
            "Access to 4 different prediction models",
            "Priority support"
        ]
    },
    "enterprise": {
        "id": settings.ENTERPRISE_PLAN_ID,
        "name": "Enterprise",
        "description": "Unlimited access for professional trading teams",
        "price_monthly_usd": 49.99,
        "features": [
            "Up to 200 predictions per day",
            "Up to 60 days forecast",
            "Access to all prediction models",
            "Premium support",
            "Bulk API access"
        ]
    }
}

@router.get("/plans")
def get_subscription_plans() -> Dict:
    """
    Get available subscription plans
    """
    return {"plans": PLANS}

@router.post("/create-checkout-session/{plan_id}")
def create_checkout_session(
    plan_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Dict:
    """
    Create a Stripe checkout session for subscription
    """
    if plan_id not in ["basic", "pro", "enterprise"]:
        raise HTTPException(status_code=400, detail="Invalid plan ID")
    
    # Check if user already has an active subscription
    existing_subscription = (
        db.query(UserSubscription)
        .filter(
            UserSubscription.user_id == current_user.id,
            UserSubscription.status == "active"
        )
        .first()
    )
    
    # Set up success and cancel URLs
    success_url = f"{settings.BACKEND_CORS_ORIGINS[0]}/subscription/success"
    cancel_url = f"{settings.BACKEND_CORS_ORIGINS[0]}/subscription/cancel"
    
    try:
        # Create or retrieve Stripe customer
        if existing_subscription and existing_subscription.stripe_customer_id:
            customer_id = existing_subscription.stripe_customer_id
        else:
            customer = stripe.Customer.create(
                email=current_user.email,
                name=current_user.full_name,
                metadata={"user_id": current_user.id}
            )
            customer_id = customer.id
        
        # Create checkout session
        checkout_session = stripe.checkout.Session.create(
            customer=customer_id,
            payment_method_types=["card"],
            line_items=[
                {
                    "price": PLANS[plan_id]["id"],
                    "quantity": 1,
                }
            ],
            mode="subscription",
            success_url=success_url,
            cancel_url=cancel_url,
            metadata={
                "user_id": current_user.id,
                "plan_id": plan_id
            }
        )
        
        return {"checkout_url": checkout_session.url}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating checkout session: {str(e)}")

@router.post("/webhook")
async def stripe_webhook(request: Request, response: Response, db: Session = Depends(get_db)) -> Dict:
    """
    Handle Stripe webhook events
    """
    # Get the webhook secret
    webhook_secret = settings.STRIPE_WEBHOOK_SECRET
    
    # Get request body
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")
    
    try:
        # Verify webhook signature
        event = stripe.Webhook.construct_event(
            payload, sig_header, webhook_secret
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid payload: {str(e)}")
    except stripe.error.SignatureVerificationError as e:
        raise HTTPException(status_code=400, detail=f"Invalid signature: {str(e)}")
    
    # Handle specific webhook events
    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        
        # Get metadata
        user_id = int(session.get("metadata", {}).get("user_id"))
        plan_id = session.get("metadata", {}).get("plan_id")
        
        if not user_id or not plan_id:
            return {"status": "error", "message": "Missing metadata"}
        
        # Get subscription and customer info
        subscription_id = session.get("subscription")
        customer_id = session.get("customer")
        
        if not subscription_id:
            return {"status": "error", "message": "No subscription found"}
        
        # Get subscription details from Stripe
        subscription = stripe.Subscription.retrieve(subscription_id)
        
        # Update user subscription in database
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return {"status": "error", "message": "User not found"}
        
        # Check for existing subscription
        existing_subscription = (
            db.query(UserSubscription)
            .filter(UserSubscription.user_id == user_id)
            .first()
        )
        
        if existing_subscription:
            # Update existing subscription
            existing_subscription.stripe_customer_id = customer_id
            existing_subscription.stripe_subscription_id = subscription_id
            existing_subscription.plan_id = plan_id
            existing_subscription.status = subscription.status
            existing_subscription.current_period_start = datetime.fromtimestamp(subscription.current_period_start)
            existing_subscription.current_period_end = datetime.fromtimestamp(subscription.current_period_end)
        else:
            # Create new subscription
            new_subscription = UserSubscription(
                user_id=user_id,
                stripe_customer_id=customer_id,
                stripe_subscription_id=subscription_id,
                plan_id=plan_id,
                status=subscription.status,
                current_period_start=datetime.fromtimestamp(subscription.current_period_start),
                current_period_end=datetime.fromtimestamp(subscription.current_period_end)
            )
            db.add(new_subscription)
        
        # Update user's subscription tier
        user.subscription_tier = plan_id
        
        db.commit()
    
    elif event["type"] == "customer.subscription.updated":
        subscription = event["data"]["object"]
        subscription_id = subscription.id
        
        # Find the subscription in our database
        db_subscription = (
            db.query(UserSubscription)
            .filter(UserSubscription.stripe_subscription_id == subscription_id)
            .first()
        )
        
        if db_subscription:
            # Update subscription details
            db_subscription.status = subscription.status
            db_subscription.current_period_start = datetime.fromtimestamp(subscription.current_period_start)
            db_subscription.current_period_end = datetime.fromtimestamp(subscription.current_period_end)
            
            # If subscription canceled or unpaid, downgrade user to free tier
            if subscription.status in ["canceled", "unpaid", "past_due"]:
                user = db.query(User).filter(User.id == db_subscription.user_id).first()
                if user:
                    user.subscription_tier = "free"
            
            db.commit()
    
    return {"status": "success"}
