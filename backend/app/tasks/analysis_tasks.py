"""
Analysis Tasks for Celery
Distributed analysis pipeline for IAskan GEO Platform

This module implements the complete GEO analysis pipeline using Celery
for distributed task execution. It uses the modular services:
- LLMConnector: For querying multiple LLM providers
- GEOScoringEngine: For calculating GEO scores
- CompetitiveIntelligenceEngine: For competitor analysis
- QueryGenerationEngine: For generating analysis queries
"""
import asyncio
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any, Optional

from ..celery_config import celery_app
from ..db.database import async_session_maker
from ..db.services import (
    ProjectService, AnalysisService, SubscriptionService, 
    NotificationService, ScheduleService, UserService
)
from ..db.models import AnalysisStatus
from ..core.config import EMERGENT_LLM_KEY, SUBSCRIPTION_PLANS

# Import modular engines and services
from ..services.llm_connector import LLMConnector
from ..services.geo_scoring import GEOScoringEngine
from ..services.competitive_intelligence import CompetitiveIntelligenceEngine
from ..engines.query.generator import QueryGenerationEngine
from ..engines.query.variation import PromptVariationEngine
from ..engines.semantic.analyzer import SemanticAnalysisEngine
from ..engines.gap.finder import ContentGapEngine

logger = logging.getLogger(__name__)


