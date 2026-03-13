"""
IAskan Database Module
MongoDB connection and collections (LEGACY - only used if MONGO_URL is set)
Primary database is PostgreSQL.
"""
from motor.motor_asyncio import AsyncIOMotorClient
from .config import MONGO_URL, DB_NAME, USE_POSTGRES

# MongoDB connection (legacy - only initialized if MONGO_URL is provided and not using PostgreSQL)
client = None
db = None

if MONGO_URL and not USE_POSTGRES:
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]

# Collections - will be None if MongoDB is not configured
users_collection = db.users if db else None
organizations_collection = db.organizations if db else None
projects_collection = db.projects if db else None
analyses_collection = db.analyses if db else None
queries_collection = db.queries if db else None
subscriptions_collection = db.subscriptions if db else None
notifications_collection = db.notifications if db else None
scan_schedules_collection = db.scan_schedules if db else None
free_trial_usage_collection = db.free_trial_usage if db else None
email_verification_tokens_collection = db.email_verification_tokens if db else None
password_resets_collection = db.password_resets if db else None
magic_links_collection = db.magic_links if db else None
user_sessions_collection = db.user_sessions if db else None
contact_messages_collection = db.contact_messages if db else None
payment_transactions_collection = db.payment_transactions if db else None

# New collections for enhanced features
article_optimizations_collection = db.article_optimizations if db else None
influence_sources_collection = db.influence_sources if db else None
semantic_clusters_collection = db.semantic_clusters if db else None
content_gaps_collection = db.content_gaps if db else None
admin_logs_collection = db.admin_logs if db else None
api_usage_collection = db.api_usage if db else None

async def close_db():
    """Close database connection"""
    if client:
        client.close()
