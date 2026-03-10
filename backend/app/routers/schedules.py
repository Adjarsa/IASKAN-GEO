"""
Schedules Router - PostgreSQL Version
Handles scheduled scan operations
"""
from fastapi import APIRouter, HTTPException, Request, Depends
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, timezone
import logging

from ..db.database import async_session_maker
from ..db.services import ScheduleService, ProjectService, SubscriptionService
from .auth import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/schedules", tags=["Schedules"])


# Request Models
class ScheduleCreate(BaseModel):
    project_id: str
    frequency: str = "weekly"  # daily, weekly, biweekly, monthly
    time: str = "09:00"
    day_of_week: Optional[int] = None
    day_of_month: Optional[int] = None
    email_report: bool = True
    report_recipients: Optional[List[str]] = []


class ScheduleUpdate(BaseModel):
    frequency: Optional[str] = None
    time: Optional[str] = None
    day_of_week: Optional[int] = None
    day_of_month: Optional[int] = None
    email_report: Optional[bool] = None
    report_recipients: Optional[List[str]] = None
    enabled: Optional[bool] = None


@router.get("")
async def get_schedules(user: dict = Depends(get_current_user)):
    """Get all schedules for the current user"""
    async with async_session_maker() as db:
        schedules = await ScheduleService.get_by_user(db, user["user_id"])
        
        result = []
        for schedule in schedules:
            schedule_dict = ScheduleService.to_dict(schedule)
            
            # Get project info
            project = await ProjectService.get_by_id(db, schedule.project_id)
            if project:
                schedule_dict["project"] = {
                    "project_id": project.project_id,
                    "name": project.name,
                    "brand_name": project.brand_name
                }
            
            result.append(schedule_dict)
        
        return result


@router.post("")
async def create_schedule(schedule_data: ScheduleCreate, user: dict = Depends(get_current_user)):
    """Create a new scheduled scan"""
    async with async_session_maker() as db:
        # Check subscription allows scheduled scans
        subscription = await SubscriptionService.get_by_user_id(db, user["user_id"])
        plan = subscription.plan.value if subscription else "free"
        
        if plan == "free":
            raise HTTPException(
                status_code=403,
                detail="Les scans programmés nécessitent un abonnement payant."
            )
        
        # Check project exists and belongs to user
        project = await ProjectService.get_by_id(db, schedule_data.project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Projet non trouvé")
        if project.user_id != user["user_id"]:
            raise HTTPException(status_code=403, detail="Accès non autorisé")
        
        # Check if schedule already exists for this project
        existing = await ScheduleService.get_by_project(db, schedule_data.project_id)
        if existing:
            raise HTTPException(
                status_code=400,
                detail="Un scan programmé existe déjà pour ce projet."
            )
        
        # Parse time
        hour, minute = 9, 0
        if schedule_data.time:
            try:
                parts = schedule_data.time.split(":")
                hour = int(parts[0])
                minute = int(parts[1]) if len(parts) > 1 else 0
            except (ValueError, IndexError):
                pass
        
        # Create schedule
        schedule = await ScheduleService.create(
            db,
            user_id=user["user_id"],
            project_id=schedule_data.project_id,
            frequency=schedule_data.frequency,
            time=schedule_data.time,
            day_of_week=schedule_data.day_of_week,
            day_of_month=schedule_data.day_of_month,
            hour=hour,
            minute=minute,
            email_report=schedule_data.email_report,
            send_report_email=schedule_data.email_report,
            report_recipients=schedule_data.report_recipients or []
        )
        
        return ScheduleService.to_dict(schedule)


@router.get("/{schedule_id}")
async def get_schedule(schedule_id: str, user: dict = Depends(get_current_user)):
    """Get a specific schedule"""
    async with async_session_maker() as db:
        schedule = await ScheduleService.get_by_id(db, schedule_id)
        
        if not schedule:
            raise HTTPException(status_code=404, detail="Planning non trouvé")
        
        if schedule.user_id != user["user_id"]:
            raise HTTPException(status_code=403, detail="Accès non autorisé")
        
        schedule_dict = ScheduleService.to_dict(schedule)
        
        # Get project info
        project = await ProjectService.get_by_id(db, schedule.project_id)
        if project:
            schedule_dict["project"] = {
                "project_id": project.project_id,
                "name": project.name,
                "brand_name": project.brand_name
            }
        
        return schedule_dict


@router.put("/{schedule_id}")
async def update_schedule(schedule_id: str, schedule_update: ScheduleUpdate, user: dict = Depends(get_current_user)):
    """Update a schedule"""
    async with async_session_maker() as db:
        schedule = await ScheduleService.get_by_id(db, schedule_id)
        
        if not schedule:
            raise HTTPException(status_code=404, detail="Planning non trouvé")
        
        if schedule.user_id != user["user_id"]:
            raise HTTPException(status_code=403, detail="Accès non autorisé")
        
        # Build update dict
        update_data = {}
        if schedule_update.frequency is not None:
            update_data["frequency"] = schedule_update.frequency
        if schedule_update.time is not None:
            update_data["time"] = schedule_update.time
            try:
                parts = schedule_update.time.split(":")
                update_data["hour"] = int(parts[0])
                update_data["minute"] = int(parts[1]) if len(parts) > 1 else 0
            except (ValueError, IndexError):
                pass
        if schedule_update.day_of_week is not None:
            update_data["day_of_week"] = schedule_update.day_of_week
        if schedule_update.day_of_month is not None:
            update_data["day_of_month"] = schedule_update.day_of_month
        if schedule_update.email_report is not None:
            update_data["email_report"] = schedule_update.email_report
            update_data["send_report_email"] = schedule_update.email_report
        if schedule_update.report_recipients is not None:
            update_data["report_recipients"] = schedule_update.report_recipients
        if schedule_update.enabled is not None:
            update_data["enabled"] = schedule_update.enabled
        
        if update_data:
            updated_schedule = await ScheduleService.update(db, schedule_id, **update_data)
            return ScheduleService.to_dict(updated_schedule)
        
        return ScheduleService.to_dict(schedule)


@router.delete("/{schedule_id}")
async def delete_schedule(schedule_id: str, user: dict = Depends(get_current_user)):
    """Delete a schedule"""
    async with async_session_maker() as db:
        schedule = await ScheduleService.get_by_id(db, schedule_id)
        
        if not schedule:
            raise HTTPException(status_code=404, detail="Planning non trouvé")
        
        if schedule.user_id != user["user_id"]:
            raise HTTPException(status_code=403, detail="Accès non autorisé")
        
        await ScheduleService.delete(db, schedule_id)
        
        return {"success": True, "message": "Planning supprimé"}


@router.post("/{schedule_id}/toggle")
async def toggle_schedule(schedule_id: str, user: dict = Depends(get_current_user)):
    """Toggle schedule enabled/disabled"""
    async with async_session_maker() as db:
        schedule = await ScheduleService.get_by_id(db, schedule_id)
        
        if not schedule:
            raise HTTPException(status_code=404, detail="Planning non trouvé")
        
        if schedule.user_id != user["user_id"]:
            raise HTTPException(status_code=403, detail="Accès non autorisé")
        
        new_enabled = not schedule.enabled
        await ScheduleService.update(db, schedule_id, enabled=new_enabled)
        
        return {"success": True, "enabled": new_enabled}
