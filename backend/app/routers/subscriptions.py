"""
Subscription Router
Handles subscription and payment endpoints
"""
from fastapi import APIRouter, HTTPException, Request, Depends
from typing import Optional
from datetime import datetime, timezone, timedelta
from pydantic import BaseModel
import logging

from ..core.database import db
from ..core.config import SUBSCRIPTION_PLANS, STRIPE_API_KEY, FRONTEND_URL
from ..services.email_service import email_service
from .auth import get_current_user
from .notifications import create_notification

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
async def get_subscription(user: dict = Depends(get_current_user)):
    """Get user's current subscription"""
    subscription = await db.subscriptions.find_one({"user_id": user["user_id"]}, {"_id": 0})
    if not subscription:
        return {"subscription": None}
    return {"subscription": subscription}


@router.post("/checkout/create")
async def create_checkout(data: CheckoutRequest, user: dict = Depends(get_current_user)):
    """Create Stripe checkout session"""
    if data.plan not in SUBSCRIPTION_PLANS:
        raise HTTPException(status_code=400, detail="Plan invalide")
    
    plan_config = SUBSCRIPTION_PLANS[data.plan]
    
    if plan_config["price"] == 0:
        raise HTTPException(status_code=400, detail="Ce plan est gratuit")
    
    try:
        from emergentintegrations.payments.stripe.checkout import StripeCheckout, CheckoutSessionRequest
        
        checkout = StripeCheckout(api_key=STRIPE_API_KEY)
        
        success_url = data.success_url or f"{FRONTEND_URL}/settings?payment=success"
        cancel_url = data.cancel_url or f"{FRONTEND_URL}/pricing?payment=cancelled"
        
        session = await checkout.create_session(CheckoutSessionRequest(
            product_name=f"IAskan {plan_config['name']}",
            unit_amount=int(plan_config["price"] * 100),
            currency="eur",
            success_url=success_url,
            cancel_url=cancel_url,
            customer_email=user.get("email"),
            metadata={
                "user_id": user["user_id"],
                "plan": data.plan
            }
        ))
        
        # Store pending transaction
        await db.payment_transactions.insert_one({
            "transaction_id": f"txn_{session.id[:12]}",
            "user_id": user["user_id"],
            "session_id": session.id,
            "amount": plan_config["price"],
            "currency": "eur",
            "plan": data.plan,
            "status": "pending",
            "created_at": datetime.now(timezone.utc).isoformat()
        })
        
        return {
            "session_id": session.id,
            "url": session.url
        }
        
    except Exception as e:
        logger.error(f"Checkout creation error: {e}")
        raise HTTPException(status_code=500, detail="Erreur lors de la création du paiement")


@router.get("/checkout/status/{session_id}")
async def get_checkout_status(session_id: str, user: dict = Depends(get_current_user)):
    """Get checkout session status"""
    try:
        from emergentintegrations.payments.stripe.checkout import StripeCheckout
        
        checkout = StripeCheckout(api_key=STRIPE_API_KEY)
        status = await checkout.get_session_status(session_id)
        
        # If payment is complete, update subscription
        if status.status == "complete" and status.payment_status == "paid":
            transaction = await db.payment_transactions.find_one({"session_id": session_id})
            
            if transaction and transaction.get("status") != "paid":
                plan = transaction.get("plan", "starter")
                plan_config = SUBSCRIPTION_PLANS.get(plan, SUBSCRIPTION_PLANS["starter"])
                
                # Update subscription
                await db.subscriptions.update_one(
                    {"user_id": user["user_id"]},
                    {"$set": {
                        "plan": plan,
                        "status": "active",
                        "queries_limit": plan_config["queries_limit"],
                        "scans_limit": plan_config["scans_limit"],
                        "queries_used": 0,
                        "scans_used": 0,
                        "article_optimizer_used": 0,
                        "current_period_start": datetime.now(timezone.utc).isoformat(),
                        "current_period_end": (datetime.now(timezone.utc) + timedelta(days=30)).isoformat(),
                        "updated_at": datetime.now(timezone.utc).isoformat()
                    }}
                )
                
                # Update transaction
                await db.payment_transactions.update_one(
                    {"session_id": session_id},
                    {"$set": {"status": "paid", "paid_at": datetime.now(timezone.utc).isoformat()}}
                )
                
                # Create notification
                await create_notification(
                    user_id=user["user_id"],
                    notification_type="subscription_activated",
                    title="Abonnement activé",
                    message=f"Votre abonnement {plan_config['name']} est maintenant actif.",
                    data={"plan": plan}
                )
        
        return {
            "status": status.status,
            "payment_status": status.payment_status
        }
        
    except Exception as e:
        logger.error(f"Checkout status error: {e}")
        raise HTTPException(status_code=500, detail="Erreur lors de la vérification du paiement")


