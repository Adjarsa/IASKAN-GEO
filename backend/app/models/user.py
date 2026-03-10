"""
User Models
"""
from pydantic import BaseModel, Field, ConfigDict, EmailStr
from typing import Optional, List
from datetime import datetime, timezone
import uuid


class User(BaseModel):
    """User model"""
    model_config = ConfigDict(extra="ignore")
    user_id: str = Field(default_factory=lambda: f"user_{uuid.uuid4().hex[:12]}")
    email: EmailStr
    name: str
    picture: Optional[str] = None
    company: Optional[str] = None
    role: str = "user"  # user, admin, super_admin
    organization_id: Optional[str] = None  # Primary organization
    email_verified: bool = False
    email_verified_at: Optional[datetime] = None
    auth_provider: str = "google"  # google, microsoft, linkedin, magic_link
    registration_ip: Optional[str] = None
    registration_fingerprint: Optional[str] = None
    last_login: Optional[datetime] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: Optional[datetime] = None


class UserSession(BaseModel):
    """User session model"""
    model_config = ConfigDict(extra="ignore")
    session_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    session_token: str
    expires_at: datetime
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class EmailVerificationToken(BaseModel):
    """Token for email verification"""
    model_config = ConfigDict(extra="ignore")
    token_id: str = Field(default_factory=lambda: f"evt_{uuid.uuid4().hex[:12]}")
    user_id: str
    email: str
    token: str = Field(default_factory=lambda: uuid.uuid4().hex)
    expires_at: datetime
    used: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
