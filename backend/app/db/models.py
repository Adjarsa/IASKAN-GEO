"""
SQLAlchemy Models for IAskan
PostgreSQL with Supabase
"""
from sqlalchemy import (
    Column, String, Integer, Float, Boolean, DateTime, Text, JSON, 
    ForeignKey, Index, Enum as SQLEnum
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime, timezone
import uuid
import enum

from .database import Base


def generate_uuid(prefix: str = "") -> str:
    """Generate a prefixed UUID"""
    return f"{prefix}{uuid.uuid4().hex[:12]}"


class SubscriptionPlan(str, enum.Enum):
    FREE = "free"
    STARTER = "starter"
    PRO = "pro"
    BUSINESS = "business"


class SubscriptionStatus(str, enum.Enum):
    ACTIVE = "active"
    CANCELLED = "cancelled"
    EXPIRED = "expired"
    PAST_DUE = "past_due"


class AnalysisStatus(str, enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class OrganizationRole(str, enum.Enum):
    OWNER = "owner"
    ADMIN = "admin"
    MEMBER = "member"
    VIEWER = "viewer"


# ================== USER MODELS ==================

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(50), unique=True, nullable=False, default=lambda: generate_uuid("user_"))
    email = Column(String(255), unique=True, nullable=False, index=True)
    name = Column(String(255))
    picture = Column(Text)
    company = Column(String(255))
    auth_provider = Column(String(50))  # google, microsoft, linkedin, magic_link
    password_hash = Column(String(255))
    email_verified = Column(Boolean, default=False)
    email_verified_at = Column(DateTime(timezone=True))
    registration_ip = Column(String(50))
    registration_fingerprint = Column(String(255))
    onboarding_completed = Column(Boolean, default=False)
    onboarding_steps = Column(JSON, default=dict)
    preferences = Column(JSON, default=dict)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    subscription = relationship("Subscription", back_populates="user", uselist=False)
    projects = relationship("Project", back_populates="user")
    sessions = relationship("UserSession", back_populates="user")
    notifications = relationship("Notification", back_populates="user")
    
    __table_args__ = (
        Index('ix_users_user_id', 'user_id'),
    )


class UserSession(Base):
    __tablename__ = "user_sessions"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(100), unique=True, nullable=False)
    user_id = Column(String(50), ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)
    session_token = Column(String(255), unique=True, nullable=False, index=True)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="sessions")


class EmailVerificationToken(Base):
    __tablename__ = "email_verification_tokens"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    token_id = Column(String(50), unique=True, nullable=False)
    user_id = Column(String(50), ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)
    email = Column(String(255), nullable=False)
    token = Column(String(255), unique=True, nullable=False, index=True)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    used = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class PasswordReset(Base):
    __tablename__ = "password_resets"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    token = Column(String(255), unique=True, nullable=False, index=True)
    user_id = Column(String(50), ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)
    email = Column(String(255), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    used = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class MagicLink(Base):
    __tablename__ = "magic_links"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    token = Column(String(255), unique=True, nullable=False, index=True)
    user_id = Column(String(50), ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)
    email = Column(String(255), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    used = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


# ================== SUBSCRIPTION MODELS ==================

class Subscription(Base):
    __tablename__ = "subscriptions"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    subscription_id = Column(String(50), unique=True, nullable=False, default=lambda: generate_uuid("sub_"))
    user_id = Column(String(50), ForeignKey("users.user_id", ondelete="CASCADE"), unique=True, nullable=False)
    plan = Column(SQLEnum(SubscriptionPlan), default=SubscriptionPlan.FREE)
    status = Column(SQLEnum(SubscriptionStatus), default=SubscriptionStatus.ACTIVE)
    stripe_customer_id = Column(String(255))
    stripe_subscription_id = Column(String(255))
    queries_limit = Column(Integer, default=90)
    queries_used = Column(Integer, default=0)
    scans_limit = Column(Integer, default=1)
    scans_used = Column(Integer, default=0)
    free_scans_remaining = Column(Integer, default=1)
    article_optimizer_limit = Column(Integer, default=0)
    article_optimizer_used = Column(Integer, default=0)
    current_period_start = Column(DateTime(timezone=True))
    current_period_end = Column(DateTime(timezone=True))
    cancelled_at = Column(DateTime(timezone=True))
    cancellation_effective_date = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="subscription")


class PaymentTransaction(Base):
    __tablename__ = "payment_transactions"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    transaction_id = Column(String(50), unique=True, nullable=False)
    user_id = Column(String(50), ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)
    session_id = Column(String(255))
    amount = Column(Float, nullable=False)
    currency = Column(String(10), default="eur")
    plan = Column(String(50))
    status = Column(String(50), default="pending")
    paid_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())


# ================== PROJECT MODELS ==================

class Project(Base):
    __tablename__ = "projects"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(String(50), unique=True, nullable=False, default=lambda: generate_uuid("proj_"))
    user_id = Column(String(50), ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False, index=True)
    organization_id = Column(String(50), ForeignKey("organizations.organization_id", ondelete="SET NULL"))
    name = Column(String(255), nullable=False)
    website_url = Column(Text)
    brand_name = Column(String(255))
    logo_url = Column(Text)
    competitors = Column(JSON, default=list)
    keywords = Column(JSON, default=list)
    industry = Column(String(100))
    description = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="projects")
    analyses = relationship("Analysis", back_populates="project")
    schedules = relationship("ScanSchedule", back_populates="project")
    organization = relationship("Organization", back_populates="projects")


# ================== ANALYSIS MODELS ==================

