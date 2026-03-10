"""
Admin Backoffice Router
API endpoints for admin dashboard and management
"""
from fastapi import APIRouter, HTTPException, Depends, Request
from typing import Optional, List
from datetime import datetime, timezone, timedelta
from pydantic import BaseModel

from ..core.database import db

router = APIRouter(prefix="/api/admin", tags=["Admin"])


# Helper to check admin access
async def get_admin_user(request: Request) -> dict:
    """Get current user and verify admin access"""
    token = request.cookies.get("session_token")
    if not token:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
    
    if not token:
        raise HTTPException(status_code=401, detail="Non authentifié")
    
    session = await db.user_sessions.find_one({"session_token": token}, {"_id": 0})
    if not session:
        raise HTTPException(status_code=401, detail="Session expirée")
    
    user = await db.users.find_one({"user_id": session["user_id"]}, {"_id": 0})
    if not user:
        raise HTTPException(status_code=401, detail="Utilisateur non trouvé")
    
    # Check admin role
    if user.get("role") not in ["admin", "super_admin"]:
        raise HTTPException(status_code=403, detail="Accès admin requis")
    
    return user


# Dashboard stats
@router.get("/stats")
async def get_admin_stats(admin: dict = Depends(get_admin_user)):
    """Get global platform statistics"""
    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    
    # User stats
    total_users = await db.users.count_documents({})
    users_today = await db.users.count_documents({
        "created_at": {"$gte": today_start.isoformat()}
    })
    users_this_month = await db.users.count_documents({
        "created_at": {"$gte": month_start.isoformat()}
    })
    verified_users = await db.users.count_documents({"email_verified": True})
    
    # Subscription stats
    subscriptions = await db.subscriptions.find({}, {"_id": 0, "plan": 1}).to_list(10000)
    plan_distribution = {}
    for sub in subscriptions:
        plan = sub.get("plan", "free")
        plan_distribution[plan] = plan_distribution.get(plan, 0) + 1
    
    # Analysis stats
    total_analyses = await db.analyses.count_documents({})
    analyses_today = await db.analyses.count_documents({
        "created_at": {"$gte": today_start.isoformat()}
    })
    analyses_this_month = await db.analyses.count_documents({
        "created_at": {"$gte": month_start.isoformat()}
    })
    completed_analyses = await db.analyses.count_documents({"status": "completed"})
    failed_analyses = await db.analyses.count_documents({"status": "failed"})
    
    # Project stats
    total_projects = await db.projects.count_documents({})
    
    # Organization stats
    total_organizations = await db.organizations.count_documents({})
    
    # Article optimizer stats
    total_optimizations = await db.article_optimizations.count_documents({})
    optimizations_this_month = await db.article_optimizations.count_documents({
        "created_at": {"$gte": month_start.isoformat()}
    })
    
    # Revenue estimation (based on paid plans)
    monthly_revenue = (
        plan_distribution.get("starter", 0) * 79 +
        plan_distribution.get("pro", 0) * 149 +
        plan_distribution.get("business", 0) * 349
    )
    
    return {
        "users": {
            "total": total_users,
            "today": users_today,
            "this_month": users_this_month,
            "verified": verified_users,
            "verification_rate": round(verified_users / max(total_users, 1) * 100, 1)
        },
        "subscriptions": {
            "distribution": plan_distribution,
            "paid_users": total_users - plan_distribution.get("free", 0),
            "conversion_rate": round((total_users - plan_distribution.get("free", 0)) / max(total_users, 1) * 100, 1)
        },
        "analyses": {
            "total": total_analyses,
            "today": analyses_today,
            "this_month": analyses_this_month,
            "completed": completed_analyses,
            "failed": failed_analyses,
            "success_rate": round(completed_analyses / max(total_analyses, 1) * 100, 1)
        },
        "projects": {
            "total": total_projects
        },
        "organizations": {
            "total": total_organizations
        },
        "article_optimizer": {
            "total": total_optimizations,
            "this_month": optimizations_this_month
        },
        "revenue": {
            "estimated_mrr": monthly_revenue
        }
    }


@router.get("/users")
async def list_users(
    skip: int = 0,
    limit: int = 50,
    search: Optional[str] = None,
    plan: Optional[str] = None,
    admin: dict = Depends(get_admin_user)
):
    """List all users with filtering"""
    query = {}
    
    if search:
        query["$or"] = [
            {"email": {"$regex": search, "$options": "i"}},
            {"name": {"$regex": search, "$options": "i"}}
        ]
    
    users = await db.users.find(query, {"_id": 0}).skip(skip).limit(limit).to_list(limit)
    
    # Enrich with subscription data
    for user in users:
        sub = await db.subscriptions.find_one(
            {"user_id": user["user_id"]},
            {"_id": 0, "plan": 1, "status": 1, "queries_used": 1, "scans_used": 1}
        )
        user["subscription"] = sub
    
    # Filter by plan if specified
    if plan:
        users = [u for u in users if u.get("subscription", {}).get("plan") == plan]
    
    total = await db.users.count_documents(query)
    
    return {
        "users": users,
        "total": total,
        "skip": skip,
        "limit": limit
    }


