"""
Notifications Router - PostgreSQL Version
Handles notification CRUD operations
"""
from fastapi import APIRouter, HTTPException, Request, Depends
from typing import List, Optional
import logging

from ..db.database import async_session_maker
from ..db.services import NotificationService
from .auth import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/notifications", tags=["Notifications"])


@router.get("")
async def get_notifications(user: dict = Depends(get_current_user), unread_only: bool = False, limit: int = 50):
    """Get notifications for the current user"""
    async with async_session_maker() as db:
        notifications = await NotificationService.get_by_user(
            db, user["user_id"], unread_only=unread_only, limit=limit
        )
        
        return [NotificationService.to_dict(n) for n in notifications]


@router.get("/unread-count")
async def get_unread_count(user: dict = Depends(get_current_user)):
    """Get count of unread notifications"""
    async with async_session_maker() as db:
        count = await NotificationService.count_unread(db, user["user_id"])
        return {"unread_count": count}


@router.post("/{notification_id}/read")
async def mark_notification_read(notification_id: str, user: dict = Depends(get_current_user)):
    """Mark a notification as read"""
    async with async_session_maker() as db:
        success = await NotificationService.mark_read(db, notification_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Notification non trouvée")
        
        return {"success": True, "message": "Notification marquée comme lue"}


@router.post("/read-all")
async def mark_all_read(user: dict = Depends(get_current_user)):
    """Mark all notifications as read"""
    async with async_session_maker() as db:
        count = await NotificationService.mark_all_read(db, user["user_id"])
        return {"success": True, "marked_read": count}


@router.delete("")
async def delete_all_notifications(user: dict = Depends(get_current_user)):
    """Delete all notifications for the current user"""
    async with async_session_maker() as db:
        count = await NotificationService.delete_all(db, user["user_id"])
        return {"success": True, "message": "Toutes les notifications supprimées", "deleted": count}
