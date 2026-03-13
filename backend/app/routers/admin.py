"""
Admin Backoffice Router - PostgreSQL Version
API endpoints for admin dashboard and management
"""
from fastapi import APIRouter, HTTPException, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, update, Integer, cast
from typing import Optional, List
from datetime import datetime, timezone, timedelta
from pydantic import BaseModel
import logging

from ..db.database import async_session_maker
from ..db.models import (
    User, UserSession, Subscription, Project, Analysis, 
    Organization, ArticleOptimization, AdminLog, Notification,
    SubscriptionPlan, AnalysisStatus
)
from ..db.services import UserService, SessionService, SubscriptionService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/admin", tags=["Admin"])


# ================== HELPER FUNCTIONS ==================

async def get_admin_user(request: Request) -> dict:
    """Get current user and verify admin access"""
    token = request.cookies.get("session_token")
    if not token:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
    
    if not token:
        raise HTTPException(status_code=401, detail="Non authentifié")
    
    async with async_session_maker() as db:
        # Get session
        session = await SessionService.get_by_token(db, token)
        if not session:
            raise HTTPException(status_code=401, detail="Session expirée")
        
        # Check expiry
        if session.expires_at < datetime.now(timezone.utc):
            raise HTTPException(status_code=401, detail="Session expirée")
        
        # Get user
        user = await UserService.get_by_user_id(db, session.user_id)
        if not user:
            raise HTTPException(status_code=401, detail="Utilisateur non trouvé")
        
        # Check admin role
        if user.role not in ["admin", "super_admin"]:
            raise HTTPException(status_code=403, detail="Accès admin requis")
        
        return UserService.to_dict(user)


# ================== DASHBOARD STATS ==================

@router.get("/stats")
async def get_admin_stats(admin: dict = Depends(get_admin_user)):
    """Get global platform statistics"""
    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    
    async with async_session_maker() as db:
        # User stats
        total_users = await db.scalar(select(func.count(User.id)))
        users_today = await db.scalar(
            select(func.count(User.id)).where(User.created_at >= today_start)
        )
        users_this_month = await db.scalar(
            select(func.count(User.id)).where(User.created_at >= month_start)
        )
        verified_users = await db.scalar(
            select(func.count(User.id)).where(User.email_verified.is_(True))
        )
        
        # Subscription stats by plan
        plan_counts = await db.execute(
            select(Subscription.plan, func.count(Subscription.id))
            .group_by(Subscription.plan)
        )
        plan_distribution = {str(plan): count for plan, count in plan_counts.fetchall()}
        
        # Analysis stats
        total_analyses = await db.scalar(select(func.count(Analysis.id)))
        analyses_today = await db.scalar(
            select(func.count(Analysis.id)).where(Analysis.created_at >= today_start)
        )
        analyses_this_month = await db.scalar(
            select(func.count(Analysis.id)).where(Analysis.created_at >= month_start)
        )
        completed_analyses = await db.scalar(
            select(func.count(Analysis.id)).where(Analysis.status == AnalysisStatus.completed)
        )
        failed_analyses = await db.scalar(
            select(func.count(Analysis.id)).where(Analysis.status == AnalysisStatus.failed)
        )
        
        # Project stats
        total_projects = await db.scalar(select(func.count(Project.id)))
        
        # Organization stats
        total_organizations = await db.scalar(select(func.count(Organization.id)))
        
        # Article optimizer stats
        total_optimizations = await db.scalar(select(func.count(ArticleOptimization.id))) or 0
        optimizations_this_month = await db.scalar(
            select(func.count(ArticleOptimization.id)).where(ArticleOptimization.created_at >= month_start)
        ) or 0
        
        # Revenue estimation
        price_map = {"free": 0, "starter": 79, "pro": 149, "business": 349}
        monthly_revenue = sum(
            plan_distribution.get(plan, 0) * price 
            for plan, price in price_map.items()
        )
        
        total_users = total_users or 0
        free_users = plan_distribution.get("free", 0)
        
        return {
            "users": {
                "total": total_users,
                "today": users_today or 0,
                "this_month": users_this_month or 0,
                "verified": verified_users or 0,
                "verification_rate": round((verified_users or 0) / max(total_users, 1) * 100, 1)
            },
            "subscriptions": {
                "distribution": plan_distribution,
                "paid_users": total_users - free_users,
                "conversion_rate": round((total_users - free_users) / max(total_users, 1) * 100, 1)
            },
            "analyses": {
                "total": total_analyses or 0,
                "today": analyses_today or 0,
                "this_month": analyses_this_month or 0,
                "completed": completed_analyses or 0,
                "failed": failed_analyses or 0,
                "success_rate": round((completed_analyses or 0) / max(total_analyses or 1, 1) * 100, 1)
            },
            "projects": {
                "total": total_projects or 0
            },
            "organizations": {
                "total": total_organizations or 0
            },
            "article_optimizer": {
                "total": total_optimizations,
                "this_month": optimizations_this_month
            },
            "revenue": {
                "estimated_mrr": monthly_revenue
            }
        }


