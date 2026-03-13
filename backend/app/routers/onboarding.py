"""
Onboarding Router
API endpoints for user onboarding flow
Uses PostgreSQL with SQLAlchemy
"""
from fastapi import APIRouter, HTTPException, Depends, Request
from typing import Optional, List
from datetime import datetime, timezone
from pydantic import BaseModel
import logging

from ..db.database import async_session_maker
from ..db.services import UserService, SessionService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/onboarding", tags=["Onboarding"])


# Onboarding steps definition
ONBOARDING_STEPS = [
    {
        "id": "welcome",
        "title": "Bienvenue sur IAskan",
        "description": "Découvrez comment optimiser votre visibilité dans les réponses IA",
        "order": 1
    },
    {
        "id": "create_project",
        "title": "Créer votre premier projet",
        "description": "Configurez votre marque et vos concurrents",
        "order": 2
    },
    {
        "id": "first_scan",
        "title": "Lancer votre première analyse",
        "description": "Découvrez votre visibilité actuelle dans les IA",
        "order": 3
    },
    {
        "id": "explore_results",
        "title": "Explorer les résultats",
        "description": "Comprenez vos scores et recommandations",
        "order": 4
    },
    {
        "id": "article_optimizer",
        "title": "Optimiser un article",
        "description": "Améliorez la citabilité de votre contenu",
        "order": 5
    },
    {
        "id": "completed",
        "title": "Prêt à performer",
        "description": "Vous maîtrisez maintenant IAskan!",
        "order": 6
    }
]


class OnboardingProgress(BaseModel):
    current_step: str
    completed_steps: List[str] = []
    skipped: bool = False


# Helper to get current user
async def get_current_user(request: Request) -> dict:
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


@router.get("/status")
async def get_onboarding_status(user: dict = Depends(get_current_user)):
    """Get user's onboarding progress"""
    # Check if user has completed onboarding (stored in user metadata or separate table)
    onboarding_completed = user.get("onboarding_completed", False)
    
    if onboarding_completed:
        return {
            "show_onboarding": False,
            "current_step": "completed",
            "completed_steps": [s["id"] for s in ONBOARDING_STEPS],
            "skipped": False,
            "progress_percent": 100
        }
    
    # For new users, show onboarding
    return {
        "show_onboarding": True,
        "current_step": "welcome",
        "completed_steps": [],
        "skipped": False,
        "progress_percent": 0,
        "steps": ONBOARDING_STEPS
    }


@router.post("/progress")
async def update_onboarding_progress(
    progress: OnboardingProgress,
    user: dict = Depends(get_current_user)
):
    """Update user's onboarding progress"""
    # Calculate progress
    total_steps = len(ONBOARDING_STEPS)
    completed_count = len(progress.completed_steps)
    progress_percent = int((completed_count / total_steps) * 100)
    
    # Check if completed
    is_completed = progress.current_step == "completed" or progress.skipped
    
    return {
        "success": True,
        "current_step": progress.current_step,
        "completed_steps": progress.completed_steps,
        "progress_percent": progress_percent,
        "is_completed": is_completed
    }


@router.post("/skip")
async def skip_onboarding(user: dict = Depends(get_current_user)):
    """Skip the onboarding process"""
    # Mark onboarding as skipped in user profile
    try:
        async with async_session_maker() as db:
            await UserService.update(db, user.get("user_id"), onboarding_completed=True)
    except Exception as e:
        logger.error(f"Error skipping onboarding: {e}")
    
    return {
        "success": True,
        "message": "Onboarding skipped",
        "show_onboarding": False
    }


@router.post("/complete")
async def complete_onboarding(user: dict = Depends(get_current_user)):
    """Mark onboarding as complete"""
    user_id = user.get("user_id")
    
    # Mark onboarding as completed
    # In production, update database
    try:
        async with async_session_maker() as db:
            await UserService.update(db, user_id, onboarding_completed=True)
    except Exception as e:
        logger.error(f"Error completing onboarding: {e}")
    
    return {
        "success": True,
        "message": "Onboarding completed",
        "show_onboarding": False,
        "progress_percent": 100
    }


@router.get("/steps")
async def get_onboarding_steps():
    """Get all onboarding steps"""
    return {
        "steps": ONBOARDING_STEPS,
        "total": len(ONBOARDING_STEPS)
    }


@router.get("/step/{step_id}")
async def get_step_details(step_id: str):
    """Get details for a specific onboarding step"""
    step = next((s for s in ONBOARDING_STEPS if s["id"] == step_id), None)
    
    if not step:
        raise HTTPException(status_code=404, detail="Step not found")
    
    # Add helpful tips for each step
    tips = {
        "welcome": [
            "IAskan analyse comment les IA parlent de votre marque",
            "Vous obtiendrez des scores et des recommandations concrètes"
        ],
        "create_project": [
            "Entrez l'URL de votre site pour démarrer",
            "Ajoutez vos concurrents pour des comparaisons"
        ],
        "first_scan": [
            "Un scan prend généralement 2-5 minutes",
            "Plus vous avez de prompts, plus l'analyse est précise"
        ],
        "explore_results": [
            "Le score global va de 0 à 100",
            "Cliquez sur chaque métrique pour plus de détails"
        ],
        "article_optimizer": [
            "Collez une URL d'article pour l'analyser",
            "Suivez les recommandations pour améliorer la citabilité"
        ],
        "completed": [
            "Lancez des analyses régulières pour suivre votre progression",
            "Programmez des scans automatiques dans les paramètres"
        ]
    }
    
    return {
        **step,
        "tips": tips.get(step_id, [])
    }
