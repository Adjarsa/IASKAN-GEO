"""
Analysis Runner Service - PostgreSQL Version with Real LLM Integration
IAskan Verified GEO Protocol™ v2.1
"""
import asyncio
import logging
import random
from datetime import datetime, timezone
from typing import Dict, Any, List

from sqlalchemy import select, update
from ..db.database import async_session_maker
from ..db.models import Analysis, Project, Subscription

from .llm_connector import LLMConnector, LLM_CONFIG

logger = logging.getLogger(__name__)

# Query templates for different intent types
QUERY_TEMPLATES = {
    "transactional": [
        "Quel est le meilleur {keyword} pour {industry}?",
        "Je cherche un {keyword} fiable, que recommandez-vous?",
        "Quelle solution de {keyword} choisir?",
    ],
    "comparative": [
        "Comparez les meilleures solutions de {keyword}",
        "Quels sont les leaders du marché en {keyword}?",
        "{brand} vs ses concurrents pour {keyword}",
    ],
    "informational": [
        "Comment fonctionne {keyword}?",
        "Qu'est-ce que {keyword} et pourquoi c'est important?",
        "Les avantages de {keyword} pour une entreprise",
    ],
    "commercial": [
        "Avis sur {brand} pour {keyword}",
        "Est-ce que {brand} est recommandé pour {keyword}?",
        "Retours d'expérience sur {brand}",
    ],
}

# Query type distribution for balanced analysis
QUERY_TYPE_DISTRIBUTION = {
    "transactional": 0.30,
    "comparative": 0.25,
    "informational": 0.25,
    "commercial": 0.20,
}


async def update_analysis(analysis_id: str, updates: dict):
    """Update analysis record in PostgreSQL"""
    try:
        async with async_session_maker() as db:
            # Filter out None values and invalid columns
            valid_updates = {k: v for k, v in updates.items() if v is not None}
            
            await db.execute(
                update(Analysis).where(
                    Analysis.analysis_id == analysis_id
                ).values(**valid_updates)
            )
            await db.commit()
    except Exception as e:
        logger.error(f"Error updating analysis {analysis_id}: {e}")


def generate_queries(brand_name: str, keywords: List[str], competitors: List[str], num_queries: int, industry: str = "") -> List[Dict[str, Any]]:
    """Generate diverse queries for GEO analysis"""
    queries = []
    
    if not keywords:
        keywords = [brand_name]
    
    for query_type, ratio in QUERY_TYPE_DISTRIBUTION.items():
        count = max(1, int(num_queries * ratio))
        templates = QUERY_TEMPLATES.get(query_type, QUERY_TEMPLATES["transactional"])
        
        for i in range(count):
            keyword = keywords[i % len(keywords)] if keywords else brand_name
            template = templates[i % len(templates)]
            
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
    mention_rate = mentioned / len(valid_responses)
    avg_position_ratio = sum(r.get("position_ratio", 1) for r in valid_responses if r.get("brand_mentioned")) / max(1, mentioned)
    position_score = max(0, 100 - (avg_position_ratio * 100))
    relevance = (mention_rate * 60) + (position_score * 0.4)
    
    # Authority: Based on role scores
    role_scores = [r.get("role_score", 0) for r in valid_responses if r.get("brand_mentioned")]
    authority = (sum(role_scores) / len(role_scores) * 100) if role_scores else 0
    
    # Truthfulness: Based on credibility scores
    cred_scores = [r.get("credibility_score", 50) for r in valid_responses if r.get("brand_mentioned")]
    truthfulness = (sum(cred_scores) / len(cred_scores)) if cred_scores else 50
    
    # Endorsement: Based on conversion scores and top recommendations
    conv_scores = [r.get("conversion_score", 0) for r in valid_responses if r.get("brand_mentioned")]
    top_recs = sum(1 for r in valid_responses if r.get("role") == "top_recommendation")
    endorsement = ((sum(conv_scores) / len(conv_scores)) if conv_scores else 0) + (top_recs * 10)
    endorsement = min(100, endorsement)
    
    # Total weighted score
    total = (relevance * 0.30) + (authority * 0.25) + (truthfulness * 0.20) + (endorsement * 0.25)
    
    # Determine grade
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


