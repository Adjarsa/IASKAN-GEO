"""
Analysis Runner Service - PostgreSQL Version with Real LLM Integration
IAskan Verified GEO Protocol™ v2.2 - Optimized for Speed
"""
import asyncio
import logging
import random
from datetime import datetime, timezone
from typing import Dict, Any, List

from sqlalchemy import select, update
from ..db.database import async_session_maker
from ..db.models import Analysis, Project, Subscription, User
from .email_service import email_service

logger = logging.getLogger(__name__)

# Query templates for different intent types - GEO optimized
# IMPORTANT: Most queries should NOT include the brand name
# to test ORGANIC visibility (will the AI mention us naturally?)

QUERY_TEMPLATES = {
    # Generic transactional - NO brand name (high GEO value)
    "transactional_generic": [
        "Quel est le meilleur {keyword} en 2024?",
        "Je cherche un {keyword} fiable et performant, que me conseillez-vous?",
        "Quelle marque de {keyword} acheter?",
        "Top 5 des meilleurs {keyword} rapport qualité-prix",
        "Quel {keyword} choisir pour un usage quotidien?",
        "Meilleur {keyword} pas cher mais de qualité",
        "Recommandez-moi un bon {keyword}",
        "Quel {keyword} acheter en ce moment?",
    ],
    # Generic comparative - NO brand name (high GEO value)
    "comparative_generic": [
        "Comparez les meilleures marques de {keyword}",
        "Quels sont les leaders du marché en {keyword}?",
        "Classement des meilleures marques de {keyword}",
        "Quelle est la meilleure marque de {keyword}?",
        "Top marques de {keyword} recommandées",
        "Quelles marques de {keyword} sont les plus fiables?",
    ],
    # Problem-solving - NO brand name (high GEO value)
    "problem_solving": [
        "Je cherche un {keyword} durable et pas trop cher",
        "Quel {keyword} pour un budget limité?",
        "Meilleur {keyword} pour les professionnels?",
        "Quel {keyword} offre le meilleur rapport qualité-prix?",
        "Je veux un {keyword} qui dure longtemps, que choisir?",
        "Quel {keyword} pour une utilisation intensive?",
    ],
    # Informational - NO brand name (medium GEO value)
    "informational": [
        "Comment choisir un bon {keyword}?",
        "Quels critères pour acheter un {keyword}?",
        "Guide d'achat {keyword} : que regarder?",
        "Qu'est-ce qui fait un bon {keyword}?",
        "Les points importants pour choisir son {keyword}",
    ],
    # Brand reputation queries - WITH brand name (validation only, ~20% of queries)
    "brand_validation": [
        "Est-ce que {brand} est une bonne marque?",
        "{brand} vs la concurrence, que choisir?",
        "Les produits {brand} sont-ils fiables?",
    ],
}


async def update_analysis(analysis_id: str, updates: dict):
    """Update analysis record in PostgreSQL with retry logic"""
    max_retries = 3
    retry_delay = 1
    
    for attempt in range(max_retries):
        try:
            async with async_session_maker() as db:
                # All columns that exist in the Analysis model
                existing_columns = {
                    'status', 'global_score', 'grade', 'mention_rate', 'ai_scores',
                    'rate_scores', 'query_scores', 'recommendations', 'total_queries',
                    'queries_processed', 'queries_with_mention', 'current_phase',
                    'ai_engines_used', 'error_message', 'started_at', 'completed_at', 
                    'competitor_analysis', 'stability_score', 'average_position'
                }
                
                valid_updates = {k: v for k, v in updates.items() if v is not None and k in existing_columns}
                
                if valid_updates:
                    logger.info(f"[{analysis_id}] Updating: {list(valid_updates.keys())} (attempt {attempt + 1})")
                    result = await db.execute(
                        update(Analysis).where(
                            Analysis.analysis_id == analysis_id
                        ).values(**valid_updates)
                    )
                    await db.commit()
                    logger.info(f"[{analysis_id}] Update committed successfully")
                    return True
        except Exception as e:
            logger.error(f"[{analysis_id}] Update error (attempt {attempt + 1}/{max_retries}): {e}")
            if attempt < max_retries - 1:
                await asyncio.sleep(retry_delay)
                retry_delay *= 2  # Exponential backoff
            else:
                import traceback
                logger.error(f"[{analysis_id}] Update failed after {max_retries} attempts")
                logger.error(traceback.format_exc())
    return False