class Analysis(Base):
    __tablename__ = "analyses"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    analysis_id = Column(String(50), unique=True, nullable=False, default=lambda: generate_uuid("ana_"))
    project_id = Column(String(50), ForeignKey("projects.project_id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(String(50), ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False, index=True)
    status = Column(SQLEnum(AnalysisStatus), default=AnalysisStatus.PENDING)
    global_score = Column(Float)
    grade = Column(String(10))  # A, B, C, D, F, or N/A
    ai_scores = Column(JSON, default=dict)  # {chatgpt: 85, claude: 78, ...}
    rate_scores = Column(JSON, default=dict)  # {relevance: 80, authority: 75, ...}
    query_scores = Column(JSON, default=list)
    competitor_analysis = Column(JSON, default=dict)
    recommendations = Column(JSON, default=list)
    stability_score = Column(Float)
    total_queries = Column(Integer, default=0)
    queries_with_mention = Column(Integer, default=0)
    mention_rate = Column(Float)
    average_position = Column(Float)
    ai_engines_used = Column(JSON, default=list)
    error_message = Column(Text)
    started_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    project = relationship("Project", back_populates="analyses")


# ================== SCHEDULE MODELS ==================

class ScanSchedule(Base):
    __tablename__ = "scan_schedules"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    schedule_id = Column(String(50), unique=True, nullable=False, default=lambda: generate_uuid("sched_"))
    user_id = Column(String(50), ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)
    project_id = Column(String(50), ForeignKey("projects.project_id", ondelete="CASCADE"), nullable=False)
    frequency = Column(String(20), default="weekly")  # daily, weekly, biweekly, monthly
    time = Column(String(10), default="09:00")  # HH:MM format
    day_of_week = Column(Integer)  # 0-6 for weekly
    day_of_month = Column(Integer)  # 1-31 for monthly
    hour = Column(Integer, default=9)
    minute = Column(Integer, default=0)
    email_report = Column(Boolean, default=True)
    send_report_email = Column(Boolean, default=True)
    report_recipients = Column(JSON, default=list)
    enabled = Column(Boolean, default=True)
    last_run = Column(DateTime(timezone=True))
    next_run = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    project = relationship("Project", back_populates="schedules")


# ================== NOTIFICATION MODELS ==================

class Notification(Base):
    __tablename__ = "notifications"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    notification_id = Column(String(50), unique=True, nullable=False, default=lambda: generate_uuid("notif_"))
    user_id = Column(String(50), ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False, index=True)
    type = Column(String(50), nullable=False)
    title = Column(String(255), nullable=False)
    message = Column(Text)
    data = Column(JSON, default=dict)
    read = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="notifications")


# ================== ORGANIZATION MODELS ==================

class Organization(Base):
    __tablename__ = "organizations"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    organization_id = Column(String(50), unique=True, nullable=False, default=lambda: generate_uuid("org_"))
    name = Column(String(255), nullable=False)
    slug = Column(String(100), unique=True)
    description = Column(Text)
    logo_url = Column(Text)
    website_url = Column(Text)
    owner_id = Column(String(50), ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)
    settings = Column(JSON, default=dict)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    members = relationship("OrganizationMember", back_populates="organization")
    projects = relationship("Project", back_populates="organization")


class OrganizationMember(Base):
    __tablename__ = "organization_members"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    organization_id = Column(String(50), ForeignKey("organizations.organization_id", ondelete="CASCADE"), nullable=False)
    user_id = Column(String(50), ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)
    role = Column(SQLEnum(OrganizationRole), default=OrganizationRole.MEMBER)
    joined_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    organization = relationship("Organization", back_populates="members")
    
    __table_args__ = (
        Index('ix_org_member_unique', 'organization_id', 'user_id', unique=True),
    )


class OrganizationInvite(Base):
    __tablename__ = "organization_invites"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    invite_id = Column(String(50), unique=True, nullable=False, default=lambda: generate_uuid("inv_"))
    organization_id = Column(String(50), ForeignKey("organizations.organization_id", ondelete="CASCADE"), nullable=False)
    email = Column(String(255), nullable=False)
    role = Column(SQLEnum(OrganizationRole), default=OrganizationRole.MEMBER)
    token = Column(String(255), unique=True, nullable=False)
    invited_by = Column(String(50), ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    accepted = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


# ================== ARTICLE OPTIMIZER MODELS ==================

class ArticleOptimization(Base):
    __tablename__ = "article_optimizations"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    optimization_id = Column(String(50), unique=True, nullable=False, default=lambda: generate_uuid("opt_"))
    user_id = Column(String(50), ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False, index=True)
    url = Column(Text)
    content = Column(Text)
    title = Column(String(500))
    scores = Column(JSON, default=dict)  # {structure: 80, authority: 75, ...}
    diagnostics = Column(JSON, default=list)
    action_plan = Column(JSON, default=dict)
    distribution_strategy = Column(JSON, default=dict)
    llm_analysis = Column(JSON, default=dict)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


# ================== CONTACT & MISC MODELS ==================

class ContactMessage(Base):
    __tablename__ = "contact_messages"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    contact_id = Column(String(50), unique=True, nullable=False, default=lambda: generate_uuid("contact_"))
    name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False)
    company = Column(String(255))
    subject = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    status = Column(String(50), default="new")
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class AdminLog(Base):
    __tablename__ = "admin_logs"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    log_id = Column(String(50), unique=True, nullable=False, default=lambda: generate_uuid("log_"))
    admin_id = Column(String(50), nullable=False)
    action = Column(String(100), nullable=False)
    target_type = Column(String(50))
    target_id = Column(String(50))
    details = Column(JSON, default=dict)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