def generate_recommendations(rate_scores: Dict[str, Any], ai_scores: Dict[str, float]) -> List[Dict[str, Any]]:
    """Generate actionable recommendations based on analysis"""
    recommendations = []
    
    # Low relevance recommendations
    if rate_scores.get("relevance", 0) < 50:
        recommendations.append({
            "priority": "critical",
            "category": "content",
            "title": "Améliorer la visibilité de marque",
            "description": "Votre marque n'est pas suffisamment mentionnée par les IA. Créez du contenu optimisé pour être cité.",
            "impact": "critique",
            "effort": "moyen",
            "metrics_impacted": ["relevance", "mention_rate"]
        })
    
    # Low authority recommendations
    if rate_scores.get("authority", 0) < 50:
        recommendations.append({
            "priority": "high",
            "category": "authority",
            "title": "Renforcer l'autorité de marque",
            "description": "Positionnez-vous comme leader en créant du contenu expert et en obtenant des backlinks de qualité.",
            "impact": "eleve",
            "effort": "eleve",
            "metrics_impacted": ["authority", "role_score"]
        })
    
    # Low endorsement recommendations
    if rate_scores.get("endorsement", 0) < 50:
        recommendations.append({
            "priority": "medium",
            "category": "engagement",
            "title": "Augmenter les signaux de confiance",
            "description": "Ajoutez des témoignages, avis clients et certifications sur votre site.",
            "impact": "moyen",
            "effort": "faible",
            "metrics_impacted": ["endorsement", "conversion_score"]
        })
    
    # AI-specific recommendations
    for ai_name, score in ai_scores.items():
        if score < 40:
            recommendations.append({
                "priority": "medium",
                "category": "technical",
                "title": f"Optimiser pour {ai_name.title()}",
                "description": f"Votre visibilité sur {ai_name.title()} est faible ({score}/100). Adaptez votre contenu.",
                "impact": "moyen",
                "effort": "moyen",
                "metrics_impacted": [f"{ai_name}_score"]
            })
    
    # Default recommendation if none generated
    if not recommendations:
        recommendations.append({
            "priority": "low",
            "category": "optimization",
            "title": "Maintenir et améliorer",
            "description": "Vos scores sont bons. Continuez à produire du contenu de qualité et surveillez l'évolution.",
            "impact": "faible",
            "effort": "faible",
            "metrics_impacted": ["all"]
        })
    
    return recommendations