async def update_subscription_usage(user_id: str, api_calls: int):
    """Update subscription usage counters after analysis"""
    try:
        async with async_session_maker() as db:
            # Increment queries_used and scans_used
            await db.execute(
                update(Subscription)
                .where(Subscription.user_id == user_id)
                .values(
                    queries_used=Subscription.queries_used + api_calls,
                    scans_used=Subscription.scans_used + 1
                )
            )
            await db.commit()
            logger.info(f"Updated subscription for user {user_id}: +{api_calls} queries, +1 scan")
    except Exception as e:
        logger.error(f"Error updating subscription usage for {user_id}: {e}")


async def get_user_info(user_id: str) -> Dict[str, str]:
    """Get user email and name for notification"""
    try:
        async with async_session_maker() as db:
            result = await db.execute(
                select(User).where(User.user_id == user_id)
            )
            user = result.scalar_one_or_none()
            if user:
                return {
                    "email": user.email,
                    "name": user.name or user.email.split("@")[0]
                }
    except Exception as e:
        logger.error(f"Error getting user info for {user_id}: {e}")
    return None


async def send_analysis_complete_notification(
    user_id: str,
    project_name: str,
    brand_name: str,
    global_score: float,
    grade: str,
    analysis_id: str,
    recommendations: List[Dict[str, Any]] = None
):
    """Send email and in-app notification when analysis is complete"""
    try:
        user_info = await get_user_info(user_id)
        if not user_info:
            logger.warning(f"Cannot send notification: user {user_id} not found")
            return
        
        # Extract top recommendation titles
        top_recs = []
        if recommendations:
            top_recs = [rec.get("title", "") for rec in recommendations[:3] if rec.get("title")]
        
        # Send email notification
        await email_service.send_scan_complete_email(
            email=user_info["email"],
            user_name=user_info["name"],
            project_name=project_name,
            brand_name=brand_name,
            global_score=global_score,
            grade=grade,
            analysis_id=analysis_id,
            recommendations=top_recs
        )
        
        # Create in-app notification
        from ..db.services import NotificationService
        async with async_session_maker() as db:
            await NotificationService.create(
                db,
                user_id=user_id,
                type="scan_complete",
                title=f"Analyse terminée - Score {int(global_score)}/100",
                message=f"L'analyse GEO de {brand_name} ({project_name}) est terminée avec la note {grade}.",
                data={
                    "analysis_id": analysis_id,
                    "project_name": project_name,
                    "brand_name": brand_name,
                    "score": global_score,
                    "grade": grade
                }
            )
        
        logger.info(f"Analysis complete notification sent to {user_info['email']}")
    except Exception as e:
        logger.error(f"Failed to send analysis complete notification: {e}")
    except Exception as e:
        logger.error(f"Failed to send analysis complete notification: {e}")


