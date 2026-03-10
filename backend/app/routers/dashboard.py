"""
Dashboard Router - PostgreSQL Version
Handles dashboard statistics and activity
"""
from fastapi import APIRouter, HTTPException, Request, Depends
from typing import List, Optional
from datetime import datetime, timezone, timedelta
import logging

from ..db.database import async_session_maker
from ..db.services import ProjectService, AnalysisService, SubscriptionService, NotificationService
from .auth import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])


@router.get("/stats")
async def get_dashboard_stats(user: dict = Depends(get_current_user)):
    """Get comprehensive dashboard statistics"""
    async with async_session_maker() as db:
        user_id = user["user_id"]
        
        # Get projects
        projects = await ProjectService.get_by_user(db, user_id)
        project_count = len(projects)
        
        # Get subscription
        subscription = await SubscriptionService.get_by_user_id(db, user_id)
        
        # Get all analyses
        total_analyses = 0
        completed_analyses = 0
        all_scores = []
        recent_analyses = []
        
        for project in projects:
            analyses = await AnalysisService.get_by_project(db, project.project_id, limit=100)
            total_analyses += len(analyses)
            
            for analysis in analyses:
                if analysis.status.value == "completed":
                    completed_analyses += 1
                    if analysis.global_score:
                        all_scores.append(analysis.global_score)
                
                # Get recent analyses (last 7 days)
                if analysis.created_at and analysis.created_at > datetime.now(timezone.utc) - timedelta(days=7):
                    recent_analyses.append({
                        "analysis_id": analysis.analysis_id,
                        "project_id": analysis.project_id,
                        "project_name": project.name,
                        "status": analysis.status.value,
                        "global_score": analysis.global_score,
                        "created_at": analysis.created_at.isoformat()
                    })
        
        # Calculate averages
        average_score = sum(all_scores) / len(all_scores) if all_scores else 0
        best_score = max(all_scores) if all_scores else 0
        
        # Get unread notifications
        unread_count = await NotificationService.count_unread(db, user_id)
        
        return {
            "projects": {
                "total": project_count,
                "limit": -1 if not subscription else None  # Will be calculated based on plan
            },
            "analyses": {
                "total": total_analyses,
                "completed": completed_analyses,
                "this_week": len(recent_analyses)
            },
            "scores": {
                "average": round(average_score, 1),
                "best": round(best_score, 1)
            },
            "subscription": SubscriptionService.to_dict(subscription) if subscription else None,
            "recent_analyses": sorted(recent_analyses, key=lambda x: x["created_at"], reverse=True)[:5],
            "notifications_unread": unread_count
        }


@router.get("/quick-stats")
async def get_quick_stats(user: dict = Depends(get_current_user)):
    """Get quick dashboard stats for header/overview"""
    async with async_session_maker() as db:
        user_id = user["user_id"]
        
        # Get counts
        projects = await ProjectService.get_by_user(db, user_id)
        project_count = len(projects)
        
        analysis_count = 0
        for project in projects:
            analyses = await AnalysisService.get_by_project(db, project.project_id)
            analysis_count += len([a for a in analyses if a.status.value == "completed"])
        
        subscription = await SubscriptionService.get_by_user_id(db, user_id)
        unread_count = await NotificationService.count_unread(db, user_id)
        
        return {
            "projects": project_count,
            "analyses": analysis_count,
            "notifications_unread": unread_count,
            "plan": subscription.plan.value if subscription else "free"
        }


@router.get("/recent-activity")
async def get_recent_activity(user: dict = Depends(get_current_user), limit: int = 10):
    """Get recent activity feed"""
    async with async_session_maker() as db:
        user_id = user["user_id"]
        
        activity = []
        
        # Get recent analyses
        projects = await ProjectService.get_by_user(db, user_id)
        for project in projects:
            analyses = await AnalysisService.get_by_project(db, project.project_id, limit=5)
            for analysis in analyses:
                activity.append({
                    "type": "analysis",
                    "action": "completed" if analysis.status.value == "completed" else analysis.status.value,
                    "project_name": project.name,
                    "project_id": project.project_id,
                    "analysis_id": analysis.analysis_id,
                    "score": analysis.global_score,
                    "timestamp": analysis.created_at.isoformat() if analysis.created_at else None
                })
        
        # Get recent notifications
        notifications = await NotificationService.get_by_user(db, user_id, limit=5)
        for notif in notifications:
            activity.append({
                "type": "notification",
                "action": notif.type,
                "title": notif.title,
                "message": notif.message,
                "read": notif.read,
                "timestamp": notif.created_at.isoformat() if notif.created_at else None
            })
        
        # Sort by timestamp
        activity.sort(key=lambda x: x.get("timestamp") or "", reverse=True)
        
        return activity[:limit]
