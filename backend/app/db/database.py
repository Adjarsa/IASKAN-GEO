"""
PostgreSQL Database Connection with SQLAlchemy
Connects to local PostgreSQL (dev) or Supabase (production)
"""
import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy.pool import NullPool
from dotenv import load_dotenv

load_dotenv()

# Get database URL from environment
DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://iaskan_user:iaskan_secure_password_2024@localhost:5432/iaskan")

# Convert to async URL format (postgresql:// -> postgresql+asyncpg://)
if DATABASE_URL.startswith("postgresql://"):
    ASYNC_DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)
elif DATABASE_URL.startswith("postgres://"):
    ASYNC_DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+asyncpg://", 1)
else:
    ASYNC_DATABASE_URL = DATABASE_URL

# Create async engine
engine = create_async_engine(
    ASYNC_DATABASE_URL,
    echo=False,  # Set to True for SQL debugging
    poolclass=NullPool,  # Disable connection pooling for serverless compatibility
)

# Create async session factory
async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

# Base class for models
Base = declarative_base()


async def get_db() -> AsyncSession:
    """Dependency to get database session"""
    async with async_session_maker() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_db():
    """Initialize database - create all tables if they don't exist"""
    from .models import Base as ModelBase
    from sqlalchemy import text
    
    async with engine.begin() as conn:
        # Create all tables (SQLAlchemy handles "if not exists" automatically)
        await conn.run_sync(ModelBase.metadata.create_all)
    
    # Test connection
    async with engine.connect() as conn:
        result = await conn.execute(text("SELECT 1"))
        result.fetchone()  # Ensure connection works


async def close_db():
    """Close database connection"""
    await engine.dispose()
