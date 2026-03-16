"""
Analysis Router - Celery-powered Analysis Pipeline
Handles GEO analysis operations using distributed tasks
"""
from fastapi import APIRouter, HTTPException, Request, Depends, BackgroundTasks
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, timezone
import logging

from ..db.database import async_session_maker
from ..db.services import ProjectService, AnalysisService, SubscriptionService
from ..db.models import AnalysisStatus
from ..core.config import SUBSCRIPTION_PLANS
from .auth import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/analysis", tags=["Analysis"])


class AnalysisRequest(BaseModel):
    project_id: str
    queries: Optional[List[str]] = None


@router.post("/start")
async def start_analysis(request: AnalysisRequest, user: dict = Depends(get_current_user)):
    """
    Start a new GEO analysis for a project
    Uses Celery for distributed processing
    """
    async with async_session_maker() as db:
        # Check project exists and belongs to user
        project = await ProjectService.get_by_id(db, request.project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Projet non trouvé")
        if project.user_id != user["user_id"]:
            raise HTTPException(status_code=403, detail="Accès non autorisé")
        
        # Check subscription limits
        subscription = await SubscriptionService.get_by_user_id(db, user["user_id"])
        plan = subscription.plan.value if subscription else "free"
        plan_config = SUBSCRIPTION_PLANS.get(plan, SUBSCRIPTION_PLANS["free"])
        
        scans_limit = plan_config.get("scans_limit", 1)
        scans_used = subscription.scans_used or 0 if subscription else 0
        free_remaining = subscription.free_scans_remaining or 0 if subscription else 0
        
        # Check if user can run analysis
        can_scan = False
        use_free_scan = False
        
        if scans_limit == -1:  # Unlimited
            can_scan = True
        elif scans_used < scans_limit:
            can_scan = True
        elif free_remaining > 0:
            can_scan = True
            use_free_scan = True
        
        if not can_scan:
            raise HTTPException(
                status_code=403,
                detail={
                    "error": "scan_limit_reached",
                    "message": f"Limite de scans atteinte ({scans_limit}/mois). Passez à un plan supérieur.",
                    "scans_used": scans_used,
                    "scans_limit": scans_limit
                }
            )
        
        # Create analysis record
        analysis = await AnalysisService.create(
            db,
            project_id=request.project_id,
            user_id=user["user_id"]
        )
        
        # Update subscription usage
        if use_free_scan:
            await SubscriptionService.update(
                db, user["user_id"],
                free_scans_remaining=free_remaining - 1
            )
        
        # Queue the Celery task
        from ..tasks.analysis_tasks import run_full_analysis
        task = run_full_analysis.delay(
            analysis.analysis_id,
            request.project_id,
            user["user_id"]
        )
        
        logger.info(f"Analysis {analysis.analysis_id} queued as task {task.id}")
        
        return {
            "analysis_id": analysis.analysis_id,
            "task_id": task.id,
            "status": "queued",
            "message": "Analyse démarrée. Vous serez notifié une fois terminée."
        }


@router.get("/status/{analysis_id}")
async def get_analysis_status(analysis_id: str, user: dict = Depends(get_current_user)):
    """Get the status of an analysis"""
    async with async_session_maker() as db:
        analysis = await AnalysisService.get_by_id(db, analysis_id)
        
        if not analysis:
            raise HTTPException(status_code=404, detail="Analyse non trouvée")
        
        if analysis.user_id != user["user_id"]:
            raise HTTPException(status_code=403, detail="Accès non autorisé")
        
        return {
            "analysis_id": analysis.analysis_id,
            "status": analysis.status.value,
            "global_score": analysis.global_score,
            "grade": analysis.grade,
            "error_message": analysis.error_message,
            "started_at": analysis.started_at.isoformat() if analysis.started_at else None,
            "completed_at": analysis.completed_at.isoformat() if analysis.completed_at else None,
            "created_at": analysis.created_at.isoformat() if analysis.created_at else None
        }


@router.get("/results/{analysis_id}")
async def get_analysis_results(analysis_id: str, user: dict = Depends(get_current_user)):
    """Get the full results of a completed analysis"""
    async with async_session_maker() as db:
        analysis = await AnalysisService.get_by_id(db, analysis_id)
        
        if not analysis:
            raise HTTPException(status_code=404, detail="Analyse non trouvée")
        
        if analysis.user_id != user["user_id"]:
            raise HTTPException(status_code=403, detail="Accès non autorisé")
        
        if analysis.status != AnalysisStatus.COMPLETED:
            return {
                "analysis_id": analysis.analysis_id,
                "status": analysis.status.value,
                "message": "Analyse en cours ou échouée",
                "error_message": analysis.error_message
            }
        
        return AnalysisService.to_dict(analysis)


@router.get("/history/{project_id}")
async def get_analysis_history(project_id: str, user: dict = Depends(get_current_user), limit: int = 10):
    """Get analysis history for a project"""
    async with async_session_maker() as db:
        # Verify project access
        project = await ProjectService.get_by_id(db, project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Projet non trouvé")
        if project.user_id != user["user_id"]:
            raise HTTPException(status_code=403, detail="Accès non autorisé")
        
        # Get analyses
        analyses = await AnalysisService.get_by_project(db, project_id, limit=limit)
        
        return [
            {
                "analysis_id": a.analysis_id,
                "status": a.status.value,
                "global_score": a.global_score,
                "grade": a.grade,
                "created_at": a.created_at.isoformat() if a.created_at else None,
                "completed_at": a.completed_at.isoformat() if a.completed_at else None
            }
            for a in analyses
        ]


@router.post("/cancel/{analysis_id}")
async def cancel_analysis(analysis_id: str, user: dict = Depends(get_current_user)):
    """Cancel a running analysis"""
    async with async_session_maker() as db:
        analysis = await AnalysisService.get_by_id(db, analysis_id)
        
        if not analysis:
            raise HTTPException(status_code=404, detail="Analyse non trouvée")
        
        if analysis.user_id != user["user_id"]:
            raise HTTPException(status_code=403, detail="Accès non autorisé")
        
        if analysis.status not in [AnalysisStatus.PENDING, AnalysisStatus.RUNNING]:
            raise HTTPException(status_code=400, detail="Cette analyse ne peut pas être annulée")
        
        # Update status
        await AnalysisService.update(
            db, analysis_id,
            status=AnalysisStatus.FAILED,
            error_message="Annulée par l'utilisateur",
            completed_at=datetime.now(timezone.utc)
        )
        
        # Note: In production, you'd also want to revoke the Celery task
        # from ..celery_config import celery_app
        # celery_app.control.revoke(task_id, terminate=True)
        
        return {"success": True, "message": "Analyse annulée"}


@router.get("/quota")
async def get_analysis_quota(user: dict = Depends(get_current_user)):
    """Get user's analysis quota information"""
    async with async_session_maker() as db:
        subscription = await SubscriptionService.get_by_user_id(db, user["user_id"])
        
        plan = subscription.plan.value if subscription else "free"
        plan_config = SUBSCRIPTION_PLANS.get(plan, SUBSCRIPTION_PLANS["free"])
        
        scans_limit = plan_config.get("scans_limit", 1)
        scans_used = subscription.scans_used or 0 if subscription else 0
        free_remaining = subscription.free_scans_remaining or 0 if subscription else 1
        
        return {
            "plan": plan,
            "scans_limit": scans_limit,
            "scans_used": scans_used,
            "scans_remaining": scans_limit - scans_used if scans_limit != -1 else -1,
            "free_scans_remaining": free_remaining,
            "unlimited": scans_limit == -1
        }


# ================== FRONTEND COMPATIBILITY ENDPOINTS ==================
# These endpoints match the frontend's expected API structure

@router.get("/{analysis_id}", name="get_analysis_detail")
async def get_analysis_detail(analysis_id: str, user: dict = Depends(get_current_user)):
    """
    Get full analysis details by ID
    Frontend compatibility endpoint for: GET /api/analysis/{analysis_id}
    """
    async with async_session_maker() as db:
        analysis = await AnalysisService.get_by_id(db, analysis_id)
        
        if not analysis:
            raise HTTPException(status_code=404, detail="Analyse non trouvée")
        
        if analysis.user_id != user["user_id"]:
            raise HTTPException(status_code=403, detail="Accès non autorisé")
        
        # Return full analysis data matching frontend expectations
        # Note: Using getattr for optional fields that may not exist in the model
        competitor_analysis = analysis.competitor_analysis or {}
        
        return {
            "analysis": {
                "analysis_id": analysis.analysis_id,
                "project_id": analysis.project_id,
                "user_id": analysis.user_id,
                "status": analysis.status.value if analysis.status else "pending",
                "global_score": analysis.global_score,
                "grade": analysis.grade,
                "ai_scores": analysis.ai_scores or {},
                "rate_scores": analysis.rate_scores or {},
                "query_scores": analysis.query_scores or [],
                "competitor_comparison": competitor_analysis.get("discovered", []) if isinstance(competitor_analysis, dict) else [],
                "recommendations": analysis.recommendations or [],
                "total_queries": analysis.total_queries or 0,
                "queries_processed": analysis.queries_processed or 0,
                "current_phase": analysis.current_phase or "pending",
                "queries_with_mention": analysis.queries_with_mention or 0,
                "mention_rate": analysis.mention_rate,
                "average_position": analysis.average_position,
                "stability_score": analysis.stability_score,
                "ai_engines_used": analysis.ai_engines_used or [],
                "competitor_analysis": competitor_analysis,
                "error_message": analysis.error_message,
                "started_at": analysis.started_at.isoformat() if analysis.started_at else None,
                "completed_at": analysis.completed_at.isoformat() if analysis.completed_at else None,
                "created_at": analysis.created_at.isoformat() if analysis.created_at else None
            }
        }
