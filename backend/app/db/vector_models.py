"""
Vector Models for Semantic Search using pgvector
Supports similarity search on queries, responses, and content
"""
from sqlalchemy import (
    Column, String, Integer, Float, DateTime, Text, JSON, 
    ForeignKey, Index
)
from sqlalchemy.sql import func
from datetime import datetime
import uuid

from .database import Base

# Check if pgvector is available
try:
    from pgvector.sqlalchemy import Vector
    PGVECTOR_AVAILABLE = True
except ImportError:
    PGVECTOR_AVAILABLE = False
    Vector = None


def generate_uuid(prefix: str = "") -> str:
    """Generate a prefixed UUID"""
    return f"{prefix}{uuid.uuid4().hex[:12]}"


# ================== EMBEDDING MODELS ==================

class QueryEmbedding(Base):
    """Store query embeddings for semantic search"""
    __tablename__ = "query_embeddings"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    embedding_id = Column(String(50), unique=True, nullable=False, default=lambda: generate_uuid("qemb_"))
    
    # Link to project for scoping
    project_id = Column(String(50), ForeignKey("projects.project_id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(String(50), nullable=False, index=True)
    
    # Query content
    query_text = Column(Text, nullable=False)
    query_type = Column(String(50))  # transactional, comparative, informational, etc.
    language = Column(String(10), default="fr")
    
    # Vector embedding (1536 dimensions for OpenAI text-embedding-3-small)
    # Note: Vector type requires pgvector extension
    if PGVECTOR_AVAILABLE and Vector is not None:
        embedding = Column(Vector(1536))
    else:
        embedding = Column(JSON)  # Fallback to JSON array if pgvector not available
    
    # Metadata
    source = Column(String(50))  # generated, user_input, imported
    analysis_id = Column(String(50))  # Link to analysis if from scan
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    __table_args__ = (
        Index('idx_query_embedding_project', 'project_id'),
        Index('idx_query_embedding_type', 'query_type'),
    )


class ContentEmbedding(Base):
    """Store content/article embeddings for similarity search"""
    __tablename__ = "content_embeddings"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    embedding_id = Column(String(50), unique=True, nullable=False, default=lambda: generate_uuid("cemb_"))
    
    # Link to project
    project_id = Column(String(50), ForeignKey("projects.project_id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(String(50), nullable=False, index=True)
    
    # Content info
    content_type = Column(String(50))  # article, page, faq, product
    title = Column(String(500))
    url = Column(Text)
    content_snippet = Column(Text)  # First 500 chars for display
    full_content_hash = Column(String(64))  # SHA256 to detect changes
    
    # Vector embedding
    if PGVECTOR_AVAILABLE and Vector is not None:
        embedding = Column(Vector(1536))
    else:
        embedding = Column(JSON)
    
    # Metadata
    word_count = Column(Integer)
    language = Column(String(10), default="fr")
    last_crawled = Column(DateTime(timezone=True))
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    __table_args__ = (
        Index('idx_content_embedding_project', 'project_id'),
        Index('idx_content_embedding_type', 'content_type'),
    )


class ResponseEmbedding(Base):
    """Store AI response embeddings for pattern analysis"""
    __tablename__ = "response_embeddings"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    embedding_id = Column(String(50), unique=True, nullable=False, default=lambda: generate_uuid("remb_"))
    
    # Links
    project_id = Column(String(50), ForeignKey("projects.project_id", ondelete="CASCADE"), nullable=False, index=True)
    analysis_id = Column(String(50), index=True)
    query_embedding_id = Column(String(50))  # Link to query
    
    # Response content
    ai_engine = Column(String(50))  # chatgpt, claude, gemini, perplexity
    response_snippet = Column(Text)  # First 1000 chars
    brand_mentioned = Column(String(1), default="N")  # Y/N for fast filtering
    brand_position = Column(Integer)  # Position in response (1-10+)
    brand_role = Column(String(50))  # leader, recommended, alternative, mentioned
    
    # Vector embedding
    if PGVECTOR_AVAILABLE and Vector is not None:
        embedding = Column(Vector(1536))
    else:
        embedding = Column(JSON)
    
    # Scores
    relevance_score = Column(Float)
    sentiment_score = Column(Float)  # -1 to 1
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    __table_args__ = (
        Index('idx_response_embedding_project', 'project_id'),
        Index('idx_response_embedding_analysis', 'analysis_id'),
        Index('idx_response_brand', 'brand_mentioned'),
    )


class SemanticCluster(Base):
    """Store semantic clusters for topic grouping"""
    __tablename__ = "semantic_clusters"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    cluster_id = Column(String(50), unique=True, nullable=False, default=lambda: generate_uuid("clust_"))
    
    project_id = Column(String(50), ForeignKey("projects.project_id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Cluster info
    name = Column(String(255), nullable=False)
    description = Column(Text)
    keywords = Column(JSON, default=list)  # Top keywords
    query_count = Column(Integer, default=0)
    
    # Centroid embedding (average of all queries in cluster)
    if PGVECTOR_AVAILABLE and Vector is not None:
        centroid = Column(Vector(1536))
    else:
        centroid = Column(JSON)
    
    # Stats
    avg_score = Column(Float)
    avg_mention_rate = Column(Float)
    dominant_intent = Column(String(50))
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    __table_args__ = (
        Index('idx_cluster_project', 'project_id'),
    )


class ContentGap(Base):
    """Store identified content gaps based on semantic analysis"""
    __tablename__ = "content_gaps"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    gap_id = Column(String(50), unique=True, nullable=False, default=lambda: generate_uuid("gap_"))
    
    project_id = Column(String(50), ForeignKey("projects.project_id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Gap info
    topic = Column(String(255), nullable=False)
    description = Column(Text)
    keywords = Column(JSON, default=list)
    
    # Related queries where brand was NOT mentioned
    related_queries = Column(JSON, default=list)  # List of query texts
    competitor_mentions = Column(JSON, default=dict)  # {competitor: count}
    
    # Priority
    importance_score = Column(Float)  # 0-100
    opportunity_score = Column(Float)  # Based on search volume/competition
    difficulty = Column(String(20))  # easy, medium, hard
    
    # Recommendations
    suggested_content_type = Column(String(50))  # article, faq, guide, comparison
    suggested_keywords = Column(JSON, default=list)
    
    status = Column(String(20), default="open")  # open, addressed, dismissed
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    __table_args__ = (
        Index('idx_gap_project', 'project_id'),
        Index('idx_gap_status', 'status'),
    )
