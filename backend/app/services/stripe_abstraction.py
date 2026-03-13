"""
Stripe Abstraction Layer for IAskan
Handles checkout sessions, subscriptions, and webhooks
"""
import os
import logging
from typing import Optional, List, Dict, Any
from pydantic import BaseModel
from datetime import datetime

logger = logging.getLogger(__name__)

# Try to import emergentintegrations, fall back to native SDK
try:
    from emergentintegrations.payments.stripe.checkout import (
        StripeCheckout as EmergentStripeCheckout,
        CheckoutSessionResponse as EmergentCheckoutResponse,
        CheckoutStatusResponse as EmergentStatusResponse,
        CheckoutSessionRequest as EmergentCheckoutRequest
    )
    USING_EMERGENT_STRIPE = True
    logger.info("Using emergentintegrations for Stripe")
except ImportError:
    USING_EMERGENT_STRIPE = False
    logger.info("emergentintegrations not available, using native Stripe SDK")


# ================== MODELS ==================

class CheckoutSessionRequest(BaseModel):
    """Checkout session request model"""
    success_url: str
    cancel_url: str
    line_items: Optional[List[Dict[str, Any]]] = None
    price_id: Optional[str] = None
    mode: str = "subscription"  # subscription, payment
    customer_email: Optional[str] = None
    metadata: Optional[Dict[str, str]] = None
    allow_promotion_codes: bool = True


class CheckoutSessionResponse(BaseModel):
    """Checkout session response model"""
    session_id: str
    url: str


class CheckoutStatusResponse(BaseModel):
    """Checkout status response model"""
    status: str
    payment_status: str
    customer_email: Optional[str] = None
    metadata: Optional[Dict[str, str]] = None
    customer_id: Optional[str] = None
    subscription_id: Optional[str] = None


class SubscriptionInfo(BaseModel):
    """Subscription information model"""
    subscription_id: str
    status: str
    current_period_start: Optional[datetime] = None
    current_period_end: Optional[datetime] = None
    cancel_at_period_end: bool = False
    plan_id: Optional[str] = None
    customer_id: Optional[str] = None


class CustomerInfo(BaseModel):
    """Customer information model"""
    customer_id: str
    email: Optional[str] = None
    name: Optional[str] = None
    created: Optional[datetime] = None


# ================== STRIPE CHECKOUT CLASS ==================

