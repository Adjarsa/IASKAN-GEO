"""
PostgreSQL Database Services for IAskan
Replaces MongoDB operations with SQLAlchemy ORM
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, func, and_, or_
from sqlalchemy.orm import selectinload
from datetime import datetime, timezone, timedelta
from typing import Optional, List, Dict, Any
import uuid

from .models import (
    User, UserSession, EmailVerificationToken, PasswordReset, MagicLink,
    Subscription, PaymentTransaction,
    Project, Analysis, ScanSchedule,
    Notification, Organization, OrganizationMember, OrganizationInvite,
    ArticleOptimization, ContactMessage, AdminLog,
    SubscriptionPlan, SubscriptionStatus, AnalysisStatus, OrganizationRole
)


def generate_id(prefix: str = "") -> str:
    """Generate a prefixed UUID"""
    return f"{prefix}{uuid.uuid4().hex[:12]}"


# ================== USER SERVICES ==================

class UserService:
    """User-related database operations"""
    
    @staticmethod
    async def get_by_email(db: AsyncSession, email: str) -> Optional[User]:
        """Get user by email"""
        result = await db.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_by_user_id(db: AsyncSession, user_id: str) -> Optional[User]:
        """Get user by user_id"""
        result = await db.execute(select(User).where(User.user_id == user_id))
        return result.scalar_one_or_none()
    
    @staticmethod
    async def create(db: AsyncSession, **kwargs) -> User:
        """Create a new user"""
        user = User(
            user_id=kwargs.get('user_id', generate_id('user_')),
            email=kwargs['email'],
            name=kwargs.get('name'),
            picture=kwargs.get('picture'),
            company=kwargs.get('company'),
            auth_provider=kwargs.get('auth_provider'),
            password_hash=kwargs.get('password_hash'),
            email_verified=kwargs.get('email_verified', False),
            registration_ip=kwargs.get('registration_ip'),
            registration_fingerprint=kwargs.get('registration_fingerprint'),
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
        return user
    
    @staticmethod
    async def update(db: AsyncSession, user_id: str, **kwargs) -> Optional[User]:
        """Update user fields"""
        await db.execute(
            update(User).where(User.user_id == user_id).values(**kwargs)
        )
        await db.commit()
        return await UserService.get_by_user_id(db, user_id)
    
    @staticmethod
    def to_dict(user: User) -> dict:
        """Convert User model to dictionary"""
        if not user:
            return None
        return {
            "user_id": user.user_id,
            "email": user.email,
            "name": user.name,
            "picture": user.picture,
            "company": user.company,
            "auth_provider": user.auth_provider,
            "email_verified": user.email_verified,
            "onboarding_completed": user.onboarding_completed,
            "preferences": user.preferences or {},
            "created_at": user.created_at.isoformat() if user.created_at else None,
        }


# ================== SESSION SERVICES ==================

class SessionService:
    """Session-related database operations"""
    
    @staticmethod
    async def create(db: AsyncSession, user_id: str, session_token: str, expires_days: int = 30) -> UserSession:
        """Create a new session"""
        session = UserSession(
            session_id=str(uuid.uuid4()),
            user_id=user_id,
            session_token=session_token,
            expires_at=datetime.now(timezone.utc) + timedelta(days=expires_days)
        )
        db.add(session)
        await db.commit()
        await db.refresh(session)
        return session
    
    @staticmethod
    async def get_by_token(db: AsyncSession, token: str) -> Optional[UserSession]:
        """Get session by token"""
        result = await db.execute(
            select(UserSession).where(
                and_(
                    UserSession.session_token == token,
                    UserSession.expires_at > datetime.now(timezone.utc)
                )
            )
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def delete_by_token(db: AsyncSession, token: str) -> None:
        """Delete session by token"""
        await db.execute(delete(UserSession).where(UserSession.session_token == token))
        await db.commit()
    
    @staticmethod
    async def delete_by_user(db: AsyncSession, user_id: str) -> None:
        """Delete all sessions for a user"""
        await db.execute(delete(UserSession).where(UserSession.user_id == user_id))
        await db.commit()


# ================== SUBSCRIPTION SERVICES ==================

class SubscriptionService:
    """Subscription-related database operations"""
    
    @staticmethod
    async def get_by_user_id(db: AsyncSession, user_id: str) -> Optional[Subscription]:
        """Get subscription by user_id"""
        result = await db.execute(select(Subscription).where(Subscription.user_id == user_id))
        return result.scalar_one_or_none()
    
    @staticmethod
    async def create_free(db: AsyncSession, user_id: str) -> Subscription:
        """Create a free subscription for new user"""
        subscription = Subscription(
            subscription_id=generate_id('sub_'),
            user_id=user_id,
            plan=SubscriptionPlan.FREE,
            status=SubscriptionStatus.ACTIVE,
            queries_limit=90,
            queries_used=0,
            scans_limit=1,
            scans_used=0,
            free_scans_remaining=1,
            article_optimizer_limit=0,
            article_optimizer_used=0,
            current_period_start=datetime.now(timezone.utc),
        )
        db.add(subscription)
        await db.commit()
        await db.refresh(subscription)
        return subscription
    
    @staticmethod
    async def update(db: AsyncSession, user_id: str, **kwargs) -> Optional[Subscription]:
        """Update subscription fields"""
        await db.execute(
            update(Subscription).where(Subscription.user_id == user_id).values(**kwargs)
        )
        await db.commit()
        return await SubscriptionService.get_by_user_id(db, user_id)
    
    @staticmethod
    def to_dict(sub: Subscription) -> dict:
        """Convert Subscription model to dictionary"""
        if not sub:
            return None
        return {
            "subscription_id": sub.subscription_id,
            "user_id": sub.user_id,
            "plan": sub.plan.value if sub.plan else "free",
            "status": sub.status.value if sub.status else "active",
            "queries_limit": sub.queries_limit,
            "queries_used": sub.queries_used,
            "scans_limit": sub.scans_limit,
            "scans_used": sub.scans_used,
            "free_scans_remaining": sub.free_scans_remaining,
            "article_optimizer_limit": sub.article_optimizer_limit,
            "article_optimizer_used": sub.article_optimizer_used,
            "stripe_customer_id": sub.stripe_customer_id,
            "stripe_subscription_id": sub.stripe_subscription_id,
            "current_period_start": sub.current_period_start.isoformat() if sub.current_period_start else None,
            "current_period_end": sub.current_period_end.isoformat() if sub.current_period_end else None,
            "cancelled_at": sub.cancelled_at.isoformat() if sub.cancelled_at else None,
            "created_at": sub.created_at.isoformat() if sub.created_at else None,
        }


# ================== PROJECT SERVICES ==================

class ProjectService:
    """Project-related database operations"""
    
    @staticmethod
    async def get_by_id(db: AsyncSession, project_id: str) -> Optional[Project]:
        """Get project by project_id"""
        result = await db.execute(select(Project).where(Project.project_id == project_id))
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_by_user(db: AsyncSession, user_id: str) -> List[Project]:
        """Get all projects for a user"""
        result = await db.execute(
            select(Project).where(Project.user_id == user_id).order_by(Project.created_at.desc())
        )
        return list(result.scalars().all())
    
    @staticmethod
    async def create(db: AsyncSession, user_id: str, **kwargs) -> Project:
        """Create a new project"""
        project = Project(
            project_id=generate_id('proj_'),
            user_id=user_id,
            name=kwargs['name'],
            website_url=kwargs.get('website_url'),
            brand_name=kwargs.get('brand_name'),
            logo_url=kwargs.get('logo_url'),
            competitors=kwargs.get('competitors', []),
            keywords=kwargs.get('keywords', []),
            industry=kwargs.get('industry'),
            description=kwargs.get('description'),
            organization_id=kwargs.get('organization_id'),
        )
        db.add(project)
        await db.commit()
        await db.refresh(project)
        return project
    
    @staticmethod
    async def update(db: AsyncSession, project_id: str, **kwargs) -> Optional[Project]:
        """Update project fields"""
        await db.execute(
            update(Project).where(Project.project_id == project_id).values(**kwargs)
        )
        await db.commit()
        return await ProjectService.get_by_id(db, project_id)
    
    @staticmethod
    async def delete(db: AsyncSession, project_id: str) -> bool:
        """Delete a project"""
        result = await db.execute(delete(Project).where(Project.project_id == project_id))
        await db.commit()
        return result.rowcount > 0
    
    @staticmethod
    async def count_by_user(db: AsyncSession, user_id: str) -> int:
        """Count projects for a user"""
        result = await db.execute(
            select(func.count(Project.id)).where(Project.user_id == user_id)
        )
        return result.scalar() or 0
    
    @staticmethod
    def to_dict(project: Project) -> dict:
        """Convert Project model to dictionary"""
        if not project:
            return None
        return {
            "project_id": project.project_id,
            "user_id": project.user_id,
            "organization_id": project.organization_id,
            "name": project.name,
            "website_url": project.website_url,
            "brand_name": project.brand_name,
            "logo_url": project.logo_url,
            "competitors": project.competitors or [],
            "keywords": project.keywords or [],
            "industry": project.industry,
            "description": project.description,
            "created_at": project.created_at.isoformat() if project.created_at else None,
            "updated_at": project.updated_at.isoformat() if project.updated_at else None,
        }


# ================== ANALYSIS SERVICES ==================

class AnalysisService:
    """Analysis-related database operations"""
    
    @staticmethod
    async def get_by_id(db: AsyncSession, analysis_id: str) -> Optional[Analysis]:
        """Get analysis by analysis_id"""
        result = await db.execute(select(Analysis).where(Analysis.analysis_id == analysis_id))
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_by_project(db: AsyncSession, project_id: str, limit: int = 10) -> List[Analysis]:
        """Get analyses for a project"""
        result = await db.execute(
            select(Analysis)
            .where(Analysis.project_id == project_id)
            .order_by(Analysis.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())
    
    @staticmethod
    async def get_by_user(db: AsyncSession, user_id: str, limit: int = 50) -> List[Analysis]:
        """Get analyses for a user"""
        result = await db.execute(
            select(Analysis)
            .where(Analysis.user_id == user_id)
            .order_by(Analysis.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())
    
    @staticmethod
    async def get_latest_by_project(db: AsyncSession, project_id: str) -> Optional[Analysis]:
        """Get latest analysis for a project"""
        result = await db.execute(
            select(Analysis)
            .where(Analysis.project_id == project_id)
            .order_by(Analysis.created_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def create(db: AsyncSession, project_id: str, user_id: str, **kwargs) -> Analysis:
        """Create a new analysis"""
        analysis = Analysis(
            analysis_id=generate_id('ana_'),
            project_id=project_id,
            user_id=user_id,
            status=AnalysisStatus.PENDING,
            **kwargs
        )
        db.add(analysis)
        await db.commit()
        await db.refresh(analysis)
        return analysis
    
    @staticmethod
    async def update(db: AsyncSession, analysis_id: str, **kwargs) -> Optional[Analysis]:
        """Update analysis fields"""
        await db.execute(
            update(Analysis).where(Analysis.analysis_id == analysis_id).values(**kwargs)
        )
        await db.commit()
        return await AnalysisService.get_by_id(db, analysis_id)
    
    @staticmethod
    async def count_by_user(db: AsyncSession, user_id: str) -> int:
        """Count analyses for a user"""
        result = await db.execute(
            select(func.count(Analysis.id)).where(Analysis.user_id == user_id)
        )
        return result.scalar() or 0
    
    @staticmethod
    def to_dict(analysis: Analysis) -> dict:
        """Convert Analysis model to dictionary"""
        if not analysis:
            return None
        
        # Extract progress from ai_scores (workaround for missing columns)
        ai_scores = analysis.ai_scores or {}
        queries_processed = ai_scores.pop('_progress', 0) if isinstance(ai_scores, dict) else 0
        current_phase = ai_scores.pop('_phase', None) if isinstance(ai_scores, dict) else None
        
        # Try to get from actual columns first (if they exist)
        if hasattr(analysis, 'queries_processed') and analysis.queries_processed:
            queries_processed = analysis.queries_processed
        if hasattr(analysis, 'current_phase') and analysis.current_phase:
            current_phase = analysis.current_phase
        
        return {
            "analysis_id": analysis.analysis_id,
            "project_id": analysis.project_id,
            "user_id": analysis.user_id,
            "status": analysis.status.value if analysis.status else "pending",
            "global_score": analysis.global_score,
            "grade": analysis.grade,
            "ai_scores": {k: v for k, v in (ai_scores or {}).items() if not k.startswith('_')},
            "rate_scores": analysis.rate_scores or {},
            "query_scores": analysis.query_scores or [],
            "competitor_analysis": analysis.competitor_analysis or {},
            "recommendations": analysis.recommendations or [],
            "stability_score": analysis.stability_score,
            "total_queries": analysis.total_queries or 0,
            "queries_processed": queries_processed,
            "queries_with_mention": analysis.queries_with_mention or 0,
            "current_phase": current_phase,
            "mention_rate": analysis.mention_rate,
            "average_position": analysis.average_position,
            "ai_engines_used": analysis.ai_engines_used or [],
            "error_message": analysis.error_message,
            "started_at": analysis.started_at.isoformat() if analysis.started_at else None,
            "completed_at": analysis.completed_at.isoformat() if analysis.completed_at else None,
            "created_at": analysis.created_at.isoformat() if analysis.created_at else None,
        }


# ================== NOTIFICATION SERVICES ==================

class NotificationService:
    """Notification-related database operations"""
    
    @staticmethod
    async def get_by_user(db: AsyncSession, user_id: str, unread_only: bool = False, limit: int = 50) -> List[Notification]:
        """Get notifications for a user"""
        query = select(Notification).where(Notification.user_id == user_id)
        if unread_only:
            query = query.where(Notification.read == False)
        query = query.order_by(Notification.created_at.desc()).limit(limit)
        result = await db.execute(query)
        return list(result.scalars().all())
    
    @staticmethod
    async def create(db: AsyncSession, user_id: str, type: str, title: str, message: str = None, data: dict = None) -> Notification:
        """Create a new notification"""
        notification = Notification(
            notification_id=generate_id('notif_'),
            user_id=user_id,
            type=type,
            title=title,
            message=message,
            data=data or {},
        )
        db.add(notification)
        await db.commit()
        await db.refresh(notification)
        return notification
    
    @staticmethod
    async def mark_read(db: AsyncSession, notification_id: str) -> bool:
        """Mark notification as read"""
        result = await db.execute(
            update(Notification).where(Notification.notification_id == notification_id).values(read=True)
        )
        await db.commit()
        return result.rowcount > 0
    
    @staticmethod
    async def mark_all_read(db: AsyncSession, user_id: str) -> int:
        """Mark all notifications as read for a user"""
        result = await db.execute(
            update(Notification).where(
                and_(Notification.user_id == user_id, Notification.read == False)
            ).values(read=True)
        )
        await db.commit()
        return result.rowcount
    
    @staticmethod
    async def delete_all(db: AsyncSession, user_id: str) -> int:
        """Delete all notifications for a user"""
        result = await db.execute(delete(Notification).where(Notification.user_id == user_id))
        await db.commit()
        return result.rowcount
    
    @staticmethod
    async def count_unread(db: AsyncSession, user_id: str) -> int:
        """Count unread notifications for a user"""
        result = await db.execute(
            select(func.count(Notification.id)).where(
                and_(Notification.user_id == user_id, Notification.read == False)
            )
        )
        return result.scalar() or 0
    
    @staticmethod
    def to_dict(notif: Notification) -> dict:
        """Convert Notification model to dictionary"""
        if not notif:
            return None
        return {
            "notification_id": notif.notification_id,
            "user_id": notif.user_id,
            "type": notif.type,
            "title": notif.title,
            "message": notif.message,
            "data": notif.data or {},
            "read": notif.read,
            "created_at": notif.created_at.isoformat() if notif.created_at else None,
        }


# ================== SCHEDULE SERVICES ==================

class ScheduleService:
    """Schedule-related database operations"""
    
    @staticmethod
    async def get_by_id(db: AsyncSession, schedule_id: str) -> Optional[ScanSchedule]:
        """Get schedule by schedule_id"""
        result = await db.execute(select(ScanSchedule).where(ScanSchedule.schedule_id == schedule_id))
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_by_user(db: AsyncSession, user_id: str) -> List[ScanSchedule]:
        """Get schedules for a user"""
        result = await db.execute(
            select(ScanSchedule).where(ScanSchedule.user_id == user_id).order_by(ScanSchedule.created_at.desc())
        )
        return list(result.scalars().all())
    
    @staticmethod
    async def get_by_project(db: AsyncSession, project_id: str) -> Optional[ScanSchedule]:
        """Get schedule for a project"""
        result = await db.execute(select(ScanSchedule).where(ScanSchedule.project_id == project_id))
        return result.scalar_one_or_none()
    
    @staticmethod
    async def create(db: AsyncSession, user_id: str, project_id: str, **kwargs) -> ScanSchedule:
        """Create a new schedule"""
        schedule = ScanSchedule(
            schedule_id=generate_id('sched_'),
            user_id=user_id,
            project_id=project_id,
            frequency=kwargs.get('frequency', 'weekly'),
            time=kwargs.get('time', '09:00'),
            day_of_week=kwargs.get('day_of_week'),
            day_of_month=kwargs.get('day_of_month'),
            hour=kwargs.get('hour', 9),
            minute=kwargs.get('minute', 0),
            email_report=kwargs.get('email_report', True),
            send_report_email=kwargs.get('send_report_email', True),
            report_recipients=kwargs.get('report_recipients', []),
            enabled=kwargs.get('enabled', True),
        )
        db.add(schedule)
        await db.commit()
        await db.refresh(schedule)
        return schedule
    
    @staticmethod
    async def update(db: AsyncSession, schedule_id: str, **kwargs) -> Optional[ScanSchedule]:
        """Update schedule fields"""
        await db.execute(
            update(ScanSchedule).where(ScanSchedule.schedule_id == schedule_id).values(**kwargs)
        )
        await db.commit()
        return await ScheduleService.get_by_id(db, schedule_id)
    
    @staticmethod
    async def delete(db: AsyncSession, schedule_id: str) -> bool:
        """Delete a schedule"""
        result = await db.execute(delete(ScanSchedule).where(ScanSchedule.schedule_id == schedule_id))
        await db.commit()
        return result.rowcount > 0
    
    @staticmethod
    def to_dict(schedule: ScanSchedule) -> dict:
        """Convert ScanSchedule model to dictionary"""
        if not schedule:
            return None
        return {
            "schedule_id": schedule.schedule_id,
            "user_id": schedule.user_id,
            "project_id": schedule.project_id,
            "frequency": schedule.frequency,
            "time": schedule.time,
            "day_of_week": schedule.day_of_week,
            "day_of_month": schedule.day_of_month,
            "hour": schedule.hour,
            "minute": schedule.minute,
            "email_report": schedule.email_report,
            "send_report_email": schedule.send_report_email,
            "report_recipients": schedule.report_recipients or [],
            "enabled": schedule.enabled,
            "last_run": schedule.last_run.isoformat() if schedule.last_run else None,
            "next_run": schedule.next_run.isoformat() if schedule.next_run else None,
            "created_at": schedule.created_at.isoformat() if schedule.created_at else None,
        }


# ================== ORGANIZATION SERVICES ==================

class OrganizationService:
    """Organization-related database operations"""
    
    @staticmethod
    async def get_by_id(db: AsyncSession, organization_id: str) -> Optional[Organization]:
        """Get organization by organization_id"""
        result = await db.execute(select(Organization).where(Organization.organization_id == organization_id))
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_by_user(db: AsyncSession, user_id: str) -> List[Organization]:
        """Get organizations where user is a member"""
        result = await db.execute(
            select(Organization)
            .join(OrganizationMember, Organization.organization_id == OrganizationMember.organization_id)
            .where(OrganizationMember.user_id == user_id)
        )
        return list(result.scalars().all())
    
    @staticmethod
    async def create(db: AsyncSession, owner_id: str, **kwargs) -> Organization:
        """Create a new organization"""
        organization = Organization(
            organization_id=generate_id('org_'),
            owner_id=owner_id,
            name=kwargs['name'],
            slug=kwargs.get('slug'),
            description=kwargs.get('description'),
            logo_url=kwargs.get('logo_url'),
            website_url=kwargs.get('website_url'),
            settings=kwargs.get('settings', {}),
        )
        db.add(organization)
        await db.commit()
        await db.refresh(organization)
        
        # Add owner as member
        member = OrganizationMember(
            organization_id=organization.organization_id,
            user_id=owner_id,
            role=OrganizationRole.OWNER,
        )
        db.add(member)
        await db.commit()
        
        return organization
    
    @staticmethod
    def to_dict(org: Organization) -> dict:
        """Convert Organization model to dictionary"""
        if not org:
            return None
        return {
            "organization_id": org.organization_id,
            "name": org.name,
            "slug": org.slug,
            "description": org.description,
            "logo_url": org.logo_url,
            "website_url": org.website_url,
            "owner_id": org.owner_id,
            "settings": org.settings or {},
            "created_at": org.created_at.isoformat() if org.created_at else None,
        }
