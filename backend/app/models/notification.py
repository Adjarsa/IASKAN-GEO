"""
Notification Models
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Dict, Any
from datetime import datetime, timezone
import uuid


class Notification(BaseModel):
    """User notifications"""
    model_config = ConfigDict(extra="ignore")
    notification_id: str = Field(default_factory=lambda: f"notif_{uuid.uuid4().hex[:12]}")
    user_id: str
    organization_id: Optional[str] = None
    type: str  # scan_complete, scan_failed, subscription_expiring, article_optimized, etc.
    title: str
    message: str
    data: Dict[str, Any] = {}
    read: bool = False
    email_sent: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
