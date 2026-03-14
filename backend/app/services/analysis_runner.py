"""
Analysis Runner Service - PostgreSQL Version
Simplified version of the IAskan Verified GEO Protocol™ analysis engine
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


async def run_analysis_simplified(analysis_id: str, project: dict, plan_config: dict):
    """
    Simplified IAskan Verified GEO Protocol™ Analysis Engine
    PostgreSQL-compatible version
    """
    try:
        brand_name = project.get("brand_name", "")
        keywords = project.get("keywords", [])
        ai_engines = plan_config.get("ai_engines", ["chatgpt"])
        num_prompts = plan_config.get("num_prompts", 10)
        
        logger.info(f"Starting analysis {analysis_id} for brand: {brand_name}")
        
        # Update status to running
        await update_analysis(analysis_id, {"status": "running"})
        
        # Simulate analysis delay
        await asyncio.sleep(3)
        
        # Generate simulated scores
        global_score = random.uniform(45, 85)
        mention_rate = random.uniform(30, 70)
        
        # Simulated AI scores
        ai_scores = {}
        for ai in ai_engines:
            ai_scores[ai] = round(random.uniform(40, 90), 1)
        
        # Simulated R.A.T.E. scores
        rate_scores = {
            "relevance": round(random.uniform(50, 90), 1),
            "authority": round(random.uniform(40, 85), 1),
            "truthfulness": round(random.uniform(45, 88), 1),
            "endorsement": round(random.uniform(35, 80), 1),
            "total": round(global_score, 1)
        }
        
        # Calculate grade
        if global_score >= 80:
            grade = "A"
        elif global_score >= 65:
            grade = "B"
        elif global_score >= 50:
            grade = "C"
        elif global_score >= 35:
            grade = "D"
        else:
            grade = "F"
        
        # Update analysis with results
        await update_analysis(analysis_id, {
            "status": "completed",
            "global_score": round(global_score, 1),
            "grade": grade,
            "mention_rate": round(mention_rate, 1),
            "ai_scores": ai_scores,
            "rate_scores": rate_scores,
            "total_queries": num_prompts,
            "ai_engines_used": ai_engines,
            "completed_at": datetime.now(timezone.utc)
        })
        
        logger.info(f"Analysis {analysis_id} completed with score: {global_score:.1f}")
        
    except Exception as e:
        logger.error(f"Analysis {analysis_id} failed: {e}")
        await update_analysis(analysis_id, {
            "status": "failed",
            "error_message": str(e),
            "completed_at": datetime.now(timezone.utc)
        })
