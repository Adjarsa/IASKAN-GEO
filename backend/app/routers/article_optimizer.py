"""
Article Optimizer Router
API endpoints for article GEO optimization
"""
from fastapi import APIRouter, HTTPException, Depends, Request, BackgroundTasks
from typing import Optional, List
from datetime import datetime, timezone
from pydantic import BaseModel, HttpUrl
import uuid

from ..core.database import db
from ..core.config import SUBSCRIPTION_PLANS, EMERGENT_LLM_KEY
from ..engines.optimizer import optimizer_engine
from ..models.article_optimizer import ArticleOptimization, OptimizationResult

router = APIRouter(prefix="/api/article-optimizer", tags=["Article Optimizer"])


# Request Models
class OptimizeArticleRequest(BaseModel):
    url: Optional[str] = None
    content: Optional[str] = None
    title: Optional[str] = None
    project_id: Optional[str] = None


class OptimizeWithLLMRequest(BaseModel):
    url: Optional[str] = None
    content: Optional[str] = None
    project_id: Optional[str] = None
    use_llm: bool = True


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


async def check_optimizer_quota(user_id: str) -> dict:
    """Check if user has access to article optimizer"""
    subscription = await db.subscriptions.find_one({"user_id": user_id}, {"_id": 0})
    
    if not subscription:
        return {"allowed": False, "reason": "Pas d'abonnement actif"}
    
    plan = subscription.get("plan", "free")
    plan_config = SUBSCRIPTION_PLANS.get(plan, SUBSCRIPTION_PLANS["free"])
    
    # Check if feature is available
    if not plan_config.get("article_optimizer", False):
        return {
            "allowed": False,
            "reason": "L'optimiseur d'articles nécessite un abonnement Starter, Pro ou Business"
        }
    
    # Check quota
    limit = plan_config.get("article_optimizer_limit", 0)
    used = subscription.get("article_optimizer_used", 0)
    
    if limit != -1 and used >= limit:  # -1 = unlimited
        return {
            "allowed": False,
            "reason": f"Quota d'optimisations atteint ({used}/{limit} ce mois)"
        }
    
    return {
        "allowed": True,
        "limit": limit,
        "used": used,
        "remaining": "illimité" if limit == -1 else limit - used
    }


@router.get("/quota")
async def get_optimizer_quota(user: dict = Depends(get_current_user)):
    """Get user's article optimizer quota"""
    quota = await check_optimizer_quota(user["user_id"])
    return quota


@router.post("/analyze")
async def analyze_article(
    data: OptimizeArticleRequest,
    user: dict = Depends(get_current_user)
):
    """
    Analyze an article for GEO optimization.
    Returns detailed diagnostics and action plan.
    """
    # Check quota
    quota = await check_optimizer_quota(user["user_id"])
    if not quota["allowed"]:
        raise HTTPException(status_code=403, detail=quota["reason"])
    
    # Validate input
    if not data.url and not data.content:
        raise HTTPException(
            status_code=400,
            detail="Veuillez fournir une URL ou du contenu à analyser"
        )
    
    # Get brand name from project if provided
    brand_name = None
    if data.project_id:
        project = await db.projects.find_one(
            {"project_id": data.project_id, "user_id": user["user_id"]},
            {"_id": 0}
        )
        if project:
            brand_name = project.get("brand_name")
    
    # Create optimization record
    optimization_id = f"opt_{uuid.uuid4().hex[:12]}"
    start_time = datetime.now(timezone.utc)
    
    # Run analysis
    try:
        result = await optimizer_engine.analyze_article(
            url=data.url,
            content=data.content,
            brand_name=brand_name
        )
        
        processing_time = int((datetime.now(timezone.utc) - start_time).total_seconds() * 1000)
        
        # Store result
        optimization_doc = {
            "optimization_id": optimization_id,
            "user_id": user["user_id"],
            "organization_id": user.get("organization_id"),
            "project_id": data.project_id,
            "article_url": data.url,
            "article_title": result.get("title", data.title),
            "status": "completed" if result.get("success") else "failed",
            "result": result,
            "created_at": start_time.isoformat(),
            "completed_at": datetime.now(timezone.utc).isoformat(),
            "processing_time_ms": processing_time
        }
        
        await db.article_optimizations.insert_one(optimization_doc)
        
        # Increment usage counter
        await db.subscriptions.update_one(
            {"user_id": user["user_id"]},
            {"$inc": {"article_optimizer_used": 1}}
        )
        
        return {
            "success": result.get("success", False),
            "optimization_id": optimization_id,
            "title": result.get("title"),
            "scores": result.get("scores"),
            "diagnostics": result.get("diagnostics"),
            "action_plan": result.get("action_plan"),
            "quick_wins": result.get("quick_wins"),
            "distribution_strategy": result.get("distribution_strategy"),
            "missing_elements": result.get("missing_elements"),
            "keyword_opportunities": result.get("keyword_opportunities"),
            "processing_time_ms": processing_time
        }
        
    except Exception as e:
        # Log error
        error_doc = {
            "optimization_id": optimization_id,
            "user_id": user["user_id"],
            "article_url": data.url,
            "status": "failed",
            "error": str(e),
            "created_at": start_time.isoformat()
        }
        await db.article_optimizations.insert_one(error_doc)
        
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de l'analyse: {str(e)}"
        )


