"""
MongoDB to PostgreSQL Migration Script for IAskan
Migrates existing data from MongoDB to PostgreSQL

Usage:
    python scripts/migrate_mongo_to_postgres.py [--dry-run]
    
Options:
    --dry-run    Preview migration without making changes
"""
import asyncio
import argparse
import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional

from motor.motor_asyncio import AsyncIOMotorClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.database import async_session_maker, init_db
from app.db.models import (
    User, UserSession, Subscription, Project, Analysis, 
    Notification, ScanSchedule, Organization, OrganizationMember,
    MagicLink, EmailVerificationToken, SubscriptionPlan, SubscriptionStatus,
    AnalysisStatus, OrganizationRole
)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# MongoDB Configuration
MONGO_URL = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
MONGO_DB_NAME = "test_database"


class MigrationStats:
    """Track migration statistics"""
    def __init__(self):
        self.users_migrated = 0
        self.users_skipped = 0
        self.sessions_migrated = 0
        self.subscriptions_migrated = 0
        self.projects_migrated = 0
        self.analyses_migrated = 0
        self.notifications_migrated = 0
        self.magic_links_migrated = 0
        self.errors = []
    
    def summary(self) -> str:
        return f"""
╔════════════════════════════════════════════════════════╗
║           MIGRATION SUMMARY                            ║
╠════════════════════════════════════════════════════════╣
║  Users migrated:         {self.users_migrated:5d}                        ║
║  Users skipped:          {self.users_skipped:5d}                        ║
║  Sessions migrated:      {self.sessions_migrated:5d}                        ║
║  Subscriptions migrated: {self.subscriptions_migrated:5d}                        ║
║  Projects migrated:      {self.projects_migrated:5d}                        ║
║  Analyses migrated:      {self.analyses_migrated:5d}                        ║
║  Notifications migrated: {self.notifications_migrated:5d}                        ║
║  Magic Links migrated:   {self.magic_links_migrated:5d}                        ║
║  Errors:                 {len(self.errors):5d}                        ║
╚════════════════════════════════════════════════════════╝
        """


def parse_datetime(value: Any) -> Optional[datetime]:
    """Parse datetime from various formats"""
    if value is None:
        return None
    if isinstance(value, datetime):
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value
    if isinstance(value, str):
        try:
            dt = datetime.fromisoformat(value.replace('Z', '+00:00'))
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt
        except ValueError:
            return None
    return None


def map_subscription_plan(plan: str) -> SubscriptionPlan:
    """Map MongoDB plan string to PostgreSQL enum"""
    mapping = {
        "free": SubscriptionPlan.FREE,
        "starter": SubscriptionPlan.STARTER,
        "pro": SubscriptionPlan.PRO,
        "business": SubscriptionPlan.BUSINESS,
    }
    return mapping.get(plan.lower(), SubscriptionPlan.FREE)


def map_subscription_status(status: str) -> SubscriptionStatus:
    """Map MongoDB status string to PostgreSQL enum"""
    mapping = {
        "active": SubscriptionStatus.ACTIVE,
        "cancelled": SubscriptionStatus.CANCELLED,
        "expired": SubscriptionStatus.EXPIRED,
        "past_due": SubscriptionStatus.PAST_DUE,
    }
    return mapping.get(status.lower(), SubscriptionStatus.ACTIVE)


def map_analysis_status(status: str) -> AnalysisStatus:
    """Map MongoDB status string to PostgreSQL enum"""
    mapping = {
        "pending": AnalysisStatus.PENDING,
        "running": AnalysisStatus.RUNNING,
        "completed": AnalysisStatus.COMPLETED,
        "failed": AnalysisStatus.FAILED,
    }
    return mapping.get(status.lower(), AnalysisStatus.PENDING)


async def check_existing(db: AsyncSession, model, field: str, value: str) -> bool:
    """Check if a record already exists"""
    result = await db.execute(
        select(model).where(getattr(model, field) == value)
    )
    return result.scalar_one_or_none() is not None