def run_async(coro):
    """Helper to run async code in sync Celery tasks"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


# Initialize service instances
llm_connector = LLMConnector(api_key=EMERGENT_LLM_KEY)
geo_scoring = GEOScoringEngine()
competitive_intel = CompetitiveIntelligenceEngine()
query_generator = QueryGenerationEngine()
variation_engine = PromptVariationEngine()
semantic_analyzer = SemanticAnalysisEngine()
gap_finder = ContentGapEngine()


# ================== LLM QUERY TASKS ==================

@celery_app.task(bind=True, max_retries=3, default_retry_delay=30)
def query_single_llm(
    self,
    llm_provider: str,
    query: str,
    brand_name: str,
    context: dict = None
) -> dict:
    """
    Query a single LLM and return the response with brand analysis.
    
    Args:
        llm_provider: 'chatgpt', 'claude', or 'gemini'
        query: The query to send to the LLM
        brand_name: The brand to look for in the response
        context: Additional context (competitors, keywords, etc.)
    
    Returns:
        Dict with response, brand_mentioned, position, etc.
    """
    context = context or {}
    competitors = context.get('competitors', [])
    
    try:
        # Use async connector
        async def _query():
            return await llm_connector.query_llm(
                query_text=query,
                ai_type=llm_provider,
                run_id=context.get('run_id', 1),
                brand_name=brand_name,
                competitors=competitors
            )
        
        result = run_async(_query())
        return result
        
    except Exception as e:
        logger.error(f"LLM query error for {llm_provider}: {e}")
        try:
            self.retry(exc=e)
        except self.MaxRetriesExceededError:
            return {
                'provider': llm_provider,
                'query': query,
                'error': str(e),
                'brand_mentioned': False,
                'role': 'error'
            }


@celery_app.task(bind=True)
def query_all_llms_task(
    self,
    query: str,
    brand_name: str,
    context: dict = None
) -> List[dict]:
    """Query all LLMs in parallel for a single query"""
    context = context or {}
    competitors = context.get('competitors', [])
    ai_types = context.get('ai_types', ['chatgpt', 'claude', 'gemini'])
    run_id = context.get('run_id', 1)
    
    async def _query_all():
        return await llm_connector.query_all_llms(
            query_text=query,
            brand_name=brand_name,
            competitors=competitors,
            ai_types=ai_types,
            run_id=run_id
        )
    
    return run_async(_query_all())


# ================== MAIN ANALYSIS PIPELINE ==================

@celery_app.task(bind=True, max_retries=2, soft_time_limit=600, time_limit=660)
def run_full_analysis(
    self,
    analysis_id: str,
    project_id: str,
    user_id: str
) -> dict:
    """
    Run a complete GEO analysis for a project.
    
    This is the main entry point for the analysis pipeline.
    It orchestrates the entire analysis process:
    1. Generate queries based on project keywords
    2. Query all LLMs for each query (with variations for stability)
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
            industry = project.industry
            
            # Get subscription for plan config
            subscription = await SubscriptionService.get_by_user_id(db, user_id)
            plan = subscription.plan.value if subscription else "free"
            plan_config = SUBSCRIPTION_PLANS.get(plan, SUBSCRIPTION_PLANS["free"])
            
            # Determine AI engines to use based on plan
            ai_engines = plan_config.get("ai_engines", ["chatgpt"])
            num_prompts = plan_config.get("num_prompts", 30)
            runs_per_query = plan_config.get("runs_per_query", 3)
            
            logger.info(f"Running analysis with {len(ai_engines)} AI engines, {num_prompts} prompts, {runs_per_query} runs")
            
            # ===== PHASE 1: QUERY GENERATION =====
            await AnalysisService.update(db, analysis_id, current_phase="query_generation")
            
            queries = query_generator.generate_queries(
                brand_name=brand_name,
                keywords=keywords,
                competitors=competitors,
                num_queries=num_prompts,
                industry=industry
            )
            
            # Add variations for multi-run stability
            if runs_per_query > 1:
                queries = variation_engine.generate_variations(
                    queries,
                    max_variations_per_query=runs_per_query - 1
                )
            
            logger.info(f"Generated {len(queries)} queries (with variations)")
            
            # ===== PHASE 2: LLM QUERYING =====
            await AnalysisService.update(db, analysis_id, current_phase="ai_querying")
            
            all_responses = []
            run_id = 1
            
            # Process queries in batches to avoid overwhelming LLMs
            batch_size = 5
            for i in range(0, min(len(queries), num_prompts), batch_size):
                batch = queries[i:i + batch_size]
                
                for query_data in batch:
                    query_text = query_data.get("text", "")
                    
                    try:
                        # Query all configured AI engines
                        responses = await llm_connector.query_all_llms(
                            query_text=query_text,
                            brand_name=brand_name,
                            competitors=competitors,
                            ai_types=ai_engines,
                            run_id=run_id
                        )
                        
                        for resp in responses:
                            resp["query_data"] = {
                                "text": query_text,
                                "intent_type": query_data.get("intent_type", "informational"),
                                "variation_type": query_data.get("variation_type", "original")
                            }
                            all_responses.append(resp)
                        
                        run_id += 1
                        
                    except Exception as e:
                        logger.error(f"Error querying LLMs for '{query_text[:50]}...': {e}")
                        # Add error response to track failures
                        all_responses.append({
                            "query_text": query_text,
                            "error": str(e),
                            "brand_mentioned": False,
                            "role": "error"
                        })
                
                # Small delay between batches to avoid rate limits
                await asyncio.sleep(0.5)
            
            logger.info(f"Collected {len(all_responses)} LLM responses")
            
            # ===== PHASE 3: SCORING & ANALYSIS =====
            await AnalysisService.update(db, analysis_id, current_phase="calculating_indices")
            
            # Calculate stability index
            stability_data = geo_scoring.calculate_stability_index(all_responses)
            
            # Calculate advanced indices
            indices = geo_scoring.calculate_advanced_indices(
                all_responses, brand_name, competitors
            )
            indices["stability_index"] = stability_data.get("stability_score", 100)
            
            # Calculate R.A.T.E. score
            rate_scores = geo_scoring.calculate_rate_score(all_responses, stability_data)
            
            # Calculate per-AI scores
            ai_scores = geo_scoring.calculate_ai_scores(all_responses)
            
            # Generate recommendations
            recommendations = geo_scoring.generate_recommendations(
                rate_scores, ai_scores, indices, stability_data
            )
            
            # ===== PHASE 4: COMPETITIVE INTELLIGENCE =====
            discovered_competitors = competitive_intel.identify_competitors(
                all_responses, brand_name, competitors
            )
            
            competitive_gap = competitive_intel.calculate_competitive_gap(
                all_responses, brand_name, competitors
            )
            
            # ===== PHASE 5: SEMANTIC ANALYSIS =====
            semantic_results = semantic_analyzer.analyze_batch(all_responses, brand_name)
            
            # ===== PHASE 6: CONTENT GAP ANALYSIS =====
            gap_analysis = gap_finder.analyze_gaps(
                queries,
                all_responses,
                brand_name,
                competitors
            )
            
            # ===== PHASE 7: COMPILE RESULTS =====
            global_score = rate_scores.get("total", 0)
            grade = rate_scores.get("grade", "F")
            
            # Build query scores summary
            query_scores = []
            for i, query in enumerate(queries[:num_prompts]):
                query_responses = [r for r in all_responses if r.get("query_data", {}).get("text") == query.get("text")]
                mentioned_count = sum(1 for r in query_responses if r.get("brand_mentioned", False))
                avg_score = sum(r.get("role_score", 0) for r in query_responses) / max(len(query_responses), 1)
                
                query_scores.append({
                    "query": query.get("text", "")[:100],
                    "intent_type": query.get("intent_type", "informational"),
                    "mentioned": mentioned_count > 0,
                    "mention_rate": round((mentioned_count / max(len(query_responses), 1)) * 100, 1),
                    "avg_score": round(avg_score * 100, 1)
                })
            
            # Update analysis with complete results
            await AnalysisService.update(
                db, analysis_id,
                status=AnalysisStatus.COMPLETED,
                completed_at=datetime.now(timezone.utc),
                global_score=global_score,
                grade=grade,
                ai_scores=ai_scores,
                rate_scores=rate_scores,
                query_scores=query_scores,
                indices=indices,
                stability_data=stability_data,
                recommendations=recommendations,
                competitor_analysis={
                    "discovered": discovered_competitors,
                    "gap_analysis": competitive_gap
                },
                semantic_analysis=semantic_results,
                content_gaps=gap_analysis,
                total_queries=len(queries),
                queries_with_mention=sum(1 for r in all_responses if r.get("brand_mentioned", False)),
                mention_rate=round(
                    sum(1 for r in all_responses if r.get("brand_mentioned", False)) / max(len(all_responses), 1) * 100,
                    1
                ),
                ai_engines_used=ai_engines,
                current_phase="completed"
            )
            
            # ===== PHASE 8: NOTIFICATIONS & CLEANUP =====
            # Create notification
            await NotificationService.create(
                db, user_id,
                type='analysis_complete',
                title='Analyse GEO terminée',
                message=f"L'analyse de {project.name} est terminée. Score: {global_score}/100 (Grade {grade})",
                data={
                    'analysis_id': analysis_id,
                    'project_id': project_id,
                    'score': global_score,
                    'grade': grade
                }
            )
            
            # Update subscription usage
            if subscription:
                await SubscriptionService.update(
                    db, user_id,
                    scans_used=(subscription.scans_used or 0) + 1
                )
            
            logger.info(f"Analysis {analysis_id} completed - Score: {global_score}, Grade: {grade}")
            
            return {
                'analysis_id': analysis_id,
                'status': 'completed',
                'global_score': global_score,
                'grade': grade,
                'queries_processed': len(queries),
                'responses_collected': len(all_responses)
            }
    
    try:
        result = run_async(_run_analysis())
        return result
        
    except Exception as exc:
        error_message = str(exc)
        logger.error(f"Analysis {analysis_id} failed: {error_message}")
        
        # Update status to failed
        async def _mark_failed(err_msg: str):
            async with async_session_maker() as db:
                await AnalysisService.update(
                    db, analysis_id,
                    status=AnalysisStatus.FAILED,
                    error_message=err_msg,
                    completed_at=datetime.now(timezone.utc),
                    current_phase="failed"
                )
        
        run_async(_mark_failed(error_message))
        
        return {
            'analysis_id': analysis_id,
            'status': 'failed',
            'error': error_message
        }