# ================== USER MANAGEMENT ==================

@router.get("/users")
async def list_users(
    skip: int = 0,
    limit: int = 50,
    search: Optional[str] = None,
    plan: Optional[str] = None,
    admin: dict = Depends(get_admin_user)
):
    """List all users with filtering"""
    async with async_session_maker() as db:
        query = select(User)
        
        if search:
            query = query.where(
                (User.email.ilike(f"%{search}%")) | 
                (User.name.ilike(f"%{search}%"))
            )
        
        # Get total count
        count_query = select(func.count(User.id))
        if search:
            count_query = count_query.where(
                (User.email.ilike(f"%{search}%")) | 
                (User.name.ilike(f"%{search}%"))
            )
        total = await db.scalar(count_query)
        
        # Get users with pagination
        query = query.order_by(User.created_at.desc()).offset(skip).limit(limit)
        result = await db.execute(query)
        users = result.scalars().all()
        
        users_data = []
        for user in users:
            user_dict = UserService.to_dict(user)
            
            # Get subscription
            sub = await SubscriptionService.get_by_user_id(db, user.user_id)
            if sub:
                user_dict["subscription"] = {
                    "plan": str(sub.plan.value) if sub.plan else "free",
                    "status": str(sub.status.value) if sub.status else "active",
                    "queries_used": sub.queries_used,
                    "scans_used": sub.scans_used
                }
            
            # Filter by plan if specified
            if plan and user_dict.get("subscription", {}).get("plan") != plan:
                continue
                
            users_data.append(user_dict)
        
        return {
            "users": users_data,
            "total": total or 0,
            "skip": skip,
            "limit": limit
        }


@router.get("/users/{user_id}")
async def get_user_details(user_id: str, admin: dict = Depends(get_admin_user)):
    """Get detailed user information"""
    async with async_session_maker() as db:
        user = await UserService.get_by_user_id(db, user_id)
        if not user:
            raise HTTPException(status_code=404, detail="Utilisateur non trouvé")
        
        user_dict = UserService.to_dict(user)
        
        # Get subscription
        subscription = await SubscriptionService.get_by_user_id(db, user_id)
        sub_dict = SubscriptionService.to_dict(subscription) if subscription else None
        
        # Get projects
        projects_result = await db.execute(
            select(Project).where(Project.user_id == user_id).limit(100)
        )
        projects = [
            {
                "project_id": p.project_id,
                "name": p.name,
                "domain": p.domain,
                "created_at": p.created_at.isoformat() if p.created_at else None
            }
            for p in projects_result.scalars().all()
        ]
        
        # Get recent analyses
        analyses_result = await db.execute(
            select(Analysis)
            .where(Analysis.user_id == user_id)
            .order_by(Analysis.created_at.desc())
            .limit(10)
        )
        analyses = [
            {
                "analysis_id": a.analysis_id,
                "status": str(a.status.value) if a.status else None,
                "global_score": a.global_score,
                "created_at": a.created_at.isoformat() if a.created_at else None
            }
            for a in analyses_result.scalars().all()
        ]
        
        # Get organization
        organization = None
        if user.organization_id:
            org_result = await db.execute(
                select(Organization).where(Organization.organization_id == user.organization_id)
            )
            org = org_result.scalar_one_or_none()
            if org:
                organization = {
                    "organization_id": org.organization_id,
                    "name": org.name
                }
        
        return {
            "user": user_dict,
            "subscription": sub_dict,
            "projects": projects,
            "recent_analyses": analyses,
            "organization": organization
        }


