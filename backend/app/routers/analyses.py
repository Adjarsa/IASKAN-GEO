"""
Analyses Router - PostgreSQL Version
Handles listing analyses (plural endpoint for frontend compatibility)
"""
from fastapi import APIRouter, HTTPException, Depends
from typing import Optional, List
import logging

from ..db.database import async_session_maker
from ..db.services import AnalysisService, ProjectService
from .auth import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/analyses", tags=["Analyses"])


@router.get("")
async def get_analyses_list(
    project_id: Optional[str] = None,
    limit: int = 50,
    user: dict = Depends(get_current_user)
):
    """
    Get all analyses for user or filtered by project
    Frontend compatibility endpoint for: GET /api/analyses?project_id=...
    """
    async with async_session_maker() as db:
        if project_id:
            # Verify project access
            project = await ProjectService.get_by_id(db, project_id)
            if not project:
                raise HTTPException(status_code=404, detail="Projet non trouvé")
            if project.user_id != user["user_id"]:
                raise HTTPException(status_code=403, detail="Accès non autorisé")
            
            # Get analyses for this project
            analyses = await AnalysisService.get_by_project(db, project_id, limit=limit)
        else:
            # Get all analyses for user
            analyses = await AnalysisService.get_by_user(db, user["user_id"], limit=limit)
        
        return {
            "analyses": [
                {
                    "analysis_id": a.analysis_id,
                    "project_id": a.project_id,
                    "status": a.status.value,
                    "global_score": a.global_score,
                    "grade": a.grade,
                    "ai_scores": a.ai_scores or {},
                    "rate_score": a.rate_scores or {},
                    "total_queries": a.total_queries,
                    "mention_rate": a.mention_rate,
                    "ai_engines_used": a.ai_engines_used or [],
                    "error_message": a.error_message,
                    "started_at": a.started_at.isoformat() if a.started_at else None,
                    "completed_at": a.completed_at.isoformat() if a.completed_at else None,
                    "created_at": a.created_at.isoformat() if a.created_at else None
                }
                for a in analyses
            ]
        }


@router.get("/history/{project_id}")
async def get_analyses_history_charts(
    project_id: str,
    user: dict = Depends(get_current_user)
):
    """
    Get analysis history with trends for charts
    Returns formatted data for score evolution charts
    """
    async with async_session_maker() as db:
        # Verify project access
        project = await ProjectService.get_by_id(db, project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Projet non trouvé")
        if project.user_id != user["user_id"]:
            raise HTTPException(status_code=403, detail="Accès non autorisé")
        
        # Get completed analyses ordered by date
        from sqlalchemy import select
        from ..db.models import Analysis, AnalysisStatus
        
        result = await db.execute(
            select(Analysis)
            .where(Analysis.project_id == project_id)
            .where(Analysis.user_id == user["user_id"])
            .where(Analysis.status == AnalysisStatus.COMPLETED)
            .order_by(Analysis.created_at.asc())
            .limit(100)
        )
        analyses = result.scalars().all()
        
        # Build chart data
        history = {
            "score_evolution": [],
            "rate_evolution": [],
            "ai_evolution": {
                "chatgpt": [],
                "claude": [],
                "gemini": [],
                "perplexity": []
            },
            "summary": {
                "total_analyses": len(analyses),
                "first_analysis": analyses[0].created_at.isoformat() if analyses else None,
                "last_analysis": analyses[-1].created_at.isoformat() if analyses else None,
                "score_change": 0,
                "trend": "stable"
            }
        }
        
        for analysis in analyses:
            date_str = analysis.created_at.isoformat() if analysis.created_at else ""
            
            # Score evolution
            history["score_evolution"].append({
                "date": date_str,
                "score": round(analysis.global_score or 0, 1),
                "analysis_id": analysis.analysis_id
            })
            
            # R.A.T.E. evolution
            rate_score = analysis.rate_scores or {}
            history["rate_evolution"].append({
                "date": date_str,
                "relevance": round(rate_score.get("relevance", 0), 1),
                "authority": round(rate_score.get("authority", 0), 1),
                "truthfulness": round(rate_score.get("truthfulness", 0), 1),
                "endorsement": round(rate_score.get("endorsement", 0), 1)
            })
            
            # AI scores evolution
            ai_scores = analysis.ai_scores or {}
            for ai_type in ["chatgpt", "claude", "gemini", "perplexity"]:
                score = ai_scores.get(ai_type, 0)
                history["ai_evolution"][ai_type].append({
                    "date": date_str,
                    "score": round(score, 1) if score else 0
                })
        
        # Calculate trend
        if len(history["score_evolution"]) >= 2:
            first_score = history["score_evolution"][0]["score"]
            last_score = history["score_evolution"][-1]["score"]
            change = last_score - first_score
            history["summary"]["score_change"] = round(change, 1)
            
            if change > 5:
                history["summary"]["trend"] = "up"
            elif change < -5:
                history["summary"]["trend"] = "down"
            else:
                history["summary"]["trend"] = "stable"
        
        return history
