"""
Dashboard Router
Handles dashboard statistics and data
"""
from fastapi import APIRouter, HTTPException, Depends
from typing import Optional
from datetime import datetime, timezone, timedelta
import logging

from ..core.database import db
from ..core.config import SUBSCRIPTION_PLANS
from .auth import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])


@router.get("/stats")
async def get_dashboard_stats(project_id: Optional[str] = None, user: dict = Depends(get_current_user)):
    """Get dashboard statistics"""
    # Get subscription
    subscription = await db.subscriptions.find_one({"user_id": user["user_id"]}, {"_id": 0})
    plan = subscription.get("plan", "free") if subscription else "free"
    plan_config = SUBSCRIPTION_PLANS.get(plan, SUBSCRIPTION_PLANS["free"])
    
    # Build query
    query = {"user_id": user["user_id"]}
    if project_id:
        query["project_id"] = project_id
    
    # Get analysis stats
    total_analyses = await db.analyses.count_documents(query)
    completed_analyses = await db.analyses.count_documents({**query, "status": "completed"})
    
    # Get latest analysis
    latest_analysis = await db.analyses.find_one(
        {**query, "status": "completed"},
        {"_id": 0, "analysis_id": 1, "global_score": 1, "grade": 1, "ai_scores": 1, "created_at": 1},
        sort=[("created_at", -1)]
    )
    
    # Get project count
    project_count = await db.projects.count_documents({"user_id": user["user_id"]})
    
    # Get score history (last 10 analyses)
    score_history = await db.analyses.find(
        {**query, "status": "completed"},
        {"_id": 0, "global_score": 1, "created_at": 1}
    ).sort("created_at", -1).limit(10).to_list(10)
    
    # Reverse for chronological order
    score_history.reverse()
    
    # Calculate average score
    if score_history:
        avg_score = sum(a.get("global_score", 0) for a in score_history) / len(score_history)
    else:
        avg_score = 0
    
    # Get this month's usage
    month_start = datetime.now(timezone.utc).replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    analyses_this_month = await db.analyses.count_documents({
        "user_id": user["user_id"],
        "created_at": {"$gte": month_start.isoformat()}
    })
    
    return {
        "subscription": {
            "plan": plan,
            "plan_name": plan_config.get("name", "Free"),
            "queries_used": subscription.get("queries_used", 0) if subscription else 0,
            "queries_limit": plan_config.get("queries_limit", 0),
            "scans_used": subscription.get("scans_used", 0) if subscription else 0,
            "scans_limit": plan_config.get("scans_limit", 0),
            "status": subscription.get("status", "active") if subscription else "active"
        },
        "analyses": {
            "total": total_analyses,
            "completed": completed_analyses,
            "this_month": analyses_this_month
        },
        "projects": {
            "count": project_count,
            "limit": plan_config.get("projects_limit", 1)
        },
        "latest_analysis": latest_analysis,
        "score_history": score_history,
        "average_score": round(avg_score, 1)
    }


@router.get("/recent-activity")
async def get_recent_activity(limit: int = 10, user: dict = Depends(get_current_user)):
    """Get recent user activity"""
    activities = []
    
    # Recent analyses
    analyses = await db.analyses.find(
        {"user_id": user["user_id"]},
        {"_id": 0, "analysis_id": 1, "project_id": 1, "status": 1, "global_score": 1, "created_at": 1}
    ).sort("created_at", -1).limit(limit).to_list(limit)
    
    for analysis in analyses:
        project = await db.projects.find_one(
            {"project_id": analysis.get("project_id")},
            {"_id": 0, "name": 1, "brand_name": 1}
        )
        activities.append({
            "type": "analysis",
            "id": analysis.get("analysis_id"),
            "project_name": project.get("name") if project else "Projet",
            "status": analysis.get("status"),
            "score": analysis.get("global_score"),
            "created_at": analysis.get("created_at")
        })
    
    # Recent notifications
    notifications = await db.notifications.find(
        {"user_id": user["user_id"]},
        {"_id": 0}
    ).sort("created_at", -1).limit(5).to_list(5)
    
    for notif in notifications:
        activities.append({
            "type": "notification",
            "id": notif.get("notification_id"),
            "title": notif.get("title"),
            "message": notif.get("message"),
            "read": notif.get("read"),
            "created_at": notif.get("created_at")
        })
    
    # Sort by date
    activities.sort(key=lambda x: x.get("created_at", ""), reverse=True)
    
    return {"activities": activities[:limit]}


@router.get("/quick-stats")
async def get_quick_stats(user: dict = Depends(get_current_user)):
    """Get quick statistics for dashboard header"""
    # Get subscription
    subscription = await db.subscriptions.find_one({"user_id": user["user_id"]}, {"_id": 0})
    
    # Get latest completed analysis
    latest = await db.analyses.find_one(
        {"user_id": user["user_id"], "status": "completed"},
        {"_id": 0, "global_score": 1, "grade": 1},
        sort=[("created_at", -1)]
    )
    
    # Get previous analysis for comparison
    previous = await db.analyses.find(
        {"user_id": user["user_id"], "status": "completed"},
        {"_id": 0, "global_score": 1}
    ).sort("created_at", -1).skip(1).limit(1).to_list(1)
    
    score_change = 0
    if latest and previous:
        score_change = latest.get("global_score", 0) - previous[0].get("global_score", 0)
    
    # Count unread notifications
    unread_notifications = await db.notifications.count_documents({
        "user_id": user["user_id"],
        "read": False
    })
    
    return {
        "current_score": latest.get("global_score", 0) if latest else None,
        "grade": latest.get("grade", "N/A") if latest else None,
        "score_change": round(score_change, 1),
        "unread_notifications": unread_notifications,
        "plan": subscription.get("plan", "free") if subscription else "free"
    }
