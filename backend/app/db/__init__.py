"""
Database abstraction layer for IAskan
Provides both MongoDB (legacy) and PostgreSQL interfaces
Allows progressive migration from MongoDB to PostgreSQL
"""
import os
from typing import Optional
from contextlib import asynccontextmanager

# Check which database to use
USE_POSTGRES = os.environ.get("USE_POSTGRES", "true").lower() == "true"

# Always import PostgreSQL components (they may be used by routers)
# The imports will work but connections will fail if USE_POSTGRES is False
try:
    from .database import async_session_maker, init_db, close_db, engine
    from .services import (
        UserService, SessionService, SubscriptionService,
        ProjectService, AnalysisService, NotificationService,
        ScheduleService, OrganizationService
    )
    from .models import (
        User, UserSession, Subscription, Project, Analysis,
        Notification, ScanSchedule, Organization, AnalysisStatus
    )
except ImportError as e:
    print(f"Warning: Could not import PostgreSQL modules: {e}")
    async_session_maker = None
    init_db = None
    close_db = None


@asynccontextmanager
async def get_db_session():
    """Get database session context manager"""
    if USE_POSTGRES:
        async with async_session_maker() as session:
            try:
                yield session
            finally:
                await session.close()
    else:
        # For MongoDB, yield None (operations use global db object)
        yield None


async def initialize_database():
    """Initialize the database"""
    if USE_POSTGRES:
        await init_db()
        print("PostgreSQL database initialized")
    else:
        print("Using MongoDB (legacy)")


async def shutdown_database():
    """Shutdown database connections"""
    if USE_POSTGRES:
        await close_db()


# Export services based on database type
__all__ = [
    'get_db_session',
    'initialize_database', 
    'shutdown_database',
    'USE_POSTGRES',
    'async_session_maker',
    'UserService',
    'SessionService', 
    'SubscriptionService',
    'ProjectService',
    'AnalysisService',
    'NotificationService',
    'ScheduleService',
    'OrganizationService',
    'AnalysisStatus',
]