# ================== SCHEDULED SCANS ==================

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
                        ScanSchedule.enabled.is_(True),
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
                next_run = calculate_next_run(
                    schedule.frequency,
                    schedule.hour,
                    schedule.minute,
                    schedule.day_of_week
                )
                await ScheduleService.update(
                    db, schedule.schedule_id,
                    last_run=now,
                    next_run=next_run
                )
            
            return len(schedules)
    
    count = run_async(_check_schedules())
    logger.info(f"Triggered {count} scheduled scans")
    return count


def calculate_next_run(
    frequency: str,
    hour: int,
    minute: int,
    day_of_week: int = None
) -> datetime:
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


# ================== UTILITY TASKS ==================

@celery_app.task
def cleanup_old_analyses(days_old: int = 90):
    """Clean up old analysis data to save storage"""
    logger.info(f"Cleaning up analyses older than {days_old} days")
    
    async def _cleanup():
        async with async_session_maker() as db:
            from sqlalchemy import delete
            from ..db.models import Analysis
            
            cutoff = datetime.now(timezone.utc) - timedelta(days=days_old)
            
            result = await db.execute(
                delete(Analysis).where(Analysis.created_at < cutoff)
            )
            await db.commit()
            
            return result.rowcount
    
    deleted = run_async(_cleanup())
    logger.info(f"Deleted {deleted} old analyses")
    return deleted


@celery_app.task
def health_check():
    """Simple health check task for monitoring"""
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "worker": "celery"
    }
