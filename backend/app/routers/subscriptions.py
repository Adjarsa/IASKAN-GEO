"""
Subscriptions Router - PostgreSQL Version
Handles subscription and payment operations
"""
from fastapi import APIRouter, HTTPException, Request, Depends
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timezone, timedelta
import logging

from ..db.database import async_session_maker
from ..db.services import SubscriptionService, UserService
from ..db.models import SubscriptionStatus
from ..core.config import SUBSCRIPTION_PLANS, STRIPE_API_KEY, STRIPE_WEBHOOK_SECRET
from .auth import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["Subscription"])


# Request Models
class CheckoutRequest(BaseModel):
    plan: str
    success_url: Optional[str] = None
    cancel_url: Optional[str] = None


@router.get("/subscription/plans")
async def get_subscription_plans():
    """Get available subscription plans"""
    return {"plans": SUBSCRIPTION_PLANS}


@router.get("/subscription")
async def get_user_subscription(user: dict = Depends(get_current_user)):
    """Get current user's subscription"""
    async with async_session_maker() as db:
        subscription = await SubscriptionService.get_by_user_id(db, user["user_id"])
        
        if not subscription:
            # Create free subscription if none exists
            subscription = await SubscriptionService.create_free(db, user["user_id"])
        
        sub_dict = SubscriptionService.to_dict(subscription)
        
        # Add plan details
        plan = subscription.plan.value if subscription.plan else "free"
        plan_config = SUBSCRIPTION_PLANS.get(plan, SUBSCRIPTION_PLANS["free"])
        sub_dict["plan_details"] = plan_config
        
        return sub_dict


@router.post("/checkout/session")
async def create_checkout_session(request: Request, checkout: CheckoutRequest, user: dict = Depends(get_current_user)):
    """Create a Stripe checkout session"""
    if checkout.plan not in SUBSCRIPTION_PLANS or checkout.plan == "free":
        raise HTTPException(status_code=400, detail="Plan invalide")
    
    plan_config = SUBSCRIPTION_PLANS[checkout.plan]
    
    try:
        from ..services.stripe_abstraction import StripeCheckout, CheckoutSessionRequest
        
        stripe = StripeCheckout(api_key=STRIPE_API_KEY)
        
        # Get base URL
        referer = request.headers.get("referer", "")
        base_url = referer.rsplit("/", 1)[0] if referer else "https://iaskan.com"
        
        success_url = checkout.success_url or f"{base_url}/checkout/success?session_id={{CHECKOUT_SESSION_ID}}"
        cancel_url = checkout.cancel_url or f"{base_url}/pricing"
        
        session_request = CheckoutSessionRequest(
            success_url=success_url,
            cancel_url=cancel_url,
            line_items=[{
                "price_data": {
                    "currency": "eur",
                    "product_data": {
                        "name": f"IAskan {plan_config['name']}",
                        "description": f"Abonnement mensuel - {', '.join(plan_config['features'][:3])}"
                    },
                    "unit_amount": int(plan_config["price"] * 100),
                    "recurring": {"interval": "month"}
                },
                "quantity": 1
            }],
            mode="subscription",
            customer_email=user.get("email"),
            metadata={
                "user_id": user["user_id"],
                "plan": checkout.plan
            }
        )
        
        session = stripe.create_session(session_request)
        
        return {
            "session_id": session.session_id,
            "url": session.url
        }
        
    except Exception as e:
        logger.error(f"Checkout error: {e}")
        raise HTTPException(status_code=500, detail="Erreur lors de la création de la session de paiement")


@router.get("/checkout/status/{session_id}")
async def get_checkout_status(session_id: str, user: dict = Depends(get_current_user)):
    """Check checkout session status and update subscription if paid"""
    try:
        from ..services.stripe_abstraction import StripeCheckout
        
        stripe = StripeCheckout(api_key=STRIPE_API_KEY)
        status = stripe.get_session_status(session_id)
        
        if status.payment_status == "paid":
            # Update subscription
            async with async_session_maker() as db:
                # Get plan from session metadata (would need to store this during checkout)
                # For now, we'll use the session metadata from Stripe
                plan = status.metadata.get("plan", "starter") if hasattr(status, "metadata") else "starter"
                plan_config = SUBSCRIPTION_PLANS.get(plan, SUBSCRIPTION_PLANS["starter"])
                
                await SubscriptionService.update(
                    db,
                    user["user_id"],
                    plan=plan,
                    status=SubscriptionStatus.ACTIVE,
                    queries_limit=plan_config["queries_limit"],
                    scans_limit=plan_config["scans_limit"],
                    article_optimizer_limit=plan_config.get("article_optimizer_limit", 0),
                    current_period_start=datetime.now(timezone.utc),
                    current_period_end=datetime.now(timezone.utc) + timedelta(days=30)
                )
        
        return {
            "status": status.payment_status,
            "customer_email": status.customer_email
        }
        
    except Exception as e:
        logger.error(f"Status check error: {e}")
        raise HTTPException(status_code=500, detail="Erreur lors de la vérification du paiement")


