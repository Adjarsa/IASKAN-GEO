"""
Visibility Router - GEO Visibility Tracking
Migrated from server.py for better code organization
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from typing import Dict, Any
import logging

from ..db.database import async_session_maker
from ..db.models import Project, Analysis, AnalysisStatus
from ..routers.auth import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["visibility"])


@router.get("/visibility/{project_id}")
async def get_visibility_data(project_id: str, user: dict = Depends(get_current_user)) -> Dict[str, Any]:
    """Get visibility tracking data for a project"""
    try:
        async with async_session_maker() as session:
            # Verify project belongs to user
            project_result = await session.execute(
                select(Project).where(
                    Project.project_id == project_id,
                    Project.user_id == user["user_id"]
                )
            )
            project = project_result.scalar_one_or_none()
            
            if not project:
                raise HTTPException(status_code=404, detail="Projet non trouvé")
            
            # Get latest completed analysis
            analysis_result = await session.execute(
                select(Analysis).where(
                    Analysis.project_id == project_id,
                    Analysis.status == AnalysisStatus.COMPLETED
                ).order_by(Analysis.created_at.desc()).limit(1)
            )
            latest_analysis = analysis_result.scalar_one_or_none()
            
            if not latest_analysis:
                return _get_empty_visibility_data()
            
            # Parse analysis results
            ai_scores = latest_analysis.ai_scores or {}
            query_scores = latest_analysis.query_scores or []
            
            # Build AI engines data
            ai_engines = {}
            for ai_name, score in ai_scores.items():
                ai_engines[ai_name] = {
                    "score": round(score) if isinstance(score, (int, float)) else 0,
                    "position_avg": 3.0,
                    "mention_rate": 50,
                    "trend": "stable"
                }
            
            # Position distribution
            positions = _calculate_position_distribution(query_scores)
            
            return {
                "global_visibility_score": round(latest_analysis.global_score or 0),
                "ai_engines": ai_engines,
                "position_distribution": positions,
                "thematic_visibility": [],
                "recent_queries": [],
                "has_data": True
            }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting visibility data: {e}")
        return _get_empty_visibility_data()


def _get_empty_visibility_data() -> Dict[str, Any]:
    """Return empty visibility data structure"""
    return {
        "global_visibility_score": 0,
        "ai_engines": {},
        "position_distribution": {"first": 0, "second": 0, "third": 0, "other": 0, "absent": 100},
        "thematic_visibility": [],
        "recent_queries": [],
        "has_data": False
    }


def _calculate_position_distribution(query_scores: list) -> Dict[str, int]:
    """Calculate position distribution from query scores"""
    positions = {"first": 0, "second": 0, "third": 0, "other": 0, "absent": 0}
    
    for query in query_scores:
        for resp in query.get("responses", []):
            if not resp.get("brand_mentioned"):
                positions["absent"] += 1
            else:
                pos_ratio = resp.get("position_ratio", 1)
                if pos_ratio < 0.15:
                    positions["first"] += 1
                elif pos_ratio < 0.30:
                    positions["second"] += 1
                elif pos_ratio < 0.50:
                    positions["third"] += 1
                else:
                    positions["other"] += 1
    
    total_responses = sum(positions.values())
    if total_responses > 0:
        for key in positions:
            positions[key] = round(positions[key] / total_responses * 100)
    
    return positions