@router.put("/users/{user_id}/subscription")
async def update_user_subscription(
    user_id: str,
    request: Request,
    admin: dict = Depends(get_admin_user)
):
    """Update user subscription (admin override)"""
    body = await request.json()
    plan = body.get("plan")
    
    if plan not in ["free", "starter", "pro", "business"]:
        raise HTTPException(status_code=400, detail="Plan invalide")
    
    async with async_session_maker() as db:
        # Update subscription
        result = await db.execute(
            update(Subscription)
            .where(Subscription.user_id == user_id)
            .values(
                plan=SubscriptionPlan(plan),
                updated_at=datetime.now(timezone.utc)
            )
        )
        await db.commit()
        
        if result.rowcount == 0:
            raise HTTPException(status_code=404, detail="Abonnement non trouvé")
        
        # Log action
        log = AdminLog(
            admin_id=admin["user_id"],
            action="subscription_update",
            target_type="user",
            target_id=user_id,
            details={"new_plan": plan}
        )
        db.add(log)
        await db.commit()
    
    return {"success": True, "message": f"Plan mis à jour: {plan}"}


@router.put("/users/{user_id}/role")
async def update_user_role(
    user_id: str,
    request: Request,
    admin: dict = Depends(get_admin_user)
):
    """Update user role (super_admin only)"""
    if admin.get("role") != "super_admin":
        raise HTTPException(status_code=403, detail="Super admin requis")
    
    body = await request.json()
    role = body.get("role")
    
    if role not in ["user", "admin", "super_admin"]:
        raise HTTPException(status_code=400, detail="Rôle invalide")
    
    async with async_session_maker() as db:
        result = await db.execute(
            update(User)
            .where(User.user_id == user_id)
            .values(role=role)
        )
        await db.commit()
        
        if result.rowcount == 0:
            raise HTTPException(status_code=404, detail="Utilisateur non trouvé")
        
        # Log action
        log = AdminLog(
            admin_id=admin["user_id"],
            action="role_update",
            target_type="user",
            target_id=user_id,
            details={"new_role": role}
        )
        db.add(log)
        await db.commit()
    
    return {"success": True, "message": f"Rôle mis à jour: {role}"}


@router.post("/users/{user_id}/reset-quota")
async def reset_user_quota(user_id: str, admin: dict = Depends(get_admin_user)):
    """Reset user's monthly quota"""
    async with async_session_maker() as db:
        result = await db.execute(
            update(Subscription)
            .where(Subscription.user_id == user_id)
            .values(
                queries_used=0,
                scans_used=0,
                article_optimizer_used=0,
                updated_at=datetime.now(timezone.utc)
            )
        )
        await db.commit()
        
        if result.rowcount == 0:
            raise HTTPException(status_code=404, detail="Abonnement non trouvé")
        
        # Log action
        log = AdminLog(
            admin_id=admin["user_id"],
            action="quota_reset",
            target_type="user",
            target_id=user_id,
            details={}
        )
        db.add(log)
        await db.commit()
    
    return {"success": True, "message": "Quotas réinitialisés"}


# ================== ANALYSES ==================

@router.get("/analyses")
async def list_analyses(
    skip: int = 0,
    limit: int = 50,
    status: Optional[str] = None,
    admin: dict = Depends(get_admin_user)
):
    """List all analyses"""
    async with async_session_maker() as db:
        query = select(Analysis)
        
        if status:
            try:
                status_enum = AnalysisStatus(status)
                query = query.where(Analysis.status == status_enum)
            except ValueError:
                pass
        
        query = query.order_by(Analysis.created_at.desc()).offset(skip).limit(limit)
        result = await db.execute(query)
        analyses = result.scalars().all()
        
        # Get total count
        count_query = select(func.count(Analysis.id))
        if status:
            try:
                status_enum = AnalysisStatus(status)
                count_query = count_query.where(Analysis.status == status_enum)
            except ValueError:
                pass
        total = await db.scalar(count_query)
        
        analyses_data = [
            {
                "analysis_id": a.analysis_id,
                "project_id": a.project_id,
                "user_id": a.user_id,
                "status": str(a.status.value) if a.status else None,
                "global_score": a.global_score,
                "grade": a.grade,
                "created_at": a.created_at.isoformat() if a.created_at else None
            }
            for a in analyses
        ]
        
        return {
            "analyses": analyses_data,
            "total": total or 0
        }


@router.get("/errors")
async def get_recent_errors(
    limit: int = 50,
    admin: dict = Depends(get_admin_user)
):
    """Get recent failed analyses and errors"""
    async with async_session_maker() as db:
        result = await db.execute(
            select(Analysis)
            .where(Analysis.status == AnalysisStatus.failed)
            .order_by(Analysis.created_at.desc())
            .limit(limit)
        )
        analyses = result.scalars().all()
        
        errors_data = [
            {
                "analysis_id": a.analysis_id,
                "project_id": a.project_id,
                "user_id": a.user_id,
                "error_message": a.error_message,
                "created_at": a.created_at.isoformat() if a.created_at else None
            }
            for a in analyses
        ]
        
        return {"errors": errors_data}