@router.get("/users/{user_id}")
async def get_user_details(user_id: str, admin: dict = Depends(get_admin_user)):
    """Get detailed user information"""
    user = await db.users.find_one({"user_id": user_id}, {"_id": 0})
    
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur non trouvé")
    
    # Get subscription
    subscription = await db.subscriptions.find_one({"user_id": user_id}, {"_id": 0})
    
    # Get projects
    projects = await db.projects.find({"user_id": user_id}, {"_id": 0}).to_list(100)
    
    # Get analyses
    analyses = await db.analyses.find(
        {"user_id": user_id},
        {"_id": 0, "analysis_id": 1, "status": 1, "global_score": 1, "created_at": 1}
    ).sort("created_at", -1).limit(10).to_list(10)
    
    # Get organization
    organization = None
    if user.get("organization_id"):
        organization = await db.organizations.find_one(
            {"organization_id": user["organization_id"]},
            {"_id": 0}
        )
    
    return {
        "user": user,
        "subscription": subscription,
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
    
    result = await db.subscriptions.update_one(
        {"user_id": user_id},
        {"$set": {
            "plan": plan,
            "status": "active",
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "updated_by": admin["user_id"]
        }}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Abonnement non trouvé")
    
    # Log action
    await db.admin_logs.insert_one({
        "action": "subscription_update",
        "admin_id": admin["user_id"],
        "target_user_id": user_id,
        "details": {"new_plan": plan},
        "created_at": datetime.now(timezone.utc).isoformat()
    })
    
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
    
    result = await db.users.update_one(
        {"user_id": user_id},
        {"$set": {"role": role}}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Utilisateur non trouvé")
    
    # Log action
    await db.admin_logs.insert_one({
        "action": "role_update",
        "admin_id": admin["user_id"],
        "target_user_id": user_id,
        "details": {"new_role": role},
        "created_at": datetime.now(timezone.utc).isoformat()
    })
    
    return {"success": True, "message": f"Rôle mis à jour: {role}"}


@router.get("/analyses")
async def list_analyses(
    skip: int = 0,
    limit: int = 50,
    status: Optional[str] = None,
    admin: dict = Depends(get_admin_user)
):
    """List all analyses"""
    query = {}
    if status:
        query["status"] = status
    
    analyses = await db.analyses.find(
        query,
        {"_id": 0, "analysis_id": 1, "project_id": 1, "user_id": 1, 
         "status": 1, "global_score": 1, "grade": 1, "created_at": 1}
    ).sort("created_at", -1).skip(skip).limit(limit).to_list(limit)
    
    total = await db.analyses.count_documents(query)
    
    return {
        "analyses": analyses,
        "total": total
    }


@router.get("/api-usage")
async def get_api_usage(
    days: int = 30,
    admin: dict = Depends(get_admin_user)
):
    """Get API usage statistics"""
    start_date = datetime.now(timezone.utc) - timedelta(days=days)
    
    # Aggregate analyses by day
    pipeline = [
        {"$match": {"created_at": {"$gte": start_date.isoformat()}}},
        {"$group": {
            "_id": {"$substr": ["$created_at", 0, 10]},
            "count": {"$sum": 1},
            "completed": {"$sum": {"$cond": [{"$eq": ["$status", "completed"]}, 1, 0]}},
            "failed": {"$sum": {"$cond": [{"$eq": ["$status", "failed"]}, 1, 0]}}
        }},
        {"$sort": {"_id": 1}}
    ]
    
    daily_stats = await db.analyses.aggregate(pipeline).to_list(100)
    
    return {
        "period_days": days,
        "daily_usage": daily_stats
    }


@router.get("/errors")
async def get_recent_errors(
    limit: int = 50,
    admin: dict = Depends(get_admin_user)
):
    """Get recent failed analyses and errors"""
    failed_analyses = await db.analyses.find(
        {"status": "failed"},
        {"_id": 0}
    ).sort("created_at", -1).limit(limit).to_list(limit)
    
    return {"errors": failed_analyses}


@router.post("/users/{user_id}/reset-quota")
async def reset_user_quota(user_id: str, admin: dict = Depends(get_admin_user)):
    """Reset user's monthly quota"""
    result = await db.subscriptions.update_one(
        {"user_id": user_id},
        {"$set": {
            "queries_used": 0,
            "scans_used": 0,
            "article_optimizer_used": 0,
            "updated_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Abonnement non trouvé")
    
    # Log action
    await db.admin_logs.insert_one({
        "action": "quota_reset",
        "admin_id": admin["user_id"],
        "target_user_id": user_id,
        "created_at": datetime.now(timezone.utc).isoformat()
    })
    
    return {"success": True, "message": "Quotas réinitialisés"}


@router.get("/logs")
async def get_admin_logs(
    limit: int = 100,
    admin: dict = Depends(get_admin_user)
):
    """Get admin action logs"""
    if admin.get("role") != "super_admin":
        raise HTTPException(status_code=403, detail="Super admin requis")
    
    logs = await db.admin_logs.find(
        {},
        {"_id": 0}
    ).sort("created_at", -1).limit(limit).to_list(limit)
    
    return {"logs": logs}
