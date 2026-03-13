"""
GEO Strategy Router
API endpoints for generating optimization strategies
"""
from fastapi import APIRouter, HTTPException, Request, Depends
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone
from sqlalchemy import select, func, update
import logging

from ..engines.strategy.geo_strategy import GEOStrategyEngine
from ..db.database import async_session_maker
from ..db.services import UserService, SessionService, AnalysisService, SubscriptionService
from ..db.models import SubscriptionPlan, ImplementationProgress

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/strategy", tags=["Strategy"])

# Initialize engine
strategy_engine = GEOStrategyEngine()


# ================== HELPER FUNCTIONS ==================

async def get_current_user(request: Request) -> dict:
    """Get current authenticated user"""
    token = request.cookies.get("session_token")
    if not token:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
    
    if not token:
        raise HTTPException(status_code=401, detail="Non authentifié")
    
    async with async_session_maker() as db:
        session = await SessionService.get_by_token(db, token)
        if not session:
            raise HTTPException(status_code=401, detail="Session expirée")
        
        user = await UserService.get_by_user_id(db, session.user_id)
        if not user:
            raise HTTPException(status_code=401, detail="Utilisateur non trouvé")
        
        return UserService.to_dict(user)


# ================== REQUEST MODELS ==================

class StrategyFromScoresRequest(BaseModel):
    global_score: float
    relevance: Optional[float] = None
    authority: Optional[float] = None
    thoroughness: Optional[float] = None
    engagement: Optional[float] = None
    diagnostics: Optional[Dict[str, Any]] = None


class StrategyFromAnalysisRequest(BaseModel):
    analysis_id: str


# ================== ENDPOINTS ==================

@router.post("/generate")
async def generate_strategy_from_scores(
    request_data: StrategyFromScoresRequest,
    user: dict = Depends(get_current_user)
):
    """
    Generate GEO optimization strategy from scores.
    Returns prioritized recommendations and action plan.
    """
    try:
        result = strategy_engine.generate_from_scores(
            global_score=request_data.global_score,
            relevance=request_data.relevance,
            authority=request_data.authority,
            thoroughness=request_data.thoroughness,
            engagement=request_data.engagement,
            diagnostics=request_data.diagnostics or {}
        )
        
        if not result.get("success"):
            raise HTTPException(status_code=500, detail=result.get("error", "Erreur de génération"))
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Strategy generation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/from-analysis")
async def generate_strategy_from_analysis(
    request_data: StrategyFromAnalysisRequest,
    user: dict = Depends(get_current_user)
):
    """
    Generate GEO strategy from an existing analysis.
    """
    try:
        async with async_session_maker() as db:
            # Get the analysis
            analysis = await AnalysisService.get_by_id(db, request_data.analysis_id)
            
            if not analysis:
                raise HTTPException(status_code=404, detail="Analyse non trouvée")
            
            # Check ownership
            if analysis.user_id != user["user_id"]:
                raise HTTPException(status_code=403, detail="Accès non autorisé")
            
            # Build analysis result dict
            analysis_result = {
                "global_score": analysis.global_score or 0,
                "grade": analysis.grade,
                "rate_scores": analysis.rate_scores or {},
                "diagnostics": analysis.diagnostics or {},
                "visibility_score": analysis.visibility_score,
                "citation_rate": analysis.citation_rate
            }
            
            # Generate strategy
            result = strategy_engine.generate_strategy(analysis_result)
            
            if not result.get("success"):
                raise HTTPException(status_code=500, detail=result.get("error", "Erreur de génération"))
            
            return result
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Strategy from analysis error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/recommendations/{category}")
async def get_recommendations_by_category(
    category: str,
    user: dict = Depends(get_current_user)
):
    """
    Get all available recommendations for a specific category.
    Categories: content, authority, technical, engagement
    """
    valid_categories = ["content", "authority", "technical", "engagement"]
    
    if category not in valid_categories:
        raise HTTPException(
            status_code=400, 
            detail=f"Catégorie invalide. Choisir parmi: {', '.join(valid_categories)}"
        )
    
    recommendations = strategy_engine.recommendations_db.get(category, {})
    
    return {
        "category": category,
        "recommendations": [
            {
                "id": key,
                **value
            }
            for key, value in recommendations.items()
        ]
    }


@router.get("/quick-analysis")
async def quick_strategy_analysis(
    score: int,
    user: dict = Depends(get_current_user)
):
    """
    Quick strategy based on a single score.
    Useful for getting immediate recommendations.
    """
    if score < 0 or score > 100:
        raise HTTPException(status_code=400, detail="Score doit être entre 0 et 100")
    
    result = strategy_engine.generate_from_scores(
        global_score=score,
        diagnostics={
            "has_faq": score > 60,
            "has_author": score > 50,
            "has_schema": score > 70,
            "has_sources": score > 55,
            "structure_score": score * 0.9
        }
    )
    
    return result