@router.post("/analyze-with-llm")
async def analyze_with_llm(
    data: OptimizeWithLLMRequest,
    user: dict = Depends(get_current_user)
):
    """
    Analyze article with LLM-enhanced recommendations.
    Uses GPT to generate more detailed and contextual suggestions.
    """
    # Check quota
    quota = await check_optimizer_quota(user["user_id"])
    if not quota["allowed"]:
        raise HTTPException(status_code=403, detail=quota["reason"])
    
    if not EMERGENT_LLM_KEY:
        raise HTTPException(
            status_code=503,
            detail="Service LLM non disponible"
        )
    
    # Validate input
    if not data.url and not data.content:
        raise HTTPException(
            status_code=400,
            detail="Veuillez fournir une URL ou du contenu à analyser"
        )
    
    # Get brand name from project
    brand_name = None
    if data.project_id:
        project = await db.projects.find_one(
            {"project_id": data.project_id, "user_id": user["user_id"]},
            {"_id": 0}
        )
        if project:
            brand_name = project.get("brand_name")
    
    # First run standard analysis
    standard_result = await optimizer_engine.analyze_article(
        url=data.url,
        content=data.content,
        brand_name=brand_name
    )
    
    if not standard_result.get("success"):
        raise HTTPException(status_code=400, detail="Impossible d'analyser l'article")
    
    # Enhance with LLM
    try:
        from ..services.llm_abstraction import LlmChat, UserMessage
        
        # Prepare context for LLM
        diagnostics_summary = "\n".join([
            f"- [{d['severity'].upper()}] {d['issue']}: {d['recommendation']}"
            for d in standard_result.get("diagnostics", [])[:10]
        ])
        
        prompt = f"""Analyse cette page web pour son optimisation GEO (Generative Engine Optimization).

TITRE: {standard_result.get('title', 'N/A')}
URL: {data.url or 'Contenu direct'}
SCORE GLOBAL: {standard_result.get('scores', {}).get('overall', 0)}/100

DIAGNOSTICS EXISTANTS:
{diagnostics_summary}

En tant qu'expert GEO, fournis:

1. **RÉSUMÉ EXÉCUTIF** (3-4 phrases)
Un résumé clair de l'état actuel de la page pour les LLMs.

2. **TOP 5 ACTIONS PRIORITAIRES**
Les 5 actions les plus impactantes pour améliorer la visibilité dans les réponses IA.

3. **RECOMMANDATIONS DE CONTENU**
- Sections à ajouter
- Angles manquants
- Questions à couvrir (pour FAQ)

4. **STRATÉGIE DE DISTRIBUTION**
Comment amplifier la visibilité de ce contenu.

5. **CALENDRIER RECOMMANDÉ**
- Actions immédiates (cette semaine)
- Court terme (ce mois)
- Moyen terme (3 mois)

Réponds en français, de manière structurée et actionnable."""
        
        chat = LlmChat(
            api_key=EMERGENT_LLM_KEY,
            model="gpt-4o",
            system_prompt="Tu es un expert en GEO (Generative Engine Optimization), spécialisé dans l'optimisation de contenu pour être cité par les LLMs comme ChatGPT, Claude et Gemini."
        )
        
        llm_response = await chat.send_async(UserMessage(prompt))
        
        # Combine results
        enhanced_result = {
            **standard_result,
            "llm_analysis": llm_response,
            "enhanced": True
        }
        
        # Store optimization
        optimization_id = f"opt_{uuid.uuid4().hex[:12]}"
        await db.article_optimizations.insert_one({
            "optimization_id": optimization_id,
            "user_id": user["user_id"],
            "project_id": data.project_id,
            "article_url": data.url,
            "article_title": standard_result.get("title"),
            "status": "completed",
            "result": enhanced_result,
            "llm_enhanced": True,
            "created_at": datetime.now(timezone.utc).isoformat()
        })
        
        # Increment usage
        await db.subscriptions.update_one(
            {"user_id": user["user_id"]},
            {"$inc": {"article_optimizer_used": 1}}
        )
        
        return {
            "success": True,
            "optimization_id": optimization_id,
            **enhanced_result
        }
        
    except Exception as e:
        # Return standard result if LLM fails
        return {
            "success": True,
            "llm_error": str(e),
            **standard_result
        }


