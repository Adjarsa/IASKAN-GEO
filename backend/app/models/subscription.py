"""
Subscription Models
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime, timezone
import uuid


class Subscription(BaseModel):
    """Subscription model"""
    model_config = ConfigDict(extra="ignore")
    subscription_id: str = Field(default_factory=lambda: f"sub_{uuid.uuid4().hex[:12]}")
    user_id: str
    organization_id: Optional[str] = None  # For organization billing
    plan: str = "free"  # free, starter, pro, business
    status: str = "active"  # active, cancelled, expired, trial, past_due
    
    # Limits
    queries_limit: int = 90
    queries_used: int = 0
    scans_limit: int = 1
    scans_used: int = 0
    free_scans_remaining: int = 1
    
    # Article optimizer limits
    article_optimizer_used: int = 0
    
    # Stripe integration
    stripe_customer_id: Optional[str] = None
    stripe_subscription_id: Optional[str] = None
    
    # Period
    trial_ends_at: Optional[datetime] = None
    current_period_start: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    current_period_end: Optional[datetime] = None
    
    # Metadata
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: Optional[datetime] = None


class PaymentTransaction(BaseModel):
    """Payment transaction record"""
    model_config = ConfigDict(extra="ignore")
    transaction_id: str = Field(default_factory=lambda: f"txn_{uuid.uuid4().hex[:12]}")
    user_id: str
    organization_id: Optional[str] = None
    session_id: str
    amount: float
    currency: str = "eur"
    plan: str
    status: str = "pending"  # pending, paid, failed, expired, refunded
    payment_status: str = "initiated"
    stripe_payment_intent_id: Optional[str] = None
    metadata: dict = {}
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