async def migrate_users(mongo_db, pg_session: AsyncSession, stats: MigrationStats, dry_run: bool):
    """Migrate users from MongoDB to PostgreSQL"""
    logger.info("Migrating users...")
    
    cursor = mongo_db.users.find({})
    async for doc in cursor:
        user_id = doc.get("user_id")
        email = doc.get("email")
        
        if not user_id or not email:
            logger.warning(f"Skipping user without user_id or email: {doc.get('_id')}")
            stats.users_skipped += 1
            continue
        
        # Check if user already exists
        if await check_existing(pg_session, User, "user_id", user_id):
            logger.debug(f"User {user_id} already exists, skipping")
            stats.users_skipped += 1
            continue
        
        if await check_existing(pg_session, User, "email", email):
            logger.debug(f"User with email {email} already exists, skipping")
            stats.users_skipped += 1
            continue
        
        if dry_run:
            logger.info(f"[DRY RUN] Would migrate user: {email}")
            stats.users_migrated += 1
            continue
        
        try:
            user = User(
                user_id=user_id,
                email=email,
                name=doc.get("name"),
                picture=doc.get("picture"),
                company=doc.get("company"),
                auth_provider=doc.get("auth_provider"),
                password_hash=doc.get("password_hash"),
                email_verified=doc.get("email_verified", False),
                email_verified_at=parse_datetime(doc.get("email_verified_at")),
                registration_ip=doc.get("registration_ip"),
                registration_fingerprint=doc.get("registration_fingerprint"),
                onboarding_completed=doc.get("onboarding_completed", False),
                onboarding_steps=doc.get("onboarding_steps", {}),
                preferences=doc.get("preferences", {}),
                created_at=parse_datetime(doc.get("created_at")) or datetime.now(timezone.utc),
            )
            pg_session.add(user)
            await pg_session.flush()
            stats.users_migrated += 1
            logger.info(f"Migrated user: {email}")
            
        except Exception as e:
            logger.error(f"Error migrating user {email}: {e}")
            stats.errors.append(f"User {email}: {e}")
            await pg_session.rollback()


async def migrate_subscriptions(mongo_db, pg_session: AsyncSession, stats: MigrationStats, dry_run: bool):
    """Migrate subscriptions from MongoDB to PostgreSQL"""
    logger.info("Migrating subscriptions...")
    
    cursor = mongo_db.subscriptions.find({})
    async for doc in cursor:
        user_id = doc.get("user_id")
        subscription_id = doc.get("subscription_id")
        
        if not user_id:
            continue
        
        # Check if user exists
        if not await check_existing(pg_session, User, "user_id", user_id):
            logger.warning(f"User {user_id} not found, skipping subscription")
            continue
        
        # Check if subscription already exists
        if subscription_id and await check_existing(pg_session, Subscription, "subscription_id", subscription_id):
            logger.debug(f"Subscription {subscription_id} already exists, skipping")
            continue
        
        if await check_existing(pg_session, Subscription, "user_id", user_id):
            logger.debug(f"Subscription for user {user_id} already exists, skipping")
            continue
        
        if dry_run:
            logger.info(f"[DRY RUN] Would migrate subscription for user: {user_id}")
            stats.subscriptions_migrated += 1
            continue
        
        try:
            subscription = Subscription(
                subscription_id=subscription_id or f"sub_{user_id[:12]}",
                user_id=user_id,
                plan=map_subscription_plan(doc.get("plan", "free")),
                status=map_subscription_status(doc.get("status", "active")),
                stripe_customer_id=doc.get("stripe_customer_id"),
                stripe_subscription_id=doc.get("stripe_subscription_id"),
                queries_limit=doc.get("queries_limit", 90),
                queries_used=doc.get("queries_used", 0),
                scans_limit=doc.get("scans_limit", 1),
                scans_used=doc.get("scans_used", 0),
                free_scans_remaining=doc.get("free_scans_remaining", 1),
                article_optimizer_limit=doc.get("article_optimizer_limit", 0),
                article_optimizer_used=doc.get("article_optimizer_used", 0),
                current_period_start=parse_datetime(doc.get("current_period_start")),
                current_period_end=parse_datetime(doc.get("current_period_end")),
                created_at=parse_datetime(doc.get("created_at")) or datetime.now(timezone.utc),
            )
            pg_session.add(subscription)
            await pg_session.flush()
            stats.subscriptions_migrated += 1
            logger.info(f"Migrated subscription for user: {user_id}")
            
        except Exception as e:
            logger.error(f"Error migrating subscription for {user_id}: {e}")
            stats.errors.append(f"Subscription {user_id}: {e}")


