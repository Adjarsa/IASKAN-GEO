"""
IAskan Database Module
MongoDB connection and collections
"""
from motor.motor_asyncio import AsyncIOMotorClient
from .config import MONGO_URL, DB_NAME

# MongoDB connection
client = AsyncIOMotorClient(MONGO_URL)
db = client[DB_NAME]

# Collections
users_collection = db.users
organizations_collection = db.organizations
projects_collection = db.projects
analyses_collection = db.analyses
queries_collection = db.queries
subscriptions_collection = db.subscriptions
notifications_collection = db.notifications
scan_schedules_collection = db.scan_schedules
free_trial_usage_collection = db.free_trial_usage
email_verification_tokens_collection = db.email_verification_tokens
password_resets_collection = db.password_resets
magic_links_collection = db.magic_links
user_sessions_collection = db.user_sessions
contact_messages_collection = db.contact_messages
payment_transactions_collection = db.payment_transactions

# New collections for enhanced features
article_optimizations_collection = db.article_optimizations
influence_sources_collection = db.influence_sources
semantic_clusters_collection = db.semantic_clusters
content_gaps_collection = db.content_gaps
admin_logs_collection = db.admin_logs
api_usage_collection = db.api_usage

async def close_db():
    """Close database connection"""
    client.close()
