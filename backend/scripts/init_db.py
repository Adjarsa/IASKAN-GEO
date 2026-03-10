"""
Database initialization script for IAskan
Creates all tables in Supabase PostgreSQL
"""
import asyncio
import sys
sys.path.insert(0, '/app/backend')

from sqlalchemy import text
from app.db.database import engine, Base, async_session_maker
from app.db.models import (
    User, UserSession, EmailVerificationToken, PasswordReset, MagicLink,
    Subscription, PaymentTransaction,
    Project, Analysis, ScanSchedule,
    Notification, Organization, OrganizationMember, OrganizationInvite,
    ArticleOptimization, ContactMessage, AdminLog
)


async def init_database():
    """Initialize the database - create all tables"""
    print("Connecting to Supabase PostgreSQL...")
    
    async with engine.begin() as conn:
        # Enable pgvector extension
        print("Enabling pgvector extension...")
        try:
            await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
            print("✓ pgvector extension enabled")
        except Exception as e:
            print(f"Note: pgvector extension: {e}")
        
        # Create all tables
        print("Creating tables...")
        await conn.run_sync(Base.metadata.create_all)
        print("✓ All tables created successfully!")
    
    # Test connection with a simple query
    async with async_session_maker() as session:
        result = await session.execute(text("SELECT current_database(), current_user"))
        row = result.fetchone()
        print(f"✓ Connected to database: {row[0]} as user: {row[1]}")
    
    print("\n=== Database initialization complete ===")
    print("Tables created:")
    for table in Base.metadata.tables.keys():
        print(f"  - {table}")


if __name__ == "__main__":
    asyncio.run(init_database())