async def migrate_projects(mongo_db, pg_session: AsyncSession, stats: MigrationStats, dry_run: bool):
    """Migrate projects from MongoDB to PostgreSQL"""
    logger.info("Migrating projects...")
    
    cursor = mongo_db.projects.find({})
    async for doc in cursor:
        project_id = doc.get("project_id")
        user_id = doc.get("user_id")
        
        if not project_id or not user_id:
            continue
        
        # Check if user exists
        if not await check_existing(pg_session, User, "user_id", user_id):
            logger.warning(f"User {user_id} not found, skipping project {project_id}")
            continue
        
        # Check if project already exists
        if await check_existing(pg_session, Project, "project_id", project_id):
            logger.debug(f"Project {project_id} already exists, skipping")
            continue
        
        if dry_run:
            logger.info(f"[DRY RUN] Would migrate project: {doc.get('name')}")
            stats.projects_migrated += 1
            continue
        
        try:
            project = Project(
                project_id=project_id,
                user_id=user_id,
                name=doc.get("name", "Projet sans nom"),
                website_url=doc.get("website_url"),
                brand_name=doc.get("brand_name"),
                logo_url=doc.get("logo_url"),
                competitors=doc.get("competitors", []),
                keywords=doc.get("keywords", []),
                industry=doc.get("industry"),
                description=doc.get("description"),
                created_at=parse_datetime(doc.get("created_at")) or datetime.now(timezone.utc),
            )
            pg_session.add(project)
            await pg_session.flush()
            stats.projects_migrated += 1
            logger.info(f"Migrated project: {doc.get('name')}")
            
        except Exception as e:
            logger.error(f"Error migrating project {project_id}: {e}")
            stats.errors.append(f"Project {project_id}: {e}")


async def migrate_analyses(mongo_db, pg_session: AsyncSession, stats: MigrationStats, dry_run: bool):
    """Migrate analyses from MongoDB to PostgreSQL"""
    logger.info("Migrating analyses...")
    
    cursor = mongo_db.analyses.find({})
    async for doc in cursor:
        analysis_id = doc.get("analysis_id")
        project_id = doc.get("project_id")
        user_id = doc.get("user_id")
        
        if not analysis_id or not project_id or not user_id:
            continue
        
        # Check if project and user exist
        if not await check_existing(pg_session, User, "user_id", user_id):
            logger.warning(f"User {user_id} not found, skipping analysis {analysis_id}")
            continue
            
        if not await check_existing(pg_session, Project, "project_id", project_id):
            logger.warning(f"Project {project_id} not found, skipping analysis {analysis_id}")
            continue
        
        # Check if analysis already exists
        if await check_existing(pg_session, Analysis, "analysis_id", analysis_id):
            logger.debug(f"Analysis {analysis_id} already exists, skipping")
            continue
        
        if dry_run:
            logger.info(f"[DRY RUN] Would migrate analysis: {analysis_id}")
            stats.analyses_migrated += 1
            continue
        
        try:
            # Truncate grade to max 10 chars
            grade = doc.get("grade")
            if grade and len(str(grade)) > 10:
                grade = str(grade)[:10]
            
            analysis = Analysis(
                analysis_id=analysis_id,
                project_id=project_id,
                user_id=user_id,
                status=map_analysis_status(doc.get("status", "pending")),
                global_score=doc.get("global_score"),
                grade=grade,
                ai_scores=doc.get("ai_scores", {}),
                rate_scores=doc.get("rate_score", {}),
                query_scores=doc.get("query_scores", []),
                competitor_analysis=doc.get("competitor_comparison", {}),
                recommendations=doc.get("recommendations", []),
                stability_score=doc.get("stability_data", {}).get("stability_score"),
                total_queries=doc.get("total_queries", 0),
                queries_with_mention=doc.get("queries_with_mention", 0),
                mention_rate=doc.get("mention_rate"),
                average_position=doc.get("average_position"),
                ai_engines_used=doc.get("ai_engines_used", []),
                error_message=doc.get("error_message"),
                started_at=parse_datetime(doc.get("started_at")),
                completed_at=parse_datetime(doc.get("completed_at")),
                created_at=parse_datetime(doc.get("created_at")) or datetime.now(timezone.utc),
            )
            pg_session.add(analysis)
            await pg_session.flush()
            stats.analyses_migrated += 1
            logger.info(f"Migrated analysis: {analysis_id}")
            
        except Exception as e:
            logger.error(f"Error migrating analysis {analysis_id}: {e}")
            stats.errors.append(f"Analysis {analysis_id}: {e}")
            await pg_session.rollback()
            # Continue with next analysis


