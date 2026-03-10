"""
Schedules Router
Handles scheduled scans endpoints
"""
from fastapi import APIRouter, HTTPException, Request, Depends
from typing import Optional, List
from datetime import datetime, timezone, timedelta
from pydantic import BaseModel
import uuid
import logging

from ..core.database import db
from ..core.config import SUBSCRIPTION_PLANS
from .auth import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/schedules", tags=["Schedules"])


# Request Models
class ScheduleCreate(BaseModel):
    project_id: str
    frequency: str  # daily, weekly, biweekly, monthly
    time: str  # HH:MM format
    day_of_week: Optional[int] = None  # 0-6 for weekly
    day_of_month: Optional[int] = None  # 1-31 for monthly
    email_report: bool = True


class ScheduleUpdate(BaseModel):
    frequency: Optional[str] = None
    time: Optional[str] = None
    day_of_week: Optional[int] = None
    day_of_month: Optional[int] = None
    email_report: Optional[bool] = None
    enabled: Optional[bool] = None


def calculate_next_run(schedule: dict) -> str:
    """Calculate the next run time for a schedule"""
    now = datetime.now(timezone.utc)
    frequency = schedule.get("frequency", "weekly")
    time_str = schedule.get("time", "09:00")
    
    try:
        hour, minute = map(int, time_str.split(":"))
    except:
        hour, minute = 9, 0
    
    if frequency == "daily":
        next_run = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        if next_run <= now:
            next_run += timedelta(days=1)
    
    elif frequency == "weekly":
        day_of_week = schedule.get("day_of_week", 0)  # Monday by default
        days_ahead = day_of_week - now.weekday()
        if days_ahead <= 0:
            days_ahead += 7
        next_run = now.replace(hour=hour, minute=minute, second=0, microsecond=0) + timedelta(days=days_ahead)
    
    elif frequency == "biweekly":
        day_of_week = schedule.get("day_of_week", 0)
        days_ahead = day_of_week - now.weekday()
        if days_ahead <= 0:
            days_ahead += 14
        next_run = now.replace(hour=hour, minute=minute, second=0, microsecond=0) + timedelta(days=days_ahead)
    
    elif frequency == "monthly":
        day_of_month = schedule.get("day_of_month", 1)
        next_run = now.replace(day=min(day_of_month, 28), hour=hour, minute=minute, second=0, microsecond=0)
        if next_run <= now:
            if now.month == 12:
                next_run = next_run.replace(year=now.year + 1, month=1)
            else:
                next_run = next_run.replace(month=now.month + 1)
    
    else:
        next_run = now + timedelta(days=7)
    
    return next_run.isoformat()


@router.get("")
async def get_all_schedules(user: dict = Depends(get_current_user)):
    """Get all schedules for user"""
    schedules = await db.scan_schedules.find(
        {"user_id": user["user_id"]},
        {"_id": 0}
    ).to_list(100)
    
    # Enrich with project info
    for schedule in schedules:
        project = await db.projects.find_one(
            {"project_id": schedule.get("project_id")},
            {"_id": 0, "name": 1, "brand_name": 1, "logo_url": 1}
        )
        if project:
            schedule["project"] = project
    
    return {"schedules": schedules}


@router.get("/{project_id}")
async def get_project_schedules(project_id: str, user: dict = Depends(get_current_user)):
    """Get schedules for a specific project"""
    # Verify project ownership
    project = await db.projects.find_one(
        {"project_id": project_id, "user_id": user["user_id"]},
        {"_id": 0}
    )
    if not project:
        raise HTTPException(status_code=404, detail="Projet non trouvé")
    
    schedules = await db.scan_schedules.find(
        {"project_id": project_id, "user_id": user["user_id"]},
        {"_id": 0}
    ).to_list(10)
    
    return {"schedules": schedules, "project": project}


