"""
Article Optimizer Router - PostgreSQL Version
API endpoints for article GEO optimization
"""
from fastapi import APIRouter, HTTPException, Depends, Request, BackgroundTasks
from typing import Optional, List
from datetime import datetime, timezone
from pydantic import BaseModel, HttpUrl
from sqlalchemy import select, update, delete
import uuid

from ..core.config import SUBSCRIPTION_PLANS, EMERGENT_LLM_KEY
from ..engines.optimizer import optimizer_engine
from ..models.article_optimizer import ArticleOptimization, OptimizationResult
from ..db.database import async_session_maker
from ..db.services import UserService
from ..db.models import User, UserSession, Subscription, Project, ArticleOptimization as ArticleOptimizationModel

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
    
    async with async_session_maker() as db:
        # Find session
        session_result = await db.execute(
            select(UserSession).where(UserSession.session_token == token)
        )
        session = session_result.scalar_one_or_none()
        
        if not session:
            raise HTTPException(status_code=401, detail="Session expirée")
        
        # Find user
        user_result = await db.execute(
            select(User).where(User.user_id == session.user_id)
        )
        user = user_result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(status_code=401, detail="Utilisateur non trouvé")
        
        return UserService.to_dict(user)


async def check_optimizer_quota(user_id: str) -> dict:
    """Check if user has access to article optimizer - PostgreSQL version"""
    async with async_session_maker() as db:
        subscription_result = await db.execute(
            select(Subscription).where(Subscription.user_id == user_id)
        )
        subscription = subscription_result.scalar_one_or_none()
        
        if not subscription:
            return {"allowed": False, "reason": "Pas d'abonnement actif"}
        
        plan = subscription.plan.value if subscription.plan else "free"
        plan_config = SUBSCRIPTION_PLANS.get(plan, SUBSCRIPTION_PLANS["free"])
        
        # Check if feature is available
        if not plan_config.get("article_optimizer", False):
            return {
                "allowed": False,
                "reason": "L'optimiseur d'articles nécessite un abonnement Starter, Pro ou Business"
            }
        
        # Check quota
        limit = plan_config.get("article_optimizer_limit", 0)
        used = subscription.article_optimizer_used or 0
        
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
    try:
        quota = await check_optimizer_quota(user["user_id"])
        return quota
    except Exception as e:
        # Fallback for free users
        return {
            "allowed": True,
            "limit": 3,
            "used": 0,
            "remaining": 3
        }


@router.post("/analyze")
async def analyze_article(
    data: OptimizeArticleRequest,
    user: dict = Depends(get_current_user)
):
    """
    Analyze an article for GEO optimization - PostgreSQL version.
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
        async with async_session_maker() as db:
            result = await db.execute(
                select(Project)
                .where(Project.project_id == data.project_id)
                .where(Project.user_id == user["user_id"])
            )
            project = result.scalar_one_or_none()
            if project:
                brand_name = project.brand_name
    
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
        
        # Store result in PostgreSQL
        async with async_session_maker() as db:
            optimization = ArticleOptimizationModel(
                optimization_id=optimization_id,
                user_id=user["user_id"],
                organization_id=user.get("organization_id"),
                project_id=data.project_id,
                article_url=data.url,
                article_title=result.get("title", data.title),
                status="completed" if result.get("success") else "failed",
                result=result,
                processing_time_ms=processing_time
            )
            db.add(optimization)
            
            # Increment usage counter
            await db.execute(
                update(Subscription)
                .where(Subscription.user_id == user["user_id"])
                .values(article_optimizer_used=Subscription.article_optimizer_used + 1)
            )
            
            await db.commit()
        
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
        # Log error in PostgreSQL
        async with async_session_maker() as db:
            optimization = ArticleOptimizationModel(
                optimization_id=optimization_id,
                user_id=user["user_id"],
                article_url=data.url,
                status="failed",
                error_message=str(e)
            )
            db.add(optimization)
            await db.commit()
        
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
    Analyze article with LLM-enhanced recommendations - PostgreSQL version.
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
        async with async_session_maker() as db:
            result = await db.execute(
                select(Project)
                .where(Project.project_id == data.project_id)
                .where(Project.user_id == user["user_id"])
            )
            project = result.scalar_one_or_none()
            if project:
                brand_name = project.brand_name
    
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
        
        # Store optimization in PostgreSQL
        optimization_id = f"opt_{uuid.uuid4().hex[:12]}"
        async with async_session_maker() as db:
            optimization = ArticleOptimizationModel(
                optimization_id=optimization_id,
                user_id=user["user_id"],
                project_id=data.project_id,
                article_url=data.url,
                article_title=standard_result.get("title"),
                status="completed",
                result=enhanced_result,
                llm_enhanced=True
            )
            db.add(optimization)
            
            # Increment usage
            await db.execute(
                update(Subscription)
                .where(Subscription.user_id == user["user_id"])
                .values(article_optimizer_used=Subscription.article_optimizer_used + 1)
            )
            
            await db.commit()
        
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
    """Get user's optimization history - PostgreSQL version"""
    async with async_session_maker() as db:
        query = select(ArticleOptimizationModel).where(
            ArticleOptimizationModel.user_id == user["user_id"]
        )
        
        if project_id:
            query = query.where(ArticleOptimizationModel.project_id == project_id)
        
        query = query.order_by(ArticleOptimizationModel.created_at.desc()).limit(limit)
        
        result = await db.execute(query)
        optimizations = [
            {
                "optimization_id": opt.optimization_id,
                "user_id": opt.user_id,
                "project_id": opt.project_id,
                "article_url": opt.article_url,
                "article_title": opt.article_title,
                "status": opt.status,
                "llm_enhanced": opt.llm_enhanced,
                "processing_time_ms": opt.processing_time_ms,
                "created_at": opt.created_at.isoformat() if opt.created_at else None,
                "result": {
                    "scores": opt.result.get("scores") if opt.result else None,
                    "title": opt.result.get("title") if opt.result else None
                } if opt.result else None
            }
            for opt in result.scalars().all()
        ]
        
        return {"optimizations": optimizations}


