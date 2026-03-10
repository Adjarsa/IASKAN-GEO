"""
Projects Router - PostgreSQL Version
Handles project CRUD operations
"""
from fastapi import APIRouter, HTTPException, Request, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from datetime import datetime, timezone
from pydantic import BaseModel
import httpx
import logging

from ..db.database import async_session_maker
from ..db.services import ProjectService, AnalysisService, SubscriptionService
from .auth import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/projects", tags=["Projects"])


# Request Models
class ProjectCreate(BaseModel):
    name: str
    website_url: str
    brand_name: str
    competitors: Optional[List[str]] = []
    keywords: Optional[List[str]] = []


class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    website_url: Optional[str] = None
    brand_name: Optional[str] = None
    competitors: Optional[List[str]] = None
    keywords: Optional[List[str]] = None


# Helper Functions
async def get_favicon_url(website_url: str) -> Optional[str]:
    """Try to get favicon URL from a website"""
    try:
        if not website_url.startswith(('http://', 'https://')):
            website_url = f"https://{website_url}"
        
        from urllib.parse import urlparse
        parsed = urlparse(website_url)
        domain = parsed.netloc or parsed.path.split('/')[0]
        
        # Use Google's favicon service (most reliable)
        return f"https://www.google.com/s2/favicons?domain={domain}&sz=128"
    except Exception as e:
        logger.warning(f"Error getting favicon: {e}")
        return None


# Routes
@router.post("")
async def create_project(project: ProjectCreate, user: dict = Depends(get_current_user)):
    """Create a new project"""
    async with async_session_maker() as db:
        # Check project limit
        project_count = await ProjectService.count_by_user(db, user["user_id"])
        subscription = await SubscriptionService.get_by_user_id(db, user["user_id"])
        
        plan = subscription.plan.value if subscription else "free"
        from ..core.config import SUBSCRIPTION_PLANS
        plan_limits = SUBSCRIPTION_PLANS.get(plan, SUBSCRIPTION_PLANS["free"])
        projects_limit = plan_limits.get("projects_limit", 1)
        
        if projects_limit != -1 and project_count >= projects_limit:
            raise HTTPException(
                status_code=403,
                detail=f"Limite de projets atteinte ({projects_limit}). Passez à un plan supérieur."
            )
        
        # Get favicon
        logo_url = await get_favicon_url(project.website_url)
        
        # Create project
        new_project = await ProjectService.create(
            db,
            user_id=user["user_id"],
            name=project.name,
            website_url=project.website_url,
            brand_name=project.brand_name,
            competitors=project.competitors,
            keywords=project.keywords,
            logo_url=logo_url
        )
        
        return ProjectService.to_dict(new_project)


@router.get("")
async def list_projects(user: dict = Depends(get_current_user)):
    """List all projects for the current user"""
    async with async_session_maker() as db:
        projects = await ProjectService.get_by_user(db, user["user_id"])
        
        result = []
        for project in projects:
            project_dict = ProjectService.to_dict(project)
            
            # Get latest analysis
            latest_analysis = await AnalysisService.get_latest_by_project(db, project.project_id)
            if latest_analysis:
                project_dict["latest_analysis"] = AnalysisService.to_dict(latest_analysis)
            else:
                project_dict["latest_analysis"] = None
            
            result.append(project_dict)
        
        return result


@router.get("/{project_id}")
async def get_project(project_id: str, user: dict = Depends(get_current_user)):
    """Get a specific project"""
    async with async_session_maker() as db:
        project = await ProjectService.get_by_id(db, project_id)
        
        if not project:
            raise HTTPException(status_code=404, detail="Projet non trouvé")
        
        if project.user_id != user["user_id"]:
            raise HTTPException(status_code=403, detail="Accès non autorisé")
        
        project_dict = ProjectService.to_dict(project)
        
        # Get latest analysis
        latest_analysis = await AnalysisService.get_latest_by_project(db, project_id)
        project_dict["latest_analysis"] = AnalysisService.to_dict(latest_analysis) if latest_analysis else None
        
        return project_dict


@router.put("/{project_id}")
async def update_project(project_id: str, project_update: ProjectUpdate, user: dict = Depends(get_current_user)):
    """Update a project"""
    async with async_session_maker() as db:
        project = await ProjectService.get_by_id(db, project_id)
        
        if not project:
            raise HTTPException(status_code=404, detail="Projet non trouvé")
        
        if project.user_id != user["user_id"]:
            raise HTTPException(status_code=403, detail="Accès non autorisé")
        
        # Build update dict
        update_data = {}
        if project_update.name is not None:
            update_data["name"] = project_update.name
        if project_update.website_url is not None:
            update_data["website_url"] = project_update.website_url
            update_data["logo_url"] = await get_favicon_url(project_update.website_url)
        if project_update.brand_name is not None:
            update_data["brand_name"] = project_update.brand_name
        if project_update.competitors is not None:
            update_data["competitors"] = project_update.competitors
        if project_update.keywords is not None:
            update_data["keywords"] = project_update.keywords
        
        if update_data:
            updated_project = await ProjectService.update(db, project_id, **update_data)
            return ProjectService.to_dict(updated_project)
        
        return ProjectService.to_dict(project)


@router.delete("/{project_id}")
async def delete_project(project_id: str, user: dict = Depends(get_current_user)):
    """Delete a project"""
    async with async_session_maker() as db:
        project = await ProjectService.get_by_id(db, project_id)
        
        if not project:
            raise HTTPException(status_code=404, detail="Projet non trouvé")
        
        if project.user_id != user["user_id"]:
            raise HTTPException(status_code=403, detail="Accès non autorisé")
        
        await ProjectService.delete(db, project_id)
        
        return {"success": True, "message": "Projet supprimé"}


@router.get("/{project_id}/stats")
async def get_project_stats(project_id: str, user: dict = Depends(get_current_user)):
    """Get project statistics"""
    async with async_session_maker() as db:
        project = await ProjectService.get_by_id(db, project_id)
        
        if not project:
            raise HTTPException(status_code=404, detail="Projet non trouvé")
        
        if project.user_id != user["user_id"]:
            raise HTTPException(status_code=403, detail="Accès non autorisé")
        
        # Get analyses
        analyses = await AnalysisService.get_by_project(db, project_id, limit=30)
        
        # Calculate stats
        total_analyses = len(analyses)
        completed_analyses = [a for a in analyses if a.status.value == "completed"]
        
        if completed_analyses:
            latest = completed_analyses[0]
            avg_score = sum(a.global_score or 0 for a in completed_analyses) / len(completed_analyses)
            best_score = max(a.global_score or 0 for a in completed_analyses)
        else:
            latest = None
            avg_score = 0
            best_score = 0
        
        return {
            "project_id": project_id,
            "total_analyses": total_analyses,
            "completed_analyses": len(completed_analyses),
            "average_score": round(avg_score, 1),
            "best_score": round(best_score, 1),
            "latest_analysis": AnalysisService.to_dict(latest) if latest else None
        }