@router.get("/templates")
async def get_strategy_templates(
    user: dict = Depends(get_current_user)
):
    """
    Get all available strategy templates and recommendations.
    """
    return {
        "categories": {
            "content": {
                "name": "Contenu",
                "description": "Optimisation du contenu pour les LLMs",
                "icon": "file-text",
                "count": len(strategy_engine.CONTENT_RECOMMENDATIONS)
            },
            "authority": {
                "name": "Autorité",
                "description": "Signaux de confiance et d'expertise",
                "icon": "shield",
                "count": len(strategy_engine.AUTHORITY_RECOMMENDATIONS)
            },
            "technical": {
                "name": "Technique",
                "description": "Optimisations techniques et schema",
                "icon": "code",
                "count": len(strategy_engine.TECHNICAL_RECOMMENDATIONS)
            },
            "engagement": {
                "name": "Engagement",
                "description": "Interaction et signaux utilisateur",
                "icon": "users",
                "count": len(strategy_engine.ENGAGEMENT_RECOMMENDATIONS)
            }
        },
        "priority_levels": ["critical", "high", "medium", "low"],
        "impact_levels": ["high", "medium", "low"],
        "effort_levels": ["low", "medium", "high"]
    }


# ================== AUTOMATIC OBJECTIVES ==================

@router.get("/objective/{score}")
async def get_automatic_objective(
    score: int,
    target_grade: Optional[str] = None,
    user: dict = Depends(get_current_user)
):
    """
    Get automatic objective to reach the next grade.
    """
    if score < 0 or score > 100:
        raise HTTPException(status_code=400, detail="Score doit être entre 0 et 100")
    
    if target_grade and target_grade not in ["A", "B", "C", "D"]:
        raise HTTPException(status_code=400, detail="Grade invalide (A, B, C ou D)")
    
    objective = strategy_engine.generate_grade_objective(
        current_score=score,
        target_grade=target_grade
    )
    
    return objective


@router.get("/objective/from-analysis/{analysis_id}")
async def get_objective_from_analysis(
    analysis_id: str,
    target_grade: Optional[str] = None,
    user: dict = Depends(get_current_user)
):
    """
    Get automatic objective based on an existing analysis.
    """
    async with async_session_maker() as db:
        analysis = await AnalysisService.get_by_id(db, analysis_id)
        
        if not analysis:
            raise HTTPException(status_code=404, detail="Analyse non trouvée")
        
        if analysis.user_id != user["user_id"]:
            raise HTTPException(status_code=403, detail="Accès non autorisé")
        
        current_score = analysis.global_score or 50
        
        # Generate recommendations first
        analysis_result = {
            "global_score": current_score,
            "grade": analysis.grade,
            "rate_scores": analysis.rate_scores or {},
            "diagnostics": analysis.diagnostics or {}
        }
        
        strategy_result = strategy_engine.generate_strategy(analysis_result)
        recommendations = strategy_result.get("strategy", {}).get("recommendations", [])
        
        # Generate objective
        objective = strategy_engine.generate_grade_objective(
            current_score=current_score,
            target_grade=target_grade,
            recommendations=recommendations
        )
        
        return {
            "analysis_id": analysis_id,
            **objective
        }


@router.get("/paths/{score}")
async def get_all_improvement_paths(
    score: int,
    user: dict = Depends(get_current_user)
):
    """
    Get all possible improvement paths to different grades.
    """
    if score < 0 or score > 100:
        raise HTTPException(status_code=400, detail="Score doit être entre 0 et 100")
    
    return strategy_engine.get_all_grade_paths(score)


# ================== IMPLEMENTATION TRACKING ==================

class ImplementationStatusUpdate(BaseModel):
    status: str  # pending, in_progress, completed, skipped
    notes: Optional[str] = None
    final_score: Optional[float] = None


@router.post("/progress/{project_id}/track")
async def track_recommendation(
    project_id: str,
    request: Request,
    user: dict = Depends(get_current_user)
):
    """
    Add a recommendation to the implementation tracking.
    """
    body = await request.json()
    recommendation_id = body.get("recommendation_id")
    category = body.get("category")
    title = body.get("title")
    priority = body.get("priority", "medium")
    initial_score = body.get("initial_score")
    
    if not all([recommendation_id, category, title]):
        raise HTTPException(status_code=400, detail="recommendation_id, category et title requis")
    
    async with async_session_maker() as db:
        # Check if already tracked
        existing = await db.execute(
            select(ImplementationProgress).where(
                ImplementationProgress.project_id == project_id,
                ImplementationProgress.recommendation_id == recommendation_id
            )
        )
        if existing.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Recommandation déjà trackée")
        
        # Create tracking entry
        progress = ImplementationProgress(
            project_id=project_id,
            user_id=user["user_id"],
            recommendation_id=recommendation_id,
            category=category,
            title=title,
            priority=priority,
            initial_score=initial_score,
            status="pending"
        )
        db.add(progress)
        await db.commit()
        await db.refresh(progress)
        
        return {
            "success": True,
            "progress_id": progress.progress_id,
            "message": "Recommandation ajoutée au suivi"
        }