@router.get("/{optimization_id}")
async def get_optimization(
    optimization_id: str,
    user: dict = Depends(get_current_user)
):
    """Get a specific optimization result - PostgreSQL version"""
    async with async_session_maker() as db:
        result = await db.execute(
            select(ArticleOptimizationModel)
            .where(ArticleOptimizationModel.optimization_id == optimization_id)
            .where(ArticleOptimizationModel.user_id == user["user_id"])
        )
        optimization = result.scalar_one_or_none()
        
        if not optimization:
            raise HTTPException(status_code=404, detail="Optimisation non trouvée")
        
        return {
            "optimization": {
                "optimization_id": optimization.optimization_id,
                "user_id": optimization.user_id,
                "project_id": optimization.project_id,
                "article_url": optimization.article_url,
                "article_title": optimization.article_title,
                "status": optimization.status,
                "result": optimization.result,
                "llm_enhanced": optimization.llm_enhanced,
                "processing_time_ms": optimization.processing_time_ms,
                "created_at": optimization.created_at.isoformat() if optimization.created_at else None,
                "completed_at": optimization.completed_at.isoformat() if optimization.completed_at else None
            }
        }


@router.delete("/{optimization_id}")
async def delete_optimization(
    optimization_id: str,
    user: dict = Depends(get_current_user)
):
    """Delete an optimization from history - PostgreSQL version"""
    async with async_session_maker() as db:
        result = await db.execute(
            delete(ArticleOptimizationModel)
            .where(ArticleOptimizationModel.optimization_id == optimization_id)
            .where(ArticleOptimizationModel.user_id == user["user_id"])
        )
        await db.commit()
        
        if result.rowcount == 0:
            raise HTTPException(status_code=404, detail="Optimisation non trouvée")
        
        return {"success": True, "message": "Optimisation supprimée"}


@router.get("/export/{optimization_id}")
async def export_optimization(
    optimization_id: str,
    format: str = "json",
    user: dict = Depends(get_current_user)
):
    """Export optimization result as JSON or Markdown - PostgreSQL version"""
    async with async_session_maker() as db:
        result = await db.execute(
            select(ArticleOptimizationModel)
            .where(ArticleOptimizationModel.optimization_id == optimization_id)
            .where(ArticleOptimizationModel.user_id == user["user_id"])
        )
        optimization = result.scalar_one_or_none()
        
        if not optimization:
            raise HTTPException(status_code=404, detail="Optimisation non trouvée")
        
        opt_result = optimization.result or {}
        
        if format == "json":
            return opt_result
        
        elif format == "markdown":
            # Generate markdown report
            md = f"""# Rapport d'Optimisation GEO

## Article Analysé
- **Titre**: {opt_result.get('title', 'N/A')}
- **URL**: {optimization.article_url or 'N/A'}
- **Date**: {optimization.created_at.isoformat() if optimization.created_at else 'N/A'}

## Scores

| Métrique | Score |
|----------|-------|
| Global | {opt_result.get('scores', {}).get('overall', 0)}/100 |
| Structure | {opt_result.get('scores', {}).get('structure', 0)}/100 |
| Autorité | {opt_result.get('scores', {}).get('authority', 0)}/100 |
| Citabilité | {opt_result.get('scores', {}).get('citability', 0)}/100 |
| Fraîcheur | {opt_result.get('scores', {}).get('freshness', 0)}/100 |

## Diagnostics

"""
            for diag in opt_result.get('diagnostics', []):
                md += f"### [{diag['severity'].upper()}] {diag['issue']}\n"
                md += f"{diag['recommendation']}\n\n"
            
            md += "## Plan d'Action\n\n"
            action_plan = opt_result.get('action_plan', {})
            
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
            
            if opt_result.get("llm_analysis"):
                md += f"## Analyse LLM\n\n{opt_result['llm_analysis']}\n"
            
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
    Simulate the impact of implementing specific improvements - PostgreSQL version.
    Returns projected score changes and implementation recommendations.
    """
    try:
        # Build current analysis from request or fetch from DB
        if request_data.optimization_id:
            # Fetch from database
            async with async_session_maker() as db:
                result = await db.execute(
                    select(ArticleOptimizationModel)
                    .where(ArticleOptimizationModel.optimization_id == request_data.optimization_id)
                )
                optimization = result.scalar_one_or_none()
                
                if not optimization:
                    raise HTTPException(status_code=404, detail="Optimisation non trouvée")
                
                current_analysis = optimization.result or {}
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