@router.get("/history")
async def get_optimization_history(
    limit: int = 20,
    project_id: Optional[str] = None,
    user: dict = Depends(get_current_user)
):
    """Get user's optimization history"""
    query = {"user_id": user["user_id"]}
    if project_id:
        query["project_id"] = project_id
    
    optimizations = await db.article_optimizations.find(
        query,
        {"_id": 0, "result.raw_analysis": 0}  # Exclude large raw data
    ).sort("created_at", -1).limit(limit).to_list(limit)
    
    return {"optimizations": optimizations}


@router.get("/{optimization_id}")
async def get_optimization(
    optimization_id: str,
    user: dict = Depends(get_current_user)
):
    """Get a specific optimization result"""
    optimization = await db.article_optimizations.find_one(
        {"optimization_id": optimization_id, "user_id": user["user_id"]},
        {"_id": 0}
    )
    
    if not optimization:
        raise HTTPException(status_code=404, detail="Optimisation non trouvée")
    
    return {"optimization": optimization}


@router.delete("/{optimization_id}")
async def delete_optimization(
    optimization_id: str,
    user: dict = Depends(get_current_user)
):
    """Delete an optimization from history"""
    result = await db.article_optimizations.delete_one({
        "optimization_id": optimization_id,
        "user_id": user["user_id"]
    })
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Optimisation non trouvée")
    
    return {"success": True, "message": "Optimisation supprimée"}


@router.get("/export/{optimization_id}")
async def export_optimization(
    optimization_id: str,
    format: str = "json",
    user: dict = Depends(get_current_user)
):
    """Export optimization result as JSON or Markdown"""
    optimization = await db.article_optimizations.find_one(
        {"optimization_id": optimization_id, "user_id": user["user_id"]},
        {"_id": 0}
    )
    
    if not optimization:
        raise HTTPException(status_code=404, detail="Optimisation non trouvée")
    
    result = optimization.get("result", {})
    
    if format == "json":
        return result
    
    elif format == "markdown":
        # Generate markdown report
        md = f"""# Rapport d'Optimisation GEO

## Article Analysé
- **Titre**: {result.get('title', 'N/A')}
- **URL**: {optimization.get('article_url', 'N/A')}
- **Date**: {optimization.get('created_at', 'N/A')}

## Scores

| Métrique | Score |
|----------|-------|
| Global | {result.get('scores', {}).get('overall', 0)}/100 |
| Structure | {result.get('scores', {}).get('structure', 0)}/100 |
| Autorité | {result.get('scores', {}).get('authority', 0)}/100 |
| Citabilité | {result.get('scores', {}).get('citability', 0)}/100 |
| Fraîcheur | {result.get('scores', {}).get('freshness', 0)}/100 |

## Diagnostics

"""
        for diag in result.get('diagnostics', []):
            md += f"### [{diag['severity'].upper()}] {diag['issue']}\n"
            md += f"{diag['recommendation']}\n\n"
        
        md += "## Plan d'Action\n\n"
        action_plan = result.get('action_plan', {})
        
        for phase, data in [
            ("immediate", "Actions Immédiates"),
            ("short_term", "Court Terme"),
            ("medium_term", "Moyen Terme")
        ]:
            if action_plan.get(phase):
                md += f"### {data}\n"
                for action in action_plan[phase]:
                    md += f"- {action.get('action', '')}\n"
                md += "\n"
        
        if result.get("llm_analysis"):
            md += f"## Analyse LLM\n\n{result['llm_analysis']}\n"
        
        return {"markdown": md}
    
    else:
        raise HTTPException(status_code=400, detail="Format non supporté (json ou markdown)")



