"""
Analysis and Query Models
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
import uuid


class Query(BaseModel):
    """Query model for GEO analysis"""
    model_config = ConfigDict(extra="ignore")
    query_id: str = Field(default_factory=lambda: f"qry_{uuid.uuid4().hex[:12]}")
    analysis_id: str
    text: str
    original_text: str  # Before variation
    variation_type: str = "original"  # original, short, long, conversational
    intent_type: str  # commercial, informational, local, transactional, conversational
    persona: Optional[str] = None  # Associated persona
    cluster: Optional[str] = None  # Thematic cluster
    quality_score: float = 0.0  # Query quality scoring
    ai_responses: Dict[str, Dict[str, Any]] = {}  # AI name -> response data
    scores: Dict[str, float] = {}
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class SemanticCluster(BaseModel):
    """Semantic cluster for query grouping"""
    cluster_id: str
    name: str
    keywords: List[str] = []
    query_ids: List[str] = []
    avg_score: float = 0.0
    coverage: float = 0.0  # Brand coverage in this cluster


class InfluenceSource(BaseModel):
    """Influence source detected in AI responses"""
    source_id: str = Field(default_factory=lambda: f"src_{uuid.uuid4().hex[:12]}")
    domain: str
    url: Optional[str] = None
    mentions: int = 0
    ai_sources: List[str] = []  # Which AIs mentioned it
    cooccurrence_with_brand: int = 0
    influence_score: float = 0.0
    source_type: str = "unknown"  # blog, news, review, official, social


class Analysis(BaseModel):
    """Enhanced Analysis model with all indices"""
    model_config = ConfigDict(extra="ignore")
    analysis_id: str = Field(default_factory=lambda: f"ana_{uuid.uuid4().hex[:12]}")
    project_id: str
    user_id: str
    organization_id: Optional[str] = None
    
    # Status
    status: str = "pending"  # pending, running, completed, failed
    current_phase: str = "pending"  # query_generation, ai_querying, calculating_indices, completed
    progress: int = 0  # 0-100
    
    # Core scores
    global_score: float = 0.0
    grade: str = "N/A"  # A, B, C, D, F
    rate_score: Dict[str, Any] = {}  # R.A.T.E scores
    ai_scores: Dict[str, float] = {}  # Score per AI
    
    # Query analysis
    query_scores: List[Dict[str, Any]] = []
    query_type_breakdown: Dict[str, Any] = {}
    
    # IAskan Verified GEO Protocol™ indices
    indices: Dict[str, float] = {}  # Stability, Dominance, Trust Gap, Opportunity
    stability_data: Dict[str, Any] = {}
    
    # Semantic analysis
    semantic_clusters: List[Dict[str, Any]] = []
    topic_coverage: Dict[str, float] = {}
    
    # Influence mapping
    influence_sources: List[Dict[str, Any]] = []
    top_domains: List[Dict[str, Any]] = []
    
    # Content gaps
    content_gaps: List[Dict[str, Any]] = []
    opportunities: List[Dict[str, Any]] = []
    quick_wins: List[Dict[str, Any]] = []
    
    # Recommendations
    recommendations: List[Dict[str, Any]] = []
    competitor_comparison: List[Dict[str, Any]] = []
    
    # Site enrichment
    site_enrichment: Dict[str, Any] = {}
    
    # Diff with previous scan
    scan_diff: Dict[str, Any] = {}
    
    # Metadata
    analysis_summary: Dict[str, Any] = {}
    protocol_version: str = "IAskan Verified GEO Protocol™ v2.1"
    scheduled: bool = False
    schedule_id: Optional[str] = None
    
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: Optional[datetime] = None