def generate_queries(brand_name: str, keywords: List[str], num_queries: int, industry: str = "") -> List[Dict[str, Any]]:
    """
    Generate diverse, realistic queries for GEO analysis.
    
    IMPORTANT: ~80% of queries are GENERIC (no brand name) to test organic visibility.
    Only ~20% include the brand name for validation purposes.
    """
    queries = []
    used_templates = set()
    
    if not keywords:
        keywords = [brand_name]
    
    if not industry:
        industry = "le marché"
    
    # Priority: Generic queries first (80%), brand queries last (20%)
    generic_types = ["transactional_generic", "comparative_generic", "problem_solving", "informational"]
    brand_types = ["brand_validation"]
    
    # Calculate distribution: 80% generic, 20% brand
    generic_count = int(num_queries * 0.80)
    brand_count = num_queries - generic_count
    
    # Generate generic queries (NO brand name - true GEO test)
    for query_type in generic_types:
        templates = QUERY_TEMPLATES.get(query_type, []).copy()
        random.shuffle(templates)
        
        queries_per_type = generic_count // len(generic_types)
        count = 0
        
        for template in templates:
            if len([q for q in queries if q["type"].startswith("generic") or q["type"] in generic_types]) >= generic_count:
                break
            if count >= queries_per_type + 2:  # Allow slight overflow
                break
            
            keyword = keywords[len(queries) % len(keywords)]
            
            query_text = template.format(
                keyword=keyword,
                industry=industry
            )
            
            if query_text not in used_templates:
                used_templates.add(query_text)
                queries.append({
                    "text": query_text,
                    "type": query_type,
                    "keyword": keyword,
                    "includes_brand": False  # Flag for analysis
                })
                count += 1
    
    # Generate brand validation queries (~20%)
    for query_type in brand_types:
        templates = QUERY_TEMPLATES.get(query_type, []).copy()
        random.shuffle(templates)
        
        for template in templates:
            if len([q for q in queries if q.get("includes_brand")]) >= brand_count:
                break
            
            keyword = keywords[len(queries) % len(keywords)]
            
            query_text = template.format(
                keyword=keyword,
                brand=brand_name,
                industry=industry
            )
            
            if query_text not in used_templates:
                used_templates.add(query_text)
                queries.append({
                    "text": query_text,
                    "type": query_type,
                    "keyword": keyword,
                    "includes_brand": True  # Flag for analysis
                })
    
    # Shuffle to mix generic and brand queries
    random.shuffle(queries)
    
    logger.info(f"Generated {len(queries)} queries for '{brand_name}': {len([q for q in queries if not q.get('includes_brand')])} generic, {len([q for q in queries if q.get('includes_brand')])} with brand")
    
    return queries[:num_queries]


