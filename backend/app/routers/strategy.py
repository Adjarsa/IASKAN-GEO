"""
GEO Strategy Router
API endpoints for generating optimization strategies
"""
from fastapi import APIRouter, HTTPException, Request, Depends
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import logging

from ..engines.strategy.geo_strategy import GEOStrategyEngine
from ..db.database import async_session_maker
from ..db.services import UserService, SessionService, AnalysisService, SubscriptionService
from ..db.models import SubscriptionPlan

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