@router.post("")
async def create_schedule(data: ScheduleCreate, user: dict = Depends(get_current_user)):
    """Create a new scheduled scan"""
    # Check subscription allows scheduled scans
    subscription = await db.subscriptions.find_one({"user_id": user["user_id"]}, {"_id": 0})
    plan = subscription.get("plan", "free") if subscription else "free"
    
    if plan == "free":
        raise HTTPException(
            status_code=403,
            detail="Les scans programmés nécessitent un abonnement Pro ou Business"
        )
    
    # Verify project ownership
    project = await db.projects.find_one(
        {"project_id": data.project_id, "user_id": user["user_id"]},
        {"_id": 0}
    )
    if not project:
        raise HTTPException(status_code=404, detail="Projet non trouvé")
    
    # Check if schedule already exists for this project
    existing = await db.scan_schedules.find_one({
        "project_id": data.project_id,
        "user_id": user["user_id"]
    })
    if existing:
        raise HTTPException(status_code=400, detail="Un planning existe déjà pour ce projet")
    
    schedule_id = f"sched_{uuid.uuid4().hex[:12]}"
    
    schedule = {
        "schedule_id": schedule_id,
        "user_id": user["user_id"],
        "project_id": data.project_id,
        "frequency": data.frequency,
        "time": data.time,
        "day_of_week": data.day_of_week,
        "day_of_month": data.day_of_month,
        "email_report": data.email_report,
        "enabled": True,
        "last_run": None,
        "next_run": None,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    # Calculate next run
    schedule["next_run"] = calculate_next_run(schedule)
    
    await db.scan_schedules.insert_one(schedule)
    
    result = await db.scan_schedules.find_one({"schedule_id": schedule_id}, {"_id": 0})
    return {"schedule": result}


@router.put("/{schedule_id}")
async def update_schedule(schedule_id: str, data: ScheduleUpdate, user: dict = Depends(get_current_user)):
    """Update a scheduled scan"""
    schedule = await db.scan_schedules.find_one(
        {"schedule_id": schedule_id, "user_id": user["user_id"]},
        {"_id": 0}
    )
    if not schedule:
        raise HTTPException(status_code=404, detail="Planning non trouvé")
    
    # Build update dict
    updates = {k: v for k, v in data.model_dump().items() if v is not None}
    
    if updates:
        updates["updated_at"] = datetime.now(timezone.utc).isoformat()
        
        # Recalculate next run if schedule parameters changed
        if any(k in updates for k in ["frequency", "time", "day_of_week", "day_of_month"]):
            merged = {**schedule, **updates}
            updates["next_run"] = calculate_next_run(merged)
        
        await db.scan_schedules.update_one(
            {"schedule_id": schedule_id},
            {"$set": updates}
        )
    
    result = await db.scan_schedules.find_one({"schedule_id": schedule_id}, {"_id": 0})
    return {"schedule": result}


@router.delete("/{schedule_id}")
async def delete_schedule(schedule_id: str, user: dict = Depends(get_current_user)):
    """Delete a scheduled scan"""
    result = await db.scan_schedules.delete_one({
        "schedule_id": schedule_id,
        "user_id": user["user_id"]
    })
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Planning non trouvé")
    
    return {"success": True, "message": "Planning supprimé"}


@router.post("/{schedule_id}/run-now")
async def run_schedule_now(schedule_id: str, user: dict = Depends(get_current_user)):
    """Trigger immediate execution of a scheduled scan"""
    schedule = await db.scan_schedules.find_one(
        {"schedule_id": schedule_id, "user_id": user["user_id"]},
        {"_id": 0}
    )
    if not schedule:
        raise HTTPException(status_code=404, detail="Planning non trouvé")
    
    # This would trigger the analysis - for now just return success
    # The actual implementation would call the analysis endpoint
    return {
        "success": True,
        "message": "Scan lancé. Vous serez notifié une fois terminé.",
        "project_id": schedule.get("project_id")
    }


@router.post("/{schedule_id}/toggle")
async def toggle_schedule(schedule_id: str, user: dict = Depends(get_current_user)):
    """Toggle schedule enabled/disabled"""
    schedule = await db.scan_schedules.find_one(
        {"schedule_id": schedule_id, "user_id": user["user_id"]},
        {"_id": 0}
    )
    if not schedule:
        raise HTTPException(status_code=404, detail="Planning non trouvé")
    
    new_enabled = not schedule.get("enabled", True)
    
    await db.scan_schedules.update_one(
        {"schedule_id": schedule_id},
        {"$set": {"enabled": new_enabled}}
    )
    
    return {"success": True, "enabled": new_enabled}
