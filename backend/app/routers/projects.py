"""
Projects Router
Handles project CRUD operations
"""
from fastapi import APIRouter, HTTPException, Request, Depends
from typing import List, Optional
from datetime import datetime, timezone
from pydantic import BaseModel
import uuid
import httpx
import logging

from ..core.database import db
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
        
        # Try common favicon locations
        favicon_urls = [
            f"https://www.google.com/s2/favicons?domain={domain}&sz=128",
            f"https://{domain}/favicon.ico",
            f"https://{domain}/favicon.png"
        ]
        
        async with httpx.AsyncClient(timeout=5.0) as client:
            for url in favicon_urls:
                try:
                    response = await client.head(url)
                    if response.status_code == 200:
                        return url
                except:
                    continue
        
        # Fallback to Google's favicon service
        return f"https://www.google.com/s2/favicons?domain={domain}&sz=128"
    except Exception as e:
        logger.warning(f"Error getting favicon for {website_url}: {e}")
        return None


# Routes
@router.post("")
async def create_project(request: Request, user: dict = Depends(get_current_user)):
    """Create a new project"""
    body = await request.json()
    
    # Check project limit
    subscription = await db.subscriptions.find_one({"user_id": user["user_id"]}, {"_id": 0})
    from ..core.config import SUBSCRIPTION_PLANS
    plan_config = SUBSCRIPTION_PLANS.get(subscription.get("plan", "free"), SUBSCRIPTION_PLANS["free"])
    
    project_count = await db.projects.count_documents({"user_id": user["user_id"]})
    if plan_config["projects_limit"] != -1 and project_count >= plan_config["projects_limit"]:
        raise HTTPException(
            status_code=403, 
            detail=f"Limite de projets atteinte ({plan_config['projects_limit']}). Passez à un plan supérieur."
        )
    
    project_id = f"proj_{uuid.uuid4().hex[:12]}"
    logo_url = await get_favicon_url(body.get("website_url", ""))
    
    project = {
        "project_id": project_id,
        "user_id": user["user_id"],
        "name": body.get("name"),
        "website_url": body.get("website_url"),
        "brand_name": body.get("brand_name"),
        "logo_url": logo_url,
        "competitors": body.get("competitors", []),
        "keywords": body.get("keywords", []),
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.projects.insert_one(project)
    
    result = await db.projects.find_one({"project_id": project_id}, {"_id": 0})
    return {"project": result}


@router.get("")
async def get_projects(user: dict = Depends(get_current_user)):
    """Get all projects for user"""
    projects = await db.projects.find({"user_id": user["user_id"]}, {"_id": 0}).to_list(100)
    return {"projects": projects}


@router.get("/{project_id}")
async def get_project(project_id: str, user: dict = Depends(get_current_user)):
    """Get a specific project"""
    project = await db.projects.find_one(
        {"project_id": project_id, "user_id": user["user_id"]},
        {"_id": 0}
    )
    if not project:
        raise HTTPException(status_code=404, detail="Projet non trouvé")
    return {"project": project}


@router.put("/{project_id}")
async def update_project(project_id: str, request: Request, user: dict = Depends(get_current_user)):
    """Update a project"""
    body = await request.json()
    
    # Build update dict (only include provided fields)
    updates = {k: v for k, v in body.items() if v is not None}
    
    if updates:
        updates["updated_at"] = datetime.now(timezone.utc).isoformat()
        
        # Update logo if website changed
        if "website_url" in updates:
            updates["logo_url"] = await get_favicon_url(updates["website_url"])
        
        await db.projects.update_one(
            {"project_id": project_id, "user_id": user["user_id"]},
            {"$set": updates}
        )
    
    project = await db.projects.find_one(
        {"project_id": project_id, "user_id": user["user_id"]},
        {"_id": 0}
    )
    return {"project": project}


@router.delete("/{project_id}")
async def delete_project(project_id: str, user: dict = Depends(get_current_user)):
    """Delete a project and all associated data"""
    result = await db.projects.delete_one({"project_id": project_id, "user_id": user["user_id"]})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Projet non trouvé")
    
    # Delete associated analyses
    await db.analyses.delete_many({"project_id": project_id})
    
    # Delete associated schedules
    await db.scan_schedules.delete_many({"project_id": project_id})
    
    return {"message": "Projet supprimé"}


@router.get("/{project_id}/stats")
async def get_project_stats(project_id: str, user: dict = Depends(get_current_user)):
    """Get statistics for a project"""
    project = await db.projects.find_one(
        {"project_id": project_id, "user_id": user["user_id"]},
        {"_id": 0}
    )
    if not project:
        raise HTTPException(status_code=404, detail="Projet non trouvé")
    
    # Count analyses
    total_analyses = await db.analyses.count_documents({"project_id": project_id})
    completed_analyses = await db.analyses.count_documents({"project_id": project_id, "status": "completed"})
    
    # Get latest analysis
    latest_analysis = await db.analyses.find_one(
        {"project_id": project_id, "status": "completed"},
        {"_id": 0, "analysis_id": 1, "global_score": 1, "grade": 1, "created_at": 1},
        sort=[("created_at", -1)]
    )
    
    return {
        "project_id": project_id,
        "total_analyses": total_analyses,
        "completed_analyses": completed_analyses,
        "latest_analysis": latest_analysis
    }