@router.put("/progress/{progress_id}/status")
async def update_implementation_status(
    progress_id: str,
    status_update: ImplementationStatusUpdate,
    user: dict = Depends(get_current_user)
):
    """
    Update the status of a tracked recommendation.
    """
    if status_update.status not in ["pending", "in_progress", "completed", "skipped"]:
        raise HTTPException(status_code=400, detail="Status invalide")
    
    async with async_session_maker() as db:
        result = await db.execute(
            select(ImplementationProgress).where(
                ImplementationProgress.progress_id == progress_id,
                ImplementationProgress.user_id == user["user_id"]
            )
        )
        progress = result.scalar_one_or_none()
        
        if not progress:
            raise HTTPException(status_code=404, detail="Progression non trouvée")
        
        # Update fields
        progress.status = status_update.status
        if status_update.notes:
            progress.notes = status_update.notes
        if status_update.final_score is not None:
            progress.final_score = status_update.final_score
        if status_update.status == "completed":
            progress.completed_at = datetime.now(timezone.utc)
        
        await db.commit()
        
        return {"success": True, "message": f"Status mis à jour: {status_update.status}"}


@router.get("/progress/{project_id}")
async def get_project_progress(
    project_id: str,
    user: dict = Depends(get_current_user)
):
    """
    Get implementation progress for a project.
    """
    async with async_session_maker() as db:
        result = await db.execute(
            select(ImplementationProgress).where(
                ImplementationProgress.project_id == project_id,
                ImplementationProgress.user_id == user["user_id"]
            ).order_by(ImplementationProgress.created_at.desc())
        )
        items = result.scalars().all()
        
        # Calculate stats
        total = len(items)
        completed = sum(1 for i in items if i.status == "completed")
        in_progress = sum(1 for i in items if i.status == "in_progress")
        skipped = sum(1 for i in items if i.status == "skipped")
        
        # Score improvement
        score_improvements = [
            (i.final_score - i.initial_score) 
            for i in items 
            if i.status == "completed" and i.final_score and i.initial_score
        ]
        total_improvement = sum(score_improvements) if score_improvements else 0
        
        # Category breakdown
        categories = {}
        for item in items:
            if item.category not in categories:
                categories[item.category] = {"total": 0, "completed": 0}
            categories[item.category]["total"] += 1
            if item.status == "completed":
                categories[item.category]["completed"] += 1
        
        return {
            "project_id": project_id,
            "stats": {
                "total": total,
                "completed": completed,
                "in_progress": in_progress,
                "skipped": skipped,
                "pending": total - completed - in_progress - skipped,
                "completion_rate": round(completed / max(total, 1) * 100, 1),
                "total_score_improvement": round(total_improvement, 1)
            },
            "categories": categories,
            "items": [
                {
                    "progress_id": i.progress_id,
                    "recommendation_id": i.recommendation_id,
                    "category": i.category,
                    "title": i.title,
                    "status": i.status,
                    "priority": i.priority,
                    "initial_score": i.initial_score,
                    "final_score": i.final_score,
                    "notes": i.notes,
                    "completed_at": i.completed_at.isoformat() if i.completed_at else None,
                    "created_at": i.created_at.isoformat() if i.created_at else None
                }
                for i in items
            ]
        }


@router.delete("/progress/{progress_id}")
async def delete_progress_item(
    progress_id: str,
    user: dict = Depends(get_current_user)
):
    """
    Remove a recommendation from tracking.
    """
    async with async_session_maker() as db:
        result = await db.execute(
            select(ImplementationProgress).where(
                ImplementationProgress.progress_id == progress_id,
                ImplementationProgress.user_id == user["user_id"]
            )
        )
        progress = result.scalar_one_or_none()
        
        if not progress:
            raise HTTPException(status_code=404, detail="Progression non trouvée")
        
        await db.delete(progress)
        await db.commit()
        
        return {"success": True, "message": "Recommandation retirée du suivi"}


@router.post("/progress/{project_id}/bulk-track")
async def bulk_track_recommendations(
    project_id: str,
    request: Request,
    user: dict = Depends(get_current_user)
):
    """
    Track multiple recommendations at once from a strategy.
    """
    body = await request.json()
    recommendations = body.get("recommendations", [])
    
    if not recommendations:
        raise HTTPException(status_code=400, detail="Aucune recommandation fournie")
    
    async with async_session_maker() as db:
        added = 0
        skipped = 0
        
        for rec in recommendations:
            # Check if already tracked
            existing = await db.execute(
                select(ImplementationProgress).where(
                    ImplementationProgress.project_id == project_id,
                    ImplementationProgress.recommendation_id == rec.get("recommendation_id", rec.get("title", ""))
                )
            )
            if existing.scalar_one_or_none():
                skipped += 1
                continue
            
            # Create tracking entry
            progress = ImplementationProgress(
                project_id=project_id,
                user_id=user["user_id"],
                recommendation_id=rec.get("recommendation_id", rec.get("title", "")),
                category=rec.get("category", "content"),
                title=rec.get("title", ""),
                priority=rec.get("priority", "medium"),
                initial_score=rec.get("current_score"),
                status="pending"
            )
            db.add(progress)
            added += 1
        
        await db.commit()
        
        return {
            "success": True,
            "added": added,
            "skipped": skipped,
            "message": f"{added} recommandations ajoutées au suivi"
        }
