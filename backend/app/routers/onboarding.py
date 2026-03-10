"""
Onboarding Router
API endpoints for user onboarding flow
"""
from fastapi import APIRouter, HTTPException, Depends, Request
from typing import Optional, List
from datetime import datetime, timezone
from pydantic import BaseModel

from ..core.database import db

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
    
    session = await db.user_sessions.find_one({"session_token": token}, {"_id": 0})
    if not session:
        raise HTTPException(status_code=401, detail="Session expirée")
    
    user = await db.users.find_one({"user_id": session["user_id"]}, {"_id": 0})
    if not user:
        raise HTTPException(status_code=401, detail="Utilisateur non trouvé")
    
    return user


@router.get("/status")
async def get_onboarding_status(user: dict = Depends(get_current_user)):
    """Get user's onboarding progress"""
    onboarding = await db.user_onboarding.find_one(
        {"user_id": user["user_id"]},
        {"_id": 0}
    )
    
    if not onboarding:
        # Initialize onboarding for new user
        onboarding = {
            "user_id": user["user_id"],
            "current_step": "welcome",
            "completed_steps": [],
            "skipped": False,
            "started_at": datetime.now(timezone.utc).isoformat(),
            "completed_at": None
        }
        await db.user_onboarding.insert_one(onboarding)
    
    # Check if user has completed key actions
    has_project = await db.projects.count_documents({"user_id": user["user_id"]}) > 0
    has_analysis = await db.analyses.count_documents({"user_id": user["user_id"]}) > 0
    has_optimization = await db.article_optimizations.count_documents({"user_id": user["user_id"]}) > 0
    
    return {
        "onboarding": onboarding,
        "steps": ONBOARDING_STEPS,
        "progress": {
            "has_project": has_project,
            "has_analysis": has_analysis,
            "has_optimization": has_optimization
        },
        "show_onboarding": not onboarding.get("skipped") and onboarding.get("current_step") != "completed"
    }


@router.post("/step/{step_id}/complete")
async def complete_step(step_id: str, user: dict = Depends(get_current_user)):
    """Mark an onboarding step as completed"""
    valid_steps = [s["id"] for s in ONBOARDING_STEPS]
    
    if step_id not in valid_steps:
        raise HTTPException(status_code=400, detail="Étape invalide")
    
    onboarding = await db.user_onboarding.find_one({"user_id": user["user_id"]})
    
    if not onboarding:
        onboarding = {
            "user_id": user["user_id"],
            "current_step": "welcome",
            "completed_steps": [],
            "skipped": False,
            "started_at": datetime.now(timezone.utc).isoformat()
        }
    
    completed_steps = onboarding.get("completed_steps", [])
    if step_id not in completed_steps:
        completed_steps.append(step_id)
    
    # Determine next step
    current_index = next((i for i, s in enumerate(ONBOARDING_STEPS) if s["id"] == step_id), 0)
    next_step = ONBOARDING_STEPS[current_index + 1]["id"] if current_index < len(ONBOARDING_STEPS) - 1 else "completed"
    
    update_data = {
        "completed_steps": completed_steps,
        "current_step": next_step,
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    
    if next_step == "completed":
        update_data["completed_at"] = datetime.now(timezone.utc).isoformat()
    
    await db.user_onboarding.update_one(
        {"user_id": user["user_id"]},
        {"$set": update_data},
        upsert=True
    )
    
    return {
        "success": True,
        "current_step": next_step,
        "completed_steps": completed_steps
    }


@router.post("/skip")
async def skip_onboarding(user: dict = Depends(get_current_user)):
    """Skip the onboarding flow"""
    await db.user_onboarding.update_one(
        {"user_id": user["user_id"]},
        {"$set": {
            "skipped": True,
            "current_step": "completed",
            "updated_at": datetime.now(timezone.utc).isoformat()
        }},
        upsert=True
    )
    
    return {"success": True, "message": "Onboarding ignoré"}


@router.post("/restart")
async def restart_onboarding(user: dict = Depends(get_current_user)):
    """Restart the onboarding flow"""
    await db.user_onboarding.update_one(
        {"user_id": user["user_id"]},
        {"$set": {
            "current_step": "welcome",
            "completed_steps": [],
            "skipped": False,
            "started_at": datetime.now(timezone.utc).isoformat(),
            "completed_at": None
        }},
        upsert=True
    )
    
    return {"success": True, "message": "Onboarding redémarré"}


@router.get("/tips/{feature}")
async def get_feature_tips(feature: str):
    """Get contextual tips for a specific feature"""
    tips = {
        "dashboard": [
            "Votre Score GEO Global représente votre visibilité moyenne dans les réponses IA",
            "Consultez l'évolution de vos scores pour suivre vos progrès",
            "Les recommandations sont classées par impact potentiel"
        ],
        "analysis": [
            "Un scan analyse jusqu'à 200 requêtes sur 4 IA différentes",
            "Plus vous ajoutez de concurrents, plus le benchmark sera précis",
            "Les scans programmés vous envoient un rapport par email"
        ],
        "article_optimizer": [
            "L'optimiseur analyse la structure, l'autorité et la citabilité de votre contenu",
            "Suivez les Quick Wins pour des améliorations rapides",
            "L'analyse LLM fournit des recommandations personnalisées"
        ],
        "competitors": [
            "Ajoutez vos principaux concurrents pour un benchmark précis",
            "Le Dominance Index montre qui domine chaque type de requête",
            "Identifiez les opportunités où vos concurrents sont absents"
        ]
    }
    
    return {"tips": tips.get(feature, [])}