async def run_analysis_simplified(analysis_id: str, project: dict, plan_config: dict):
    """
    IAskan Verified GEO Protocol™ Analysis Engine
    PostgreSQL-compatible version with REAL LLM integration
    """
    try:
        brand_name = project.get("brand_name", "")
        keywords = project.get("keywords", [])
        competitors = project.get("competitors", [])
        industry = project.get("industry", "")
        
        ai_engines = plan_config.get("ai_engines", ["chatgpt"])
        num_prompts = plan_config.get("num_prompts", 10)
        runs_per_query = plan_config.get("runs_per_query", 1)
        
        if not brand_name:
            raise ValueError("Nom de marque requis")
        
        logger.info(f"Starting REAL analysis {analysis_id} for brand: {brand_name}")
        logger.info(f"Config: {num_prompts} queries × {runs_per_query} runs × {len(ai_engines)} AIs")
        
        # Update status to running
        await update_analysis(analysis_id, {
            "status": "running",
            "started_at": datetime.now(timezone.utc)
        })
        
        # Initialize LLM Connector
        llm_connector = LLMConnector()
        
        # Generate queries
        queries = generate_queries(brand_name, keywords, competitors, num_prompts, industry)
        total_api_calls = len(queries) * len(ai_engines) * runs_per_query
        
        logger.info(f"Generated {len(queries)} queries, total API calls: {total_api_calls}")
        
        # Store all responses
        all_responses = []
        query_results = []
        ai_scores_raw = {ai: [] for ai in ai_engines}
        
        # Process each query
        for query_idx, query in enumerate(queries):
            query_text = query["text"]
            query_type = query["type"]
            
            logger.info(f"Processing query {query_idx + 1}/{len(queries)}: {query_text[:50]}...")
            
            query_responses = []
            
            # Query each AI engine
            for run_id in range(1, runs_per_query + 1):
                for ai_type in ai_engines:
                    try:
                        response = await llm_connector.query_llm(
                            query_text=query_text,
                            ai_type=ai_type,
                            run_id=run_id,
                            brand_name=brand_name,
                            competitors=competitors
                        )
                        
                        query_responses.append(response)
                        all_responses.append(response)
                        
                        # Track AI-specific score
                        if response.get("brand_mentioned"):
                            ai_scores_raw[ai_type].append(response.get("role_score", 0) * 100)
                        else:
                            ai_scores_raw[ai_type].append(0)
                        
                        # Small delay to avoid rate limiting
                        await asyncio.sleep(0.5)
                        
                    except Exception as e:
                        logger.error(f"Error querying {ai_type} for query {query_idx}: {e}")
                        query_responses.append({
                            "ai_type": ai_type,
                            "error": str(e),
                            "brand_mentioned": False
                        })
            
            # Aggregate query results
            mention_count = sum(1 for r in query_responses if r.get("brand_mentioned", False))
            avg_score = sum(r.get("role_score", 0) for r in query_responses) / len(query_responses) * 100 if query_responses else 0
            
            query_results.append({
                "query_text": query_text,
                "query_type": query_type,
                "keyword": query.get("keyword", ""),
                "responses": query_responses,
                "avg_score": round(avg_score, 1),
                "mention_rate": round(mention_count / len(query_responses) * 100 if query_responses else 0, 1)
            })
            
            # Update progress
            await update_analysis(analysis_id, {
                "queries_with_mention": sum(1 for r in all_responses if r.get("brand_mentioned", False)),
                "total_queries": len(queries)
            })
        
        # Calculate final scores
        ai_scores = {}
        for ai, scores in ai_scores_raw.items():
            ai_scores[ai] = round(sum(scores) / len(scores), 1) if scores else 0
        
        # Calculate R.A.T.E. scores
        rate_scores = calculate_rate_score(all_responses)
        
        # Generate recommendations
        recommendations = generate_recommendations(rate_scores, ai_scores)
        
        # Calculate mention statistics
        mentioned_responses = [r for r in all_responses if r.get("brand_mentioned", False)]
        mention_rate = len(mentioned_responses) / len(all_responses) * 100 if all_responses else 0
        
        logger.info(f"Analysis complete: Score={rate_scores['total']}, Grade={rate_scores['grade']}, Mention Rate={mention_rate:.1f}%")
        
        # Update analysis with final results
        await update_analysis(analysis_id, {
            "status": "completed",
            "global_score": rate_scores["total"],
            "grade": rate_scores["grade"],
            "mention_rate": round(mention_rate, 1),
            "ai_scores": ai_scores,
            "rate_scores": rate_scores,
            "query_scores": query_results,
            "recommendations": recommendations,
            "total_queries": len(queries),
            "queries_with_mention": len(mentioned_responses),
            "ai_engines_used": ai_engines,
            "completed_at": datetime.now(timezone.utc)
        })
        
        logger.info(f"Analysis {analysis_id} COMPLETED with score: {rate_scores['total']}")
        
    except Exception as e:
        logger.error(f"Analysis {analysis_id} failed: {e}")
        await update_analysis(analysis_id, {
            "status": "failed",
            "error_message": str(e),
            "completed_at": datetime.now(timezone.utc)
        })