@router.post("/subscription/cancel")
async def cancel_subscription(user: dict = Depends(get_current_user)):
    """Cancel user subscription"""
    subscription = await db.subscriptions.find_one({"user_id": user["user_id"]}, {"_id": 0})
    
    if not subscription:
        raise HTTPException(status_code=404, detail="Aucun abonnement trouvé")
    
    if subscription.get("plan") == "free":
        raise HTTPException(status_code=400, detail="Vous êtes déjà sur le plan gratuit")
    
    # Calculate end date
    current_period_end = subscription.get("current_period_end")
    if current_period_end:
        end_date = datetime.fromisoformat(current_period_end.replace('Z', '+00:00'))
    else:
        end_date = datetime.now(timezone.utc) + timedelta(days=30)
    
    # Mark as cancelled
    await db.subscriptions.update_one(
        {"user_id": user["user_id"]},
        {"$set": {
            "status": "cancelled",
            "cancelled_at": datetime.now(timezone.utc).isoformat(),
            "cancellation_effective_date": end_date.isoformat()
        }}
    )
    
    # Send email
    plan_name = SUBSCRIPTION_PLANS.get(subscription.get("plan", "free"), {}).get("name", "Abonnement")
    end_date_str = end_date.strftime("%d/%m/%Y")
    
    await email_service.send_subscription_cancelled_email(
        email=user.get("email", ""),
        user_name=user.get("name", ""),
        plan_name=plan_name,
        end_date=end_date_str
    )
    
    # Create notification
    await create_notification(
        user_id=user["user_id"],
        notification_type="subscription_cancelled",
        title="Abonnement annulé",
        message=f"Votre abonnement {plan_name} sera actif jusqu'au {end_date_str}",
        data={"end_date": end_date.isoformat(), "plan": subscription.get("plan")}
    )
    
    return {
        "success": True,
        "message": f"Votre abonnement sera actif jusqu'au {end_date_str}",
        "end_date": end_date.isoformat()
    }


@router.post("/subscription/reactivate")
async def reactivate_subscription(user: dict = Depends(get_current_user)):
    """Reactivate a cancelled subscription"""
    subscription = await db.subscriptions.find_one({"user_id": user["user_id"]}, {"_id": 0})
    
    if not subscription:
        raise HTTPException(status_code=404, detail="Aucun abonnement trouvé")
    
    if subscription.get("status") != "cancelled":
        raise HTTPException(status_code=400, detail="L'abonnement n'est pas annulé")
    
    # Reactivate
    await db.subscriptions.update_one(
        {"user_id": user["user_id"]},
        {"$set": {
            "status": "active",
            "cancelled_at": None,
            "cancellation_effective_date": None
        }}
    )
    
    plan_name = SUBSCRIPTION_PLANS.get(subscription.get("plan", "free"), {}).get("name", "Abonnement")
    
    # Create notification
    await create_notification(
        user_id=user["user_id"],
        notification_type="subscription_reactivated",
        title="Abonnement réactivé",
        message=f"Votre abonnement {plan_name} a été réactivé.",
        data={"plan": subscription.get("plan")}
    )
    
    return {
        "success": True,
        "message": f"Votre abonnement {plan_name} a été réactivé"
    }


@router.post("/webhook/stripe")
async def stripe_webhook(request: Request):
    """Handle Stripe webhooks"""
    try:
        payload = await request.body()
        # Process webhook...
        return {"received": True}
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        return {"received": True, "error": str(e)}