async def migrate_notifications(mongo_db, pg_session: AsyncSession, stats: MigrationStats, dry_run: bool):
    """Migrate notifications from MongoDB to PostgreSQL"""
    logger.info("Migrating notifications...")
    
    cursor = mongo_db.notifications.find({})
    async for doc in cursor:
        notification_id = doc.get("notification_id")
        user_id = doc.get("user_id")
        
        if not notification_id or not user_id:
            continue
        
        # Check if user exists
        if not await check_existing(pg_session, User, "user_id", user_id):
            logger.warning(f"User {user_id} not found, skipping notification")
            continue
        
        # Check if notification already exists
        if await check_existing(pg_session, Notification, "notification_id", notification_id):
            logger.debug(f"Notification {notification_id} already exists, skipping")
            continue
        
        if dry_run:
            logger.info(f"[DRY RUN] Would migrate notification: {notification_id}")
            stats.notifications_migrated += 1
            continue
        
        try:
            notification = Notification(
                notification_id=notification_id,
                user_id=user_id,
                type=doc.get("type", "info"),
                title=doc.get("title", "Notification"),
                message=doc.get("message"),
                data=doc.get("data", {}),
                read=doc.get("read", False),
                created_at=parse_datetime(doc.get("created_at")) or datetime.now(timezone.utc),
            )
            pg_session.add(notification)
            await pg_session.flush()
            stats.notifications_migrated += 1
            logger.info(f"Migrated notification: {notification_id}")
            
        except Exception as e:
            logger.error(f"Error migrating notification {notification_id}: {e}")
            stats.errors.append(f"Notification {notification_id}: {e}")


async def migrate_sessions(mongo_db, pg_session: AsyncSession, stats: MigrationStats, dry_run: bool):
    """Migrate user sessions from MongoDB to PostgreSQL"""
    logger.info("Migrating user sessions...")
    
    cursor = mongo_db.user_sessions.find({})
    async for doc in cursor:
        session_id = doc.get("session_id")
        user_id = doc.get("user_id")
        session_token = doc.get("session_token")
        
        if not session_id or not user_id or not session_token:
            continue
        
        # Check if user exists
        if not await check_existing(pg_session, User, "user_id", user_id):
            continue
        
        # Check if session already exists
        if await check_existing(pg_session, UserSession, "session_id", session_id):
            continue
        
        if dry_run:
            logger.info(f"[DRY RUN] Would migrate session: {session_id}")
            stats.sessions_migrated += 1
            continue
        
        try:
            expires_at = parse_datetime(doc.get("expires_at"))
            if not expires_at:
                expires_at = datetime.now(timezone.utc)
            
            session = UserSession(
                session_id=session_id,
                user_id=user_id,
                session_token=session_token,
                expires_at=expires_at,
                created_at=parse_datetime(doc.get("created_at")) or datetime.now(timezone.utc),
            )
            pg_session.add(session)
            await pg_session.flush()
            stats.sessions_migrated += 1
            
        except Exception as e:
            logger.error(f"Error migrating session {session_id}: {e}")
            stats.errors.append(f"Session {session_id}: {e}")


