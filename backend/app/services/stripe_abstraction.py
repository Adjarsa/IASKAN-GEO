"""
Stripe Abstraction Layer for Railway Deployment
Uses emergentintegrations when available, falls back to native Stripe SDK
"""
import os
import logging
from typing import Optional
from pydantic import BaseModel

logger = logging.getLogger(__name__)

# Try to import emergentintegrations, fall back to native SDK
try:
    from emergentintegrations.payments.stripe.checkout import (
        StripeCheckout, 
        CheckoutSessionResponse, 
        CheckoutStatusResponse, 
        CheckoutSessionRequest
    )
    USING_EMERGENT_STRIPE = True
    logger.info("Using emergentintegrations for Stripe")
except ImportError:
    USING_EMERGENT_STRIPE = False
    logger.info("emergentintegrations not available, using native Stripe SDK")
    
    import stripe
    
    class CheckoutSessionRequest(BaseModel):
        """Compatible CheckoutSessionRequest"""
        price_id: str
        success_url: str
        cancel_url: str
        customer_email: Optional[str] = None
        metadata: Optional[dict] = None
    
    class CheckoutSessionResponse(BaseModel):
        """Compatible CheckoutSessionResponse"""
        session_id: str
        url: str
    
    class CheckoutStatusResponse(BaseModel):
        """Compatible CheckoutStatusResponse"""
        status: str
        payment_status: str
        customer_email: Optional[str] = None
    
    class StripeCheckout:
        """Compatible StripeCheckout class using native Stripe SDK"""
        def __init__(self, api_key: str):
            self.api_key = api_key
            stripe.api_key = api_key
        
        def create_checkout_session(self, request: CheckoutSessionRequest) -> CheckoutSessionResponse:
            """Create a Stripe checkout session"""
            session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=[{
                    'price': request.price_id,
                    'quantity': 1,
                }],
                mode='subscription',
                success_url=request.success_url,
                cancel_url=request.cancel_url,
                customer_email=request.customer_email,
                metadata=request.metadata or {}
            )
            
            return CheckoutSessionResponse(
                session_id=session.id,
                url=session.url
            )
        
        def get_session_status(self, session_id: str) -> CheckoutStatusResponse:
            """Get status of a checkout session"""
            session = stripe.checkout.Session.retrieve(session_id)
            
            return CheckoutStatusResponse(
                status=session.status,
                payment_status=session.payment_status,
                customer_email=session.customer_details.email if session.customer_details else None
            )


def get_stripe_checkout(api_key: str) -> StripeCheckout:
    """Factory function to get Stripe checkout instance"""
    return StripeCheckout(api_key=api_key)
