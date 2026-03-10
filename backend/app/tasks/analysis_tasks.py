"""
Analysis Tasks for Celery
Distributed analysis pipeline for IAskan GEO Platform
"""
import asyncio
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any, Optional
from celery import shared_task, chain, group, chord
from celery.exceptions import SoftTimeLimitExceeded

from ..celery_config import celery_app
from ..db.database import async_session_maker
from ..db.services import (
    ProjectService, AnalysisService, SubscriptionService, 
    NotificationService, ScheduleService, UserService
)
from ..db.models import AnalysisStatus
from ..core.config import EMERGENT_LLM_KEY, SUBSCRIPTION_PLANS

logger = logging.getLogger(__name__)


def run_async(coro):
    """Helper to run async code in sync Celery tasks"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


# ================== LLM QUERY TASKS ==================

@celery_app.task(bind=True, max_retries=3, default_retry_delay=30)
def query_single_llm(self, llm_provider: str, query: str, brand_name: str, context: dict = None) -> dict:
    """
    Query a single LLM and return the response with brand analysis
    
    Args:
        llm_provider: 'chatgpt', 'claude', or 'gemini'
        query: The query to send to the LLM
        brand_name: The brand to look for in the response
        context: Additional context (competitors, keywords, etc.)
    
    Returns:
        dict with response, brand_mentioned, position, etc.
    """
    try:
        from emergentintegrations.llm.chat import LlmChat, UserMessage
        
        # Map provider to model
        model_map = {
            'chatgpt': 'gpt-4o',
            'claude': 'claude-sonnet-4-20250514',
            'gemini': 'gemini-2.0-flash'
        }
        
        model = model_map.get(llm_provider, 'gpt-4o')
        
        chat = LlmChat(
            api_key=EMERGENT_LLM_KEY,
            model=model,
            suppress_print=True
        )
        
        response = chat.send_message(UserMessage(content=query))
        response_text = response.content if hasattr(response, 'content') else str(response)
        
        # Analyze response for brand mentions
        brand_mentioned = brand_name.lower() in response_text.lower() if brand_name else False
        
        # Find position if mentioned
        position = None
        if brand_mentioned:
            lines = response_text.split('\n')
            for i, line in enumerate(lines):
                if brand_name.lower() in line.lower():
                    position = i + 1
                    break
        
        # Check competitors if provided
        competitors_mentioned = []
        if context and context.get('competitors'):
            for competitor in context['competitors']:
                if competitor.lower() in response_text.lower():
                    competitors_mentioned.append(competitor)
        
        return {
            'provider': llm_provider,
            'query': query,
            'response': response_text[:2000],  # Truncate for storage
            'brand_mentioned': brand_mentioned,
            'position': position,
            'competitors_mentioned': competitors_mentioned,
            'response_length': len(response_text),
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
        
    except SoftTimeLimitExceeded:
        logger.warning(f"LLM query timeout for {llm_provider}: {query[:50]}...")
        return {
            'provider': llm_provider,
            'query': query,
            'error': 'timeout',
            'brand_mentioned': False
        }
    except Exception as e:
        logger.error(f"LLM query error for {llm_provider}: {e}")
        # Retry on failure
        try:
            self.retry(exc=e)
        except self.MaxRetriesExceededError:
            return {
                'provider': llm_provider,
                'query': query,
                'error': str(e),
                'brand_mentioned': False
            }


@celery_app.task(bind=True)
def query_all_llms(self, query: str, brand_name: str, context: dict = None) -> List[dict]:
    """Query all LLMs in parallel using Celery group"""
    providers = ['chatgpt', 'claude', 'gemini']
    
    # Create a group of tasks
    job = group(
        query_single_llm.s(provider, query, brand_name, context)
        for provider in providers
    )
    
    # Execute and wait for results
    result = job.apply_async()
    results = result.get(timeout=120)  # Wait up to 2 minutes
    
    return results


# ================== ANALYSIS PIPELINE TASKS ==================

@celery_app.task(bind=True, max_retries=2)
def run_full_analysis(self, analysis_id: str, project_id: str, user_id: str) -> dict:
    """
    Run a complete GEO analysis for a project
    
    This is the main entry point for the analysis pipeline.
    It orchestrates the entire analysis process:
    1. Generate queries based on project keywords
    2. Query all LLMs for each query
    3. Analyze responses and calculate scores
    4. Store results and send notifications
    """
    logger.info(f"Starting analysis {analysis_id} for project {project_id}")
    
    async def _run_analysis():
        async with async_session_maker() as db:
            # Update status to running
            await AnalysisService.update(
                db, analysis_id,
                status=AnalysisStatus.RUNNING,
                started_at=datetime.now(timezone.utc)
            )
            
            # Get project details
            project = await ProjectService.get_by_id(db, project_id)
            if not project:
                raise Exception(f"Project {project_id} not found")
            
            brand_name = project.brand_name or project.name
            keywords = project.keywords or []
            competitors = project.competitors or []
            
            # Generate queries
            queries = generate_analysis_queries(brand_name, keywords, project.industry)
            
            # Context for LLM queries
            context = {
                'competitors': competitors,
                'keywords': keywords,
                'industry': project.industry
            }
            
            # Query LLMs for each query
            all_results = []
            for query in queries[:10]:  # Limit to 10 queries
                try:
                    results = query_all_llms.delay(query, brand_name, context).get(timeout=180)
                    all_results.append({
                        'query': query,
                        'results': results
                    })
                except Exception as e:
                    logger.error(f"Error querying LLMs for '{query}': {e}")
                    all_results.append({
                        'query': query,
                        'results': [],
                        'error': str(e)
                    })
            
            # Calculate scores
            scores = calculate_geo_scores(all_results, brand_name, competitors)
            
            # Update analysis with results
            await AnalysisService.update(
                db, analysis_id,
                status=AnalysisStatus.COMPLETED,
                completed_at=datetime.now(timezone.utc),
                global_score=scores['global_score'],
                grade=scores['grade'],
                ai_scores=scores['ai_scores'],
                rate_scores=scores['rate_scores'],
                query_scores=scores['query_scores'],
                competitor_analysis=scores['competitor_analysis'],
                recommendations=scores['recommendations'],
                total_queries=len(queries),
                queries_with_mention=scores['queries_with_mention'],
                mention_rate=scores['mention_rate'],
                average_position=scores['average_position'],
                ai_engines_used=['chatgpt', 'claude', 'gemini']
            )
            
            # Create notification
            await NotificationService.create(
                db, user_id,
                type='analysis_complete',
                title='Analyse terminée',
                message=f"L'analyse de {project.name} est terminée. Score: {scores['global_score']}/100",
                data={
                    'analysis_id': analysis_id,
                    'project_id': project_id,
                    'score': scores['global_score']
                }
            )
            
            # Update subscription usage
            subscription = await SubscriptionService.get_by_user_id(db, user_id)
            if subscription:
                await SubscriptionService.update(
                    db, user_id,
                    scans_used=(subscription.scans_used or 0) + 1
                )
            
            return {
                'analysis_id': analysis_id,
                'status': 'completed',
                'global_score': scores['global_score'],
                'grade': scores['grade']
            }
    
    try:
        result = run_async(_run_analysis())
        logger.info(f"Analysis {analysis_id} completed with score {result.get('global_score')}")
        return result
        
    except Exception as e:
        logger.error(f"Analysis {analysis_id} failed: {e}")
        
        # Update status to failed
        async def _mark_failed():
            async with async_session_maker() as db:
                await AnalysisService.update(
                    db, analysis_id,
                    status=AnalysisStatus.FAILED,
                    error_message=str(e),
                    completed_at=datetime.now(timezone.utc)
                )
        
        run_async(_mark_failed())
        
        return {
            'analysis_id': analysis_id,
            'status': 'failed',
            'error': str(e)
        }


def generate_analysis_queries(brand_name: str, keywords: List[str], industry: str = None) -> List[str]:
    """Generate analysis queries based on brand and keywords"""
    queries = []
    
    # Base queries
    base_templates = [
        f"Quels sont les meilleurs {industry or 'services'} en France ?",
        f"Recommandez-moi une solution de {industry or 'service'} fiable",
        f"Quelle est la meilleure alternative à {brand_name} ?",
        f"Comparatif des solutions de {industry or 'service'} en 2026",
        f"Avis sur {brand_name}",
    ]
    queries.extend(base_templates)
    
    # Keyword-based queries
    for keyword in keywords[:5]:
        queries.append(f"Quelle est la meilleure solution pour {keyword} ?")
        queries.append(f"{keyword} : quelles sont les meilleures options ?")
    
    return queries[:15]  # Limit total queries


def calculate_geo_scores(results: List[dict], brand_name: str, competitors: List[str]) -> dict:
    """Calculate GEO scores from LLM results"""
    total_queries = len(results)
    queries_with_mention = 0
    positions = []
    
    ai_scores = {'chatgpt': 0, 'claude': 0, 'gemini': 0}
    ai_mentions = {'chatgpt': 0, 'claude': 0, 'gemini': 0}
    
    competitor_mentions = {c: 0 for c in competitors}
    query_scores = []
    
    for query_result in results:
        query = query_result.get('query', '')
        llm_results = query_result.get('results', [])
        
        query_mentioned = False
        query_positions = []
        
        for result in llm_results:
            provider = result.get('provider', '')
            mentioned = result.get('brand_mentioned', False)
            position = result.get('position')
            
            if provider in ai_mentions:
                if mentioned:
                    ai_mentions[provider] += 1
                    query_mentioned = True
                    if position:
                        query_positions.append(position)
                
                # Check competitor mentions
                for comp in result.get('competitors_mentioned', []):
                    if comp in competitor_mentions:
                        competitor_mentions[comp] += 1
        
        if query_mentioned:
            queries_with_mention += 1
            if query_positions:
                positions.extend(query_positions)
        
        # Calculate query score
        query_score = len([r for r in llm_results if r.get('brand_mentioned')]) / max(len(llm_results), 1) * 100
        query_scores.append({
            'query': query,
            'score': round(query_score, 1),
            'mentioned': query_mentioned,
            'position': min(query_positions) if query_positions else None
        })
    
    # Calculate AI scores
    for provider in ai_scores:
        if total_queries > 0:
            ai_scores[provider] = round(ai_mentions[provider] / total_queries * 100, 1)
    
    # Calculate mention rate
    mention_rate = queries_with_mention / max(total_queries, 1) * 100
    
    # Calculate average position
    avg_position = sum(positions) / len(positions) if positions else None
    
    # Calculate global score (weighted average)
    global_score = round(
        (ai_scores['chatgpt'] * 0.4 + ai_scores['claude'] * 0.35 + ai_scores['gemini'] * 0.25),
        1
    )
    
    # Determine grade
    if global_score >= 80:
        grade = 'A'
    elif global_score >= 60:
        grade = 'B'
    elif global_score >= 40:
        grade = 'C'
    elif global_score >= 20:
        grade = 'D'
    else:
        grade = 'F'
    
    # Generate recommendations
    recommendations = generate_recommendations(global_score, ai_scores, mention_rate, competitor_mentions)
    
    return {
        'global_score': global_score,
        'grade': grade,
        'ai_scores': ai_scores,
        'rate_scores': {
            'relevance': round(mention_rate, 1),
            'authority': round(global_score * 0.9, 1),
            'trust': round(global_score * 0.85, 1),
            'engagement': round(mention_rate * 0.8, 1)
        },
        'query_scores': query_scores,
        'competitor_analysis': competitor_mentions,
        'recommendations': recommendations,
        'queries_with_mention': queries_with_mention,
        'mention_rate': round(mention_rate, 1),
        'average_position': round(avg_position, 1) if avg_position else None
    }


def generate_recommendations(score: float, ai_scores: dict, mention_rate: float, competitors: dict) -> List[dict]:
    """Generate actionable recommendations based on scores"""
    recommendations = []
    
    if score < 50:
        recommendations.append({
            'priority': 'high',
            'category': 'visibility',
            'title': 'Améliorer la visibilité IA',
            'description': 'Votre marque a une faible visibilité dans les réponses IA. Concentrez-vous sur la création de contenu autoritaire.',
            'actions': [
                'Créer des articles de blog optimisés pour les requêtes courantes',
                'Obtenir des mentions sur des sites autoritaires',
                'Développer une présence sur les plateformes de reviews'
            ]
        })
    
    # Check individual AI scores
    for provider, provider_score in ai_scores.items():
        if provider_score < 30:
            recommendations.append({
                'priority': 'medium',
                'category': 'ai_optimization',
                'title': f'Optimiser pour {provider.title()}',
                'description': f'Score faible sur {provider.title()} ({provider_score}%). Adaptez votre contenu.',
                'actions': [
                    f'Analyser les sources préférées de {provider.title()}',
                    'Structurer le contenu avec des listes et tableaux',
                    'Ajouter des données chiffrées et citations'
                ]
            })
    
    if mention_rate < 40:
        recommendations.append({
            'priority': 'high',
            'category': 'content',
            'title': 'Augmenter le taux de mention',
            'description': f'Taux de mention de {mention_rate}%. Diversifiez vos mots-clés et contenus.',
            'actions': [
                'Identifier les requêtes où vous n\'apparaissez pas',
                'Créer du contenu ciblé pour ces requêtes',
                'Optimiser les balises et métadonnées'
            ]
        })
    
    # Competitor analysis
    top_competitor = max(competitors.items(), key=lambda x: x[1], default=(None, 0))
    if top_competitor[0] and top_competitor[1] > 0:
        recommendations.append({
            'priority': 'medium',
            'category': 'competitive',
            'title': f'Analyser {top_competitor[0]}',
            'description': f'{top_competitor[0]} apparaît fréquemment. Analysez leur stratégie.',
            'actions': [
                f'Étudier le contenu de {top_competitor[0]}',
                'Identifier leurs sources de citations',
                'Développer des différenciateurs clairs'
            ]
        })
    
    return recommendations


# ================== SCHEDULED SCANS TASK ==================

@celery_app.task
def check_scheduled_scans_task():
    """Check and execute scheduled scans (runs every minute via Celery Beat)"""
    logger.info("Checking scheduled scans...")
    
    async def _check_schedules():
        async with async_session_maker() as db:
            from sqlalchemy import select, and_
            from ..db.models import ScanSchedule
            
            now = datetime.now(timezone.utc)
            
            # Find schedules that need to run
            result = await db.execute(
                select(ScanSchedule).where(
                    and_(
                        ScanSchedule.enabled == True,
                        ScanSchedule.next_run <= now
                    )
                )
            )
            schedules = result.scalars().all()
            
            for schedule in schedules:
                logger.info(f"Running scheduled scan for project {schedule.project_id}")
                
                # Create analysis
                analysis = await AnalysisService.create(
                    db, schedule.project_id, schedule.user_id
                )
                
                # Queue the analysis task
                run_full_analysis.delay(
                    analysis.analysis_id,
                    schedule.project_id,
                    schedule.user_id
                )
                
                # Update next run time
                next_run = calculate_next_run(schedule.frequency, schedule.hour, schedule.minute, schedule.day_of_week)
                await ScheduleService.update(
                    db, schedule.schedule_id,
                    last_run=now,
                    next_run=next_run
                )
            
            return len(schedules)
    
    count = run_async(_check_schedules())
    logger.info(f"Triggered {count} scheduled scans")
    return count


def calculate_next_run(frequency: str, hour: int, minute: int, day_of_week: int = None) -> datetime:
    """Calculate next run time based on frequency"""
    now = datetime.now(timezone.utc)
    
    if frequency == 'daily':
        next_run = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        if next_run <= now:
            next_run += timedelta(days=1)
    
    elif frequency == 'weekly':
        days_ahead = day_of_week - now.weekday() if day_of_week else 0
        if days_ahead <= 0:
            days_ahead += 7
        next_run = now.replace(hour=hour, minute=minute, second=0, microsecond=0) + timedelta(days=days_ahead)
    
    elif frequency == 'biweekly':
        next_run = now.replace(hour=hour, minute=minute, second=0, microsecond=0) + timedelta(days=14)
    
    elif frequency == 'monthly':
        next_month = now.replace(day=1) + timedelta(days=32)
        next_run = next_month.replace(day=1, hour=hour, minute=minute, second=0, microsecond=0)
    
    else:
        next_run = now + timedelta(days=7)  # Default to weekly
    
    return next_run