def calculate_rate_score(all_responses: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Calculate R.A.T.E. score from responses"""
    if not all_responses:
        return {"relevance": 0, "authority": 0, "truthfulness": 0, "endorsement": 0, "total": 0, "grade": "F"}
    
    valid_responses = [r for r in all_responses if not r.get("error")]
    if not valid_responses:
        return {"relevance": 0, "authority": 0, "truthfulness": 0, "endorsement": 0, "total": 0, "grade": "F"}
    
    # Relevance: Based on mention rate and position
    mentioned = sum(1 for r in valid_responses if r.get("brand_mentioned", False))
    mention_rate = mentioned / len(valid_responses) if valid_responses else 0
    relevance = mention_rate * 100
    
    # Authority: Based on role scores
    role_scores = [r.get("role_score", 0) for r in valid_responses if r.get("brand_mentioned")]
    authority = (sum(role_scores) / len(role_scores) * 100) if role_scores else 30
    
    # Truthfulness: Based on credibility
    cred_scores = [r.get("credibility_score", 50) for r in valid_responses if r.get("brand_mentioned")]
    truthfulness = (sum(cred_scores) / len(cred_scores)) if cred_scores else 50
    
    # Endorsement: Based on conversion potential
    conv_scores = [r.get("conversion_score", 0) for r in valid_responses if r.get("brand_mentioned")]
    endorsement = (sum(conv_scores) / len(conv_scores)) if conv_scores else 30
    
    # Total weighted score
    total = (relevance * 0.30) + (authority * 0.25) + (truthfulness * 0.20) + (endorsement * 0.25)
    
    # Grade
    if total >= 80:
        grade = "A"
    elif total >= 65:
        grade = "B"
    elif total >= 50:
        grade = "C"
    elif total >= 35:
        grade = "D"
    else:
        grade = "F"
    
    return {
        "relevance": round(relevance, 1),
        "authority": round(authority, 1),
        "truthfulness": round(truthfulness, 1),
        "endorsement": round(endorsement, 1),
        "total": round(total, 1),
        "grade": grade
    }


def generate_recommendations(rate_scores: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Generate actionable recommendations"""
    recommendations = []
    
    if rate_scores.get("relevance", 0) < 50:
        recommendations.append({
            "priority": "critical",
            "category": "content",
            "title": "Améliorer la visibilité de marque",
            "description": "Votre marque n'est pas suffisamment mentionnée par les IA. Créez du contenu optimisé.",
            "impact": "critique",
            "effort": "moyen",
            "metrics_impacted": ["relevance"]
        })
    
    if rate_scores.get("authority", 0) < 50:
        recommendations.append({
            "priority": "high",
            "category": "authority",
            "title": "Renforcer l'autorité de marque",
            "description": "Positionnez-vous comme leader avec du contenu expert et des backlinks de qualité.",
            "impact": "eleve",
            "effort": "eleve",
            "metrics_impacted": ["authority"]
        })
    
    if not recommendations:
        recommendations.append({
            "priority": "low",
            "category": "optimization",
            "title": "Continuer les bonnes pratiques",
            "description": "Vos scores sont bons. Maintenez la qualité de votre contenu.",
            "impact": "faible",
            "effort": "faible",
            "metrics_impacted": ["all"]
        })
    
    return recommendations


async def query_llm_with_timeout(llm_connector, query_text: str, ai_type: str, run_id: int, brand_name: str, competitors: List[str], timeout: int = 60) -> Dict[str, Any]:
    """Query LLM with timeout protection - generous timeout for reliability"""
    try:
        response = await asyncio.wait_for(
            llm_connector.query_llm(
                query_text=query_text,
                ai_type=ai_type,
                run_id=run_id,
                brand_name=brand_name,
                competitors=competitors
            ),
            timeout=timeout
        )
        return response
    except asyncio.TimeoutError:
        logger.warning(f"LLM query timeout for {ai_type} after {timeout}s")
        return {
            "ai_type": ai_type,
            "run_id": run_id,
            "error": "timeout",
            "brand_mentioned": False,
            "role_score": 0.0
        }
    except Exception as e:
        logger.error(f"LLM query error: {e}")
        return {
            "ai_type": ai_type,
            "run_id": run_id,
            "error": str(e),
            "brand_mentioned": False,
            "role_score": 0.0
        }


async def run_analysis_simplified(analysis_id: str, project: dict, plan_config: dict):
    """
    IAskan Verified GEO Protocol™ Analysis Engine
    Optimized version with parallel queries and timeouts
    RESPECTS plan_config for precision and reliability
    """
    try:
        brand_name = project.get("brand_name", "")
        keywords = project.get("keywords", [])
        competitors = project.get("competitors", [])
        industry = project.get("industry", "")
        
        # Use FULL plan config - no reduction
        ai_engines = plan_config.get("ai_engines", ["chatgpt"])
        num_prompts = plan_config.get("num_prompts", 10)
        runs_per_query = plan_config.get("runs_per_query", 3)
        
        if not brand_name:
            raise ValueError("Nom de marque requis")
        
        logger.info(f"Starting analysis {analysis_id} for brand: {brand_name}")
        logger.info(f"Config: {num_prompts} queries × {runs_per_query} runs × {len(ai_engines)} AIs")
        
        # Update status
        await update_analysis(analysis_id, {
            "status": "running",
            "current_phase": "query_generation",
            "started_at": datetime.now(timezone.utc)
        })
        
        # Import LLM connector
        from .llm_connector import LLMConnector
        llm_connector = LLMConnector()
        
        # Generate queries
        queries = generate_queries(brand_name, keywords, num_prompts, industry)
        total_queries = len(queries)
        
        logger.info(f"Generated {total_queries} queries")
        
        await update_analysis(analysis_id, {
            "current_phase": "ai_querying",
            "total_queries": total_queries
        })
        
        # Process queries in batches for speed
        all_responses = []
        query_results = []
        
        for query_idx, query in enumerate(queries):
            query_text = query["text"]
            query_type = query["type"]
            
            logger.info(f"Query {query_idx + 1}/{total_queries}: {query_text[:40]}...")
            
            # Run all AI engines in parallel for this query
            tasks = []
            for run_id in range(1, runs_per_query + 1):
                for ai_type in ai_engines:
                    tasks.append(
                        query_llm_with_timeout(
                            llm_connector, query_text, ai_type, run_id,
                            brand_name, competitors, timeout=25
                        )
                    )
            
            # Execute in parallel with overall timeout per batch
            try:
                query_responses = await asyncio.wait_for(
                    asyncio.gather(*tasks, return_exceptions=True),
                    timeout=120  # 2 min per query batch for reliability
                )
                # Filter out exceptions
                query_responses = [r for r in query_responses if isinstance(r, dict)]
            except asyncio.TimeoutError:
                logger.warning(f"Query batch timeout at query {query_idx}")
                query_responses = []
            
            all_responses.extend(query_responses)
            
            # Calculate query stats
            mention_count = sum(1 for r in query_responses if r.get("brand_mentioned", False))
            avg_score = sum(r.get("role_score", 0) for r in query_responses) / len(query_responses) * 100 if query_responses else 0
            
            query_results.append({
                "query_text": query_text,
                "query_type": query_type,
                "keyword": query.get("keyword", ""),
                "responses": query_responses[:3],  # Keep only first 3 for storage
                "avg_score": round(avg_score, 1),
                "mention_rate": round(mention_count / len(query_responses) * 100 if query_responses else 0, 1)
            })
            
            # Update progress
            await update_analysis(analysis_id, {
                "queries_processed": query_idx + 1,
                "queries_with_mention": sum(1 for r in all_responses if r.get("brand_mentioned", False))
            })
        
        # Calculate scores
        await update_analysis(analysis_id, {"current_phase": "calculating_indices"})
        
        # AI scores per engine
        ai_scores = {}
        for ai in ai_engines:
            ai_responses = [r for r in all_responses if r.get("ai_type") == ai and r.get("brand_mentioned")]
            if ai_responses:
                ai_scores[ai] = round(sum(r.get("role_score", 0) for r in ai_responses) / len(ai_responses) * 100, 1)
            else:
                ai_scores[ai] = 0
        
        # R.A.T.E. scores
        rate_scores = calculate_rate_score(all_responses)
        
        # Recommendations
        recommendations = generate_recommendations(rate_scores)
        
        # Mention rate
        mentioned_count = sum(1 for r in all_responses if r.get("brand_mentioned", False))
        mention_rate = round(mentioned_count / len(all_responses) * 100 if all_responses else 0, 1)
        
        logger.info(f"Analysis complete: Score={rate_scores['total']}, Grade={rate_scores['grade']}")
        
        # Calculate total API calls made
        total_api_calls = len(all_responses)
        
        # Final update
        await update_analysis(analysis_id, {
            "status": "completed",
            "current_phase": "completed",
            "global_score": rate_scores["total"],
            "grade": rate_scores["grade"],
            "mention_rate": mention_rate,
            "ai_scores": ai_scores,
            "rate_scores": rate_scores,
            "query_scores": query_results,
            "recommendations": recommendations,
            "total_queries": total_queries,
            "queries_with_mention": mentioned_count,
            "ai_engines_used": ai_engines,
            "completed_at": datetime.now(timezone.utc)
        })
        
        # Update subscription usage
        user_id = project.get("user_id")
        if user_id:
            await update_subscription_usage(user_id, total_api_calls)
            
            # Send completion notification email
            await send_analysis_complete_notification(
                user_id=user_id,
                project_name=project.get("name", "Projet"),
                brand_name=brand_name,
                global_score=rate_scores["total"],
                grade=rate_scores["grade"],
                analysis_id=analysis_id,
                recommendations=recommendations
            )
        
        logger.info(f"Analysis {analysis_id} COMPLETED with score: {rate_scores['total']}")
        
    except Exception as e:
        logger.error(f"Analysis {analysis_id} failed: {e}")
        import traceback
        logger.error(traceback.format_exc())
        await update_analysis(analysis_id, {
            "status": "failed",
            "current_phase": "failed",
            "error_message": str(e),
            "completed_at": datetime.now(timezone.utc)
        })
