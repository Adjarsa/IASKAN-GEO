"""
Organization Models - Multi-tenant support
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
import uuid


class OrganizationMember(BaseModel):
    """Organization member with role"""
    user_id: str
    email: str
    name: str
    role: str = "member"  # owner, admin, member, viewer
    invited_by: Optional[str] = None
    joined_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class OrganizationSettings(BaseModel):
    """Organization settings"""
    default_language: str = "fr"
    default_country: str = "FR"
    default_ai_engines: List[str] = ["chatgpt"]
    notification_emails: List[str] = []
    branding: Dict[str, Any] = {}  # Custom branding options


class Organization(BaseModel):
    """Organization/Workspace model for multi-tenant support"""
    model_config = ConfigDict(extra="ignore")
    organization_id: str = Field(default_factory=lambda: f"org_{uuid.uuid4().hex[:12]}")
    name: str
    slug: str  # URL-friendly identifier
    owner_id: str  # User ID of the owner
    logo_url: Optional[str] = None
    website_url: Optional[str] = None
    industry: Optional[str] = None  # Sector/industry
    size: Optional[str] = None  # startup, small, medium, enterprise
    members: List[OrganizationMember] = []
    settings: OrganizationSettings = Field(default_factory=OrganizationSettings)
    subscription_id: Optional[str] = None  # Linked subscription
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: Optional[datetime] = None
    
    
class OrganizationInvite(BaseModel):
    """Invitation to join an organization"""
    model_config = ConfigDict(extra="ignore")
    invite_id: str = Field(default_factory=lambda: f"inv_{uuid.uuid4().hex[:12]}")
    organization_id: str
    email: str
    role: str = "member"
    invited_by: str  # User ID
    token: str = Field(default_factory=lambda: uuid.uuid4().hex)
    expires_at: datetime
    accepted: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
