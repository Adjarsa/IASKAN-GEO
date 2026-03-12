"""
Analysis Tasks for Celery
Distributed analysis pipeline for IAskan GEO Platform

This module implements the complete GEO analysis pipeline using Celery
for distributed task execution. It uses the modular services:
- AnalysisPipelineService: Main orchestrator for GEO analysis
- LLMConnector: For querying multiple LLM providers
- GEOScoringEngine: For calculating GEO scores
- CompetitiveIntelligenceEngine: For competitor analysis
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

# Import modular services
from ..services.analysis_pipeline import AnalysisPipelineService, analysis_pipeline
from ..services.llm_connector import LLMConnector
from ..services.geo_scoring import GEOScoringEngine
from ..services.competitive_intelligence import CompetitiveIntelligenceEngine

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
    Run a complete GEO analysis for a project using AnalysisPipelineService.
    
    This is the main entry point for the analysis pipeline.
    It delegates to the AnalysisPipelineService which orchestrates:
    1. Query generation with multi-dimension distribution
    2. Multi-run AI querying for stability
    3. GEO scoring and indices calculation
    4. Competitive intelligence analysis
    5. Semantic and content gap analysis
    6. Results compilation and notifications
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
            
            # Build project dict for pipeline
            project_data = {
                "project_id": project_id,
                "user_id": user_id,
                "brand_name": project.brand_name or project.name,
                "name": project.name,
                "keywords": project.keywords or [],
                "competitors": project.competitors or [],
                "website_url": project.website_url or "",
                "products": getattr(project, 'products', []) or [],
                "industry": project.industry
            }
            
            # Get subscription for plan config
            subscription = await SubscriptionService.get_by_user_id(db, user_id)
            plan = subscription.plan.value if subscription else "free"
            plan_config = SUBSCRIPTION_PLANS.get(plan, SUBSCRIPTION_PLANS["free"])
            
            logger.info(f"Running analysis with plan: {plan}")
            
            # Define update callback for progress tracking
            async def update_progress(aid: str, data: dict):
                await AnalysisService.update(db, aid, **data)
            
            # Run the full analysis pipeline
            results = await analysis_pipeline.run_full_analysis(
                analysis_id=analysis_id,
                project=project_data,
                plan_config=plan_config,
                update_callback=update_progress
            )
            
            # Update analysis with complete results
            await AnalysisService.update(
                db, analysis_id,
                status=AnalysisStatus.COMPLETED,
                completed_at=datetime.now(timezone.utc),
                global_score=results.get("global_score", 0),
                grade=results.get("grade", "F"),
                ai_scores=results.get("ai_scores", {}),
                rate_scores=results.get("rate_score", {}),
                query_scores=results.get("query_scores", []),
                indices=results.get("indices", {}),
                stability_data=results.get("stability_data", {}),
                recommendations=results.get("recommendations", []),
                competitor_analysis={
                    "discovered": results.get("competitor_comparison", []),
                    "gap_analysis": results.get("competitive_gap", {})
                },
                semantic_analysis=results.get("semantic_analysis"),
                content_gaps=results.get("content_gaps"),
                analysis_summary=results.get("analysis_summary", {}),
                site_enrichment=results.get("site_enrichment", {}),
                brand_analysis=results.get("brand_analysis", {}),
                current_phase="completed"
            )
            
            # Create notification
            global_score = results.get("global_score", 0)
            grade = results.get("grade", "F")
            
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
                'queries_processed': len(results.get("query_scores", [])),
                'responses_collected': results.get("analysis_summary", {}).get("total_responses", 0)
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