@router.post("/subscription/cancel")
async def cancel_subscription(user: dict = Depends(get_current_user)):
    """Cancel subscription (will remain active until end of billing period)"""
    async with async_session_maker() as db:
        subscription = await SubscriptionService.get_by_user_id(db, user["user_id"])
        
        if not subscription:
            raise HTTPException(status_code=404, detail="Aucun abonnement trouvé")
        
        if subscription.plan.value == "free":
            raise HTTPException(status_code=400, detail="Impossible d'annuler un plan gratuit")
        
        # Mark as cancelled
        cancellation_date = subscription.current_period_end or (datetime.now(timezone.utc) + timedelta(days=30))
        
        await SubscriptionService.update(
            db,
            user["user_id"],
            status=SubscriptionStatus.CANCELLED,
            cancelled_at=datetime.now(timezone.utc),
            cancellation_effective_date=cancellation_date
        )
        
        return {
            "success": True,
            "message": "Votre abonnement sera annulé à la fin de la période en cours.",
            "effective_date": cancellation_date.isoformat()
        }


@router.post("/subscription/reactivate")
async def reactivate_subscription(user: dict = Depends(get_current_user)):
    """Reactivate a cancelled subscription"""
    async with async_session_maker() as db:
        subscription = await SubscriptionService.get_by_user_id(db, user["user_id"])
        
        if not subscription:
            raise HTTPException(status_code=404, detail="Aucun abonnement trouvé")
        
        if subscription.status.value != "cancelled":
            raise HTTPException(status_code=400, detail="L'abonnement n'est pas annulé")
        
        # Reactivate
        await SubscriptionService.update(
            db,
            user["user_id"],
            status=SubscriptionStatus.ACTIVE,
            cancelled_at=None,
            cancellation_effective_date=None
        )
        
        return {
            "success": True,
            "message": "Votre abonnement a été réactivé."
        }


@router.post("/webhook/stripe")
async def stripe_webhook(request: Request):
    """Handle Stripe webhooks"""
    try:
        payload = await request.body()
        sig_header = request.headers.get("stripe-signature", "")
        
        # Parse event - verify signature in production
        import json
        
        if STRIPE_WEBHOOK_SECRET and sig_header:
            try:
                from ..services.stripe_abstraction import StripeCheckout
                event = StripeCheckout.verify_webhook_signature(
                    payload, sig_header, STRIPE_WEBHOOK_SECRET
                )
            except ValueError as e:
                logger.error(f"Invalid webhook signature: {e}")
                raise HTTPException(status_code=400, detail="Invalid signature")
        else:
            event = json.loads(payload)
        
        event_type = event.get("type")
        data = event.get("data", {}).get("object", {})
        
        logger.info(f"Stripe webhook received: {event_type}")
        
        if event_type == "checkout.session.completed":
            user_id = data.get("metadata", {}).get("user_id")
            plan = data.get("metadata", {}).get("plan")
            
            if user_id and plan:
                async with async_session_maker() as db:
                    plan_config = SUBSCRIPTION_PLANS.get(plan, SUBSCRIPTION_PLANS["starter"])
                    
                    await SubscriptionService.update(
                        db,
                        user_id,
                        plan=plan,
                        status=SubscriptionStatus.ACTIVE,
                        stripe_customer_id=data.get("customer"),
                        stripe_subscription_id=data.get("subscription"),
                        queries_limit=plan_config["queries_limit"],
                        scans_limit=plan_config["scans_limit"],
                        article_optimizer_limit=plan_config.get("article_optimizer_limit", 0),
                        queries_used=0,
                        scans_used=0,
                        current_period_start=datetime.now(timezone.utc),
                        current_period_end=datetime.now(timezone.utc) + timedelta(days=30)
                    )
                    
                    logger.info(f"Subscription updated for user {user_id} to plan {plan}")
        
        elif event_type == "customer.subscription.updated":
            stripe_subscription_id = data.get("id")
            status = data.get("status")
            cancel_at_period_end = data.get("cancel_at_period_end", False)
            
            logger.info(f"Subscription {stripe_subscription_id} updated: status={status}, cancel_at_period_end={cancel_at_period_end}")
            # Could update local subscription status based on Stripe status
        
        elif event_type == "customer.subscription.deleted":
            stripe_subscription_id = data.get("id")
            logger.info(f"Subscription {stripe_subscription_id} deleted")
            # Could find and downgrade user to free plan
        
        elif event_type == "invoice.payment_succeeded":
            # Recurring payment succeeded - could extend period
            customer_id = data.get("customer")
            subscription_id = data.get("subscription")
            logger.info(f"Payment succeeded for customer {customer_id}")
        
        elif event_type == "invoice.payment_failed":
            # Payment failed - could notify user
            customer_id = data.get("customer")
            logger.warning(f"Payment failed for customer {customer_id}")
        
        return {"received": True}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        return {"received": True, "error": str(e)}