async def migrate_magic_links(mongo_db, pg_session: AsyncSession, stats: MigrationStats, dry_run: bool):
    """Migrate magic links from MongoDB to PostgreSQL"""
    logger.info("Migrating magic links...")
    
    cursor = mongo_db.magic_links.find({})
    async for doc in cursor:
        token = doc.get("token")
        user_id = doc.get("user_id")
        
        if not token or not user_id:
            continue
        
        # Check if user exists
        if not await check_existing(pg_session, User, "user_id", user_id):
            continue
        
        # Check if magic link already exists
        if await check_existing(pg_session, MagicLink, "token", token):
            continue
        
        if dry_run:
            logger.info(f"[DRY RUN] Would migrate magic link for user: {user_id}")
            stats.magic_links_migrated += 1
            continue
        
        try:
            expires_at = parse_datetime(doc.get("expires_at"))
            if not expires_at:
                expires_at = datetime.now(timezone.utc)
            
            magic_link = MagicLink(
                token=token,
                user_id=user_id,
                email=doc.get("email", ""),
                expires_at=expires_at,
                used=doc.get("used", False),
                created_at=parse_datetime(doc.get("created_at")) or datetime.now(timezone.utc),
            )
            pg_session.add(magic_link)
            await pg_session.flush()
            stats.magic_links_migrated += 1
            
        except Exception as e:
            logger.error(f"Error migrating magic link: {e}")
            stats.errors.append(f"MagicLink: {e}")


async def run_migration(dry_run: bool = False):
    """Main migration function"""
    logger.info("=" * 60)
    logger.info("IAskan MongoDB to PostgreSQL Migration")
    logger.info("=" * 60)
    
    if dry_run:
        logger.info("🔍 DRY RUN MODE - No changes will be made")
    
    stats = MigrationStats()
    
    # Initialize PostgreSQL
    logger.info("Initializing PostgreSQL database...")
    await init_db()
    
    # Connect to MongoDB
    logger.info(f"Connecting to MongoDB: {MONGO_URL}")
    mongo_client = AsyncIOMotorClient(MONGO_URL)
    mongo_db = mongo_client[MONGO_DB_NAME]
    
    # Verify MongoDB connection
    collections = await mongo_db.list_collection_names()
    logger.info(f"Found MongoDB collections: {collections}")
    
    async with async_session_maker() as pg_session:
        try:
            # Migrate in order (respecting foreign key constraints)
            await migrate_users(mongo_db, pg_session, stats, dry_run)
            await migrate_subscriptions(mongo_db, pg_session, stats, dry_run)
            await migrate_projects(mongo_db, pg_session, stats, dry_run)
            await migrate_analyses(mongo_db, pg_session, stats, dry_run)
            await migrate_notifications(mongo_db, pg_session, stats, dry_run)
            await migrate_sessions(mongo_db, pg_session, stats, dry_run)
            await migrate_magic_links(mongo_db, pg_session, stats, dry_run)
            
            if not dry_run:
                await pg_session.commit()
                logger.info("✅ All changes committed to PostgreSQL")
            else:
                await pg_session.rollback()
                logger.info("🔍 DRY RUN completed - no changes made")
                
        except Exception as e:
            logger.error(f"Migration error: {e}")
            await pg_session.rollback()
            stats.errors.append(f"Migration: {e}")
    
    # Close MongoDB connection
    mongo_client.close()
    
    # Print summary
    print(stats.summary())
    
    if stats.errors:
        logger.error("Errors encountered during migration:")
        for error in stats.errors:
            logger.error(f"  - {error}")
    
    return stats


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Migrate IAskan data from MongoDB to PostgreSQL")
    parser.add_argument("--dry-run", action="store_true", help="Preview migration without making changes")
    args = parser.parse_args()
    
    asyncio.run(run_migration(dry_run=args.dry_run))