class StripeCheckout:
    """
    Stripe checkout handler with support for both 
    emergentintegrations and native Stripe SDK
    """
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self._stripe = None
        
        if not USING_EMERGENT_STRIPE:
            import stripe
            stripe.api_key = api_key
            self._stripe = stripe
    
    def create_session(self, request: CheckoutSessionRequest) -> CheckoutSessionResponse:
        """Create a checkout session"""
        if USING_EMERGENT_STRIPE:
            return self._create_session_emergent(request)
        else:
            return self._create_session_native(request)
    
    def _create_session_emergent(self, request: CheckoutSessionRequest) -> CheckoutSessionResponse:
        """Create session using emergentintegrations"""
        emergent_request = EmergentCheckoutRequest(
            price_id=request.price_id or "",
            success_url=request.success_url,
            cancel_url=request.cancel_url,
            customer_email=request.customer_email,
            metadata=request.metadata
        )
        checkout = EmergentStripeCheckout(api_key=self.api_key)
        response = checkout.create_checkout_session(emergent_request)
        return CheckoutSessionResponse(
            session_id=response.session_id,
            url=response.url
        )
    
    def _create_session_native(self, request: CheckoutSessionRequest) -> CheckoutSessionResponse:
        """Create session using native Stripe SDK"""
        params = {
            'success_url': request.success_url,
            'cancel_url': request.cancel_url,
            'mode': request.mode,
            'allow_promotion_codes': request.allow_promotion_codes,
        }
        
        # Add line items
        if request.line_items:
            params['line_items'] = request.line_items
        elif request.price_id:
            params['line_items'] = [{
                'price': request.price_id,
                'quantity': 1,
            }]
        
        # Add customer email
        if request.customer_email:
            params['customer_email'] = request.customer_email
        
        # Add metadata
        if request.metadata:
            params['metadata'] = request.metadata
        
        try:
            session = self._stripe.checkout.Session.create(**params)
            
            return CheckoutSessionResponse(
                session_id=session.id,
                url=session.url
            )
        except Exception as e:
            logger.error(f"Stripe session creation error: {e}")
            raise
    
    def get_session_status(self, session_id: str) -> CheckoutStatusResponse:
        """Get checkout session status"""
        if USING_EMERGENT_STRIPE:
            checkout = EmergentStripeCheckout(api_key=self.api_key)
            response = checkout.get_session_status(session_id)
            return CheckoutStatusResponse(
                status=response.status,
                payment_status=response.payment_status,
                customer_email=response.customer_email
            )
        else:
            session = self._stripe.checkout.Session.retrieve(
                session_id,
                expand=['subscription', 'customer']
            )
            
            return CheckoutStatusResponse(
                status=session.status,
                payment_status=session.payment_status,
                customer_email=session.customer_details.email if session.customer_details else None,
                metadata=dict(session.metadata) if session.metadata else None,
                customer_id=session.customer if isinstance(session.customer, str) else (session.customer.id if session.customer else None),
                subscription_id=session.subscription if isinstance(session.subscription, str) else (session.subscription.id if session.subscription else None)
            )
    
    def get_subscription(self, subscription_id: str) -> Optional[SubscriptionInfo]:
        """Get subscription details"""
        if USING_EMERGENT_STRIPE:
            return None  # Not supported in emergentintegrations
        
        try:
            subscription = self._stripe.Subscription.retrieve(subscription_id)
            return SubscriptionInfo(
                subscription_id=subscription.id,
                status=subscription.status,
                current_period_start=datetime.fromtimestamp(subscription.current_period_start) if subscription.current_period_start else None,
                current_period_end=datetime.fromtimestamp(subscription.current_period_end) if subscription.current_period_end else None,
                cancel_at_period_end=subscription.cancel_at_period_end,
                plan_id=subscription.items.data[0].price.id if subscription.items.data else None,
                customer_id=subscription.customer if isinstance(subscription.customer, str) else subscription.customer.id
            )
        except Exception as e:
            logger.error(f"Error retrieving subscription: {e}")
            return None
    
    def cancel_subscription(self, subscription_id: str, at_period_end: bool = True) -> bool:
        """Cancel a subscription"""
        if USING_EMERGENT_STRIPE:
            return False  # Not supported
        
        try:
            if at_period_end:
                self._stripe.Subscription.modify(
                    subscription_id,
                    cancel_at_period_end=True
                )
            else:
                self._stripe.Subscription.cancel(subscription_id)
            return True
        except Exception as e:
            logger.error(f"Error cancelling subscription: {e}")
            return False
    
    def reactivate_subscription(self, subscription_id: str) -> bool:
        """Reactivate a cancelled subscription"""
        if USING_EMERGENT_STRIPE:
            return False
        
        try:
            self._stripe.Subscription.modify(
                subscription_id,
                cancel_at_period_end=False
            )
            return True
        except Exception as e:
            logger.error(f"Error reactivating subscription: {e}")
            return False
    
    def get_or_create_customer(self, email: str, name: Optional[str] = None, metadata: Optional[Dict] = None) -> CustomerInfo:
        """Get existing customer or create new one"""
        if USING_EMERGENT_STRIPE:
            raise NotImplementedError("Customer management not supported in emergentintegrations")
        
        # Search for existing customer
        customers = self._stripe.Customer.search(query=f"email:'{email}'")
        
        if customers.data:
            customer = customers.data[0]
        else:
            # Create new customer
            customer = self._stripe.Customer.create(
                email=email,
                name=name,
                metadata=metadata or {}
            )
        
        return CustomerInfo(
            customer_id=customer.id,
            email=customer.email,
            name=customer.name,
            created=datetime.fromtimestamp(customer.created) if customer.created else None
        )
    
    def create_billing_portal_session(self, customer_id: str, return_url: str) -> str:
        """Create a billing portal session for customer to manage subscription"""
        if USING_EMERGENT_STRIPE:
            raise NotImplementedError("Billing portal not supported in emergentintegrations")
        
        session = self._stripe.billing_portal.Session.create(
            customer=customer_id,
            return_url=return_url
        )
        return session.url
    
    @staticmethod
    def verify_webhook_signature(payload: bytes, signature: str, webhook_secret: str) -> Dict[str, Any]:
        """Verify webhook signature and return event"""
        import stripe
        try:
            event = stripe.Webhook.construct_event(
                payload, signature, webhook_secret
            )
            return dict(event)
        except stripe.error.SignatureVerificationError:
            raise ValueError("Invalid webhook signature")


def get_stripe_checkout(api_key: str) -> StripeCheckout:
    """Factory function to get Stripe checkout instance"""
    return StripeCheckout(api_key=api_key)