# Simulation endpoint
class SimulateImpactRequest(BaseModel):
    optimization_id: Optional[str] = None
    current_scores: Optional[dict] = None
    overall_score: Optional[float] = None
    improvements: List[str]


@router.post("/simulate")
async def simulate_optimization_impact(
    request_data: SimulateImpactRequest,
    user: dict = Depends(get_current_user)
):
    """
    Simulate the impact of implementing specific improvements.
    Returns projected score changes and implementation recommendations.
    """
    try:
        # Build current analysis from request or fetch from DB
        if request_data.optimization_id:
            # Fetch from database
            optimization = await db.article_optimizations.find_one(
                {"optimization_id": request_data.optimization_id},
                {"_id": 0}
            )
            if not optimization:
                raise HTTPException(status_code=404, detail="Optimisation non trouvée")
            
            current_analysis = optimization.get("result", {})
        else:
            # Use provided scores
            current_analysis = {
                "overall_score": request_data.overall_score or 50,
                "scores": request_data.current_scores or {}
            }
        
        # Run simulation
        result = optimizer_engine.simulate_impact(
            current_analysis=current_analysis,
            improvements=request_data.improvements
        )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/improvement-options")
async def get_improvement_options(user: dict = Depends(get_current_user)):
    """
    Get all available improvement options for the simulator.
    """
    return {
        "categories": {
            "content": {
                "name": "Contenu",
                "improvements": [
                    {"id": "add_faq", "name": "Ajouter une section FAQ", "impact": "high", "effort": "easy"},
                    {"id": "improve_structure", "name": "Améliorer la structure (H2/H3)", "impact": "high", "effort": "easy"},
                    {"id": "add_definitions", "name": "Ajouter des définitions claires", "impact": "medium", "effort": "easy"},
                    {"id": "expand_content", "name": "Enrichir le contenu (+1000 mots)", "impact": "high", "effort": "medium"},
                    {"id": "add_introduction", "name": "Renforcer l'introduction", "impact": "medium", "effort": "easy"},
                ]
            },
            "authority": {
                "name": "Autorité",
                "improvements": [
                    {"id": "add_author", "name": "Ajouter les infos auteur", "impact": "high", "effort": "easy"},
                    {"id": "add_sources", "name": "Citer des sources fiables", "impact": "high", "effort": "medium"},
                    {"id": "add_credentials", "name": "Afficher les credentials", "impact": "medium", "effort": "easy"},
                    {"id": "update_date", "name": "Mettre à jour la date", "impact": "medium", "effort": "easy"},
                    {"id": "add_expert_review", "name": "Ajouter une review d'expert", "impact": "high", "effort": "medium"},
                ]
            },
            "technical": {
                "name": "Technique",
                "improvements": [
                    {"id": "add_schema", "name": "Ajouter Schema.org", "impact": "high", "effort": "medium"},
                    {"id": "improve_meta", "name": "Optimiser les meta tags", "impact": "medium", "effort": "easy"},
                    {"id": "add_structured_data", "name": "Ajouter données structurées", "impact": "high", "effort": "medium"},
                    {"id": "optimize_headings", "name": "Optimiser les titres H1/H2", "impact": "medium", "effort": "easy"},
                ]
            },
            "engagement": {
                "name": "Engagement",
                "improvements": [
                    {"id": "add_media", "name": "Ajouter images/vidéos", "impact": "medium", "effort": "medium"},
                    {"id": "add_internal_links", "name": "Ajouter liens internes", "impact": "medium", "effort": "easy"},
                    {"id": "add_cta", "name": "Ajouter des CTAs", "impact": "low", "effort": "easy"},
                ]
            }
        }
    }
