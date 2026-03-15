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
from ..db.models import Analysis, Project, Subscription

logger = logging.getLogger(__name__)

# Query templates for different intent types
QUERY_TEMPLATES = {
    "transactional": [
        "Quel est le meilleur {keyword} pour {industry}?",
        "Je cherche un {keyword} fiable, que recommandez-vous?",
    ],
    "comparative": [
        "Comparez les meilleures solutions de {keyword}",
        "{brand} vs ses concurrents pour {keyword}",
    ],
    "informational": [
        "Comment fonctionne {keyword}?",
        "Les avantages de {keyword} pour une entreprise",
    ],
    "commercial": [
        "Avis sur {brand} pour {keyword}",
        "Est-ce que {brand} est recommandé pour {keyword}?",
    ],
}


async def update_analysis(analysis_id: str, updates: dict):
    """Update analysis record in PostgreSQL"""
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
                logger.info(f"Updating analysis {analysis_id}: {list(valid_updates.keys())}")
                await db.execute(
                    update(Analysis).where(
                        Analysis.analysis_id == analysis_id
                    ).values(**valid_updates)
                )
                await db.commit()
    except Exception as e:
        logger.error(f"Error updating analysis {analysis_id}: {e}")
        import traceback
        logger.error(traceback.format_exc())


def generate_queries(brand_name: str, keywords: List[str], num_queries: int, industry: str = "") -> List[Dict[str, Any]]:
    """Generate diverse queries for GEO analysis - full precision"""
    queries = []
    
    if not keywords:
        keywords = [brand_name]
    
    # Ensure we generate enough queries across all types
    query_types = list(QUERY_TEMPLATES.keys())
    queries_per_type = max(1, num_queries // len(query_types))
    
    for query_type in query_types:
        templates = QUERY_TEMPLATES[query_type]
        for i in range(queries_per_type):
            if len(queries) >= num_queries:
                break
            template = templates[i % len(templates)]
            keyword = keywords[i % len(keywords)] if keywords else brand_name
            query_text = template.format(
                keyword=keyword,
                brand=brand_name,
                industry=industry or "ce secteur"
            )
            queries.append({
                "text": query_text,
                "type": query_type,
                "keyword": keyword
            })
    
    # Fill remaining with random types if needed
    while len(queries) < num_queries:
        query_type = random.choice(query_types)
        templates = QUERY_TEMPLATES[query_type]
        template = random.choice(templates)
        keyword = random.choice(keywords) if keywords else brand_name
        query_text = template.format(
            keyword=keyword,
            brand=brand_name,
            industry=industry or "ce secteur"
        )
        queries.append({
            "text": query_text,
            "type": query_type,
            "keyword": keyword
        })
    
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