# ================== API USAGE ==================

@router.get("/api-usage")
async def get_api_usage(
    days: int = 30,
    admin: dict = Depends(get_admin_user)
):
    """Get API usage statistics"""
    start_date = datetime.now(timezone.utc) - timedelta(days=days)
    
    async with async_session_maker() as db:
        # Get daily analysis counts
        result = await db.execute(
            select(
                func.date(Analysis.created_at).label('date'),
                func.count(Analysis.id).label('count'),
                func.sum(
                    func.cast(Analysis.status == AnalysisStatus.completed, Integer)
                ).label('completed'),
                func.sum(
                    func.cast(Analysis.status == AnalysisStatus.failed, Integer)
                ).label('failed')
            )
            .where(Analysis.created_at >= start_date)
            .group_by(func.date(Analysis.created_at))
            .order_by(func.date(Analysis.created_at))
        )
        
        daily_stats = [
            {
                "date": str(row.date),
                "count": row.count,
                "completed": row.completed or 0,
                "failed": row.failed or 0
            }
            for row in result.fetchall()
        ]
        
        return {
            "period_days": days,
            "daily_usage": daily_stats
        }


# ================== ADMIN LOGS ==================

@router.get("/logs")
async def get_admin_logs(
    limit: int = 100,
    admin: dict = Depends(get_admin_user)
):
    """Get admin action logs"""
    if admin.get("role") != "super_admin":
        raise HTTPException(status_code=403, detail="Super admin requis")
    
    async with async_session_maker() as db:
        result = await db.execute(
            select(AdminLog)
            .order_by(AdminLog.created_at.desc())
            .limit(limit)
        )
        logs = result.scalars().all()
        
        logs_data = [
            {
                "id": log.id,
                "admin_id": log.admin_id,
                "action": log.action,
                "target_type": log.target_type,
                "target_id": log.target_id,
                "details": log.details,
                "created_at": log.created_at.isoformat() if log.created_at else None
            }
            for log in logs
        ]
        
        return {"logs": logs_data}


# ================== MAKE USER ADMIN ==================

@router.post("/make-admin/{email}")
async def make_user_admin(email: str, admin: dict = Depends(get_admin_user)):
    """Make a user an admin (super_admin only)"""
    if admin.get("role") != "super_admin":
        raise HTTPException(status_code=403, detail="Super admin requis")
    
    async with async_session_maker() as db:
        user = await UserService.get_by_email(db, email)
        if not user:
            raise HTTPException(status_code=404, detail="Utilisateur non trouvé")
        
        await db.execute(
            update(User)
            .where(User.email == email)
            .values(role="admin")
        )
        await db.commit()
        
        return {"success": True, "message": f"{email} est maintenant admin"}


@router.post("/setup-first-admin")
async def setup_first_admin(request: Request):
    """Setup the first super_admin - only works if no admin exists"""
    try:
        body = await request.json()
        email = body.get("email")
        secret = body.get("secret")
        
        if not email:
            raise HTTPException(status_code=400, detail="Email requis")
        
        # Security: require a secret key
        import os
        expected_secret = os.environ.get("ADMIN_SETUP_SECRET", "iaskan_admin_setup_2024")
        if secret != expected_secret:
            raise HTTPException(status_code=403, detail="Secret invalide")
        
        async with async_session_maker() as db:
            # Check if any admin already exists
            existing_admin = await db.execute(
                select(User).where(User.role.in_(["admin", "super_admin"]))
            )
            if existing_admin.scalar_one_or_none():
                raise HTTPException(status_code=400, detail="Un admin existe déjà")
            
            # Find user by email
            user = await UserService.get_by_email(db, email)
            if not user:
                raise HTTPException(status_code=404, detail=f"Utilisateur '{email}' non trouvé. Connectez-vous d'abord avec Google sur www.iaskan.com")
            
            # Make super_admin
            await db.execute(
                update(User)
                .where(User.email == email)
                .values(role="super_admin")
            )
            await db.commit()
            
            return {"success": True, "message": f"{email} est maintenant super_admin"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Setup first admin error: {e}")
        raise HTTPException(status_code=500, detail=f"Erreur: {str(e)}")
