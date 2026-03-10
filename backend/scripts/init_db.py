"""
Database initialization script for IAskan
Creates all tables in PostgreSQL
"""
import asyncio
import sys
sys.path.insert(0, '/app/backend')

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.pool import NullPool
import os
from dotenv import load_dotenv

load_dotenv('/app/backend/.env')

DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://iaskan_user:iaskan_secure_password_2024@localhost:5432/iaskan")
ASYNC_DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)


async def init_database():
    """Initialize the database - create all tables"""
    print(f"Connecting to PostgreSQL...")
    print(f"URL: {DATABASE_URL[:50]}...")
    
    # Create engine
    engine = create_async_engine(ASYNC_DATABASE_URL, echo=False, poolclass=NullPool)
    
    # Import models to register them with Base
    from app.db.models import (
        User, UserSession, EmailVerificationToken, PasswordReset, MagicLink,
        Subscription, PaymentTransaction,
        Project, Analysis, ScanSchedule,
        Notification, Organization, OrganizationMember, OrganizationInvite,
        ArticleOptimization, ContactMessage, AdminLog
    )
    from app.db.database import Base
    
    async with engine.begin() as conn:
        print("Creating tables...")
        await conn.run_sync(Base.metadata.create_all)
        print("✓ All tables created successfully!")
    
    # Test connection with a simple query
    async with engine.connect() as conn:
        result = await conn.execute(text("SELECT current_database(), current_user"))
        row = result.fetchone()
        print(f"✓ Connected to database: {row[0]} as user: {row[1]}")
    
    await engine.dispose()
    
    print("\n=== Database initialization complete ===")
    print("Tables created:")
    for table in Base.metadata.tables.keys():
        print(f"  - {table}")


if __name__ == "__main__":
    asyncio.run(init_database())
