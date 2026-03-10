"""
Article Optimizer Models
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
import uuid


class ContentDiagnostic(BaseModel):
    """Diagnostic result for content analysis"""
    category: str  # structure, semantics, citations, authority, freshness
    score: float  # 0-100
    status: str  # excellent, good, needs_improvement, critical
    findings: List[str] = []
    recommendations: List[str] = []


class ActionItem(BaseModel):
    """Actionable recommendation"""
    priority: str  # critical, high, medium, low
    category: str  # content, structure, distribution, timing
    action: str
    impact: str
    effort: str  # low, medium, high
    timeline: str  # immediate, short_term, medium_term, long_term
    details: Optional[str] = None


class DistributionStrategy(BaseModel):
    """Distribution strategy recommendation"""
    channel: str  # blog, social, pr, partnerships, directories
    priority: str
    action: str
    expected_impact: str
    timing: str


class OptimizationResult(BaseModel):
    """Complete optimization result"""
    # Scores
    overall_score: float = 0.0
    citability_score: float = 0.0
    structure_score: float = 0.0
    authority_score: float = 0.0
    freshness_score: float = 0.0
    
    # Diagnostics
    diagnostics: List[ContentDiagnostic] = []
    
    # Action plan
    action_items: List[ActionItem] = []
    quick_wins: List[ActionItem] = []
    
    # Distribution strategy
    distribution_strategy: List[DistributionStrategy] = []
    
    # Content suggestions
    suggested_sections: List[str] = []
    missing_elements: List[str] = []
    keyword_opportunities: List[str] = []
    
    # Timing recommendations
    optimal_publish_times: List[str] = []
    refresh_schedule: Optional[str] = None


class ArticleOptimization(BaseModel):
    """Article optimization record"""
    model_config = ConfigDict(extra="ignore")
    optimization_id: str = Field(default_factory=lambda: f"opt_{uuid.uuid4().hex[:12]}")
    user_id: str
    organization_id: Optional[str] = None
    project_id: Optional[str] = None
    
    # Input
    article_url: Optional[str] = None
    article_content: Optional[str] = None
    article_title: Optional[str] = None
    
    # Analysis results
    status: str = "pending"  # pending, processing, completed, failed
    result: Optional[OptimizationResult] = None
    
    # Raw analysis data
    raw_analysis: Dict[str, Any] = {}
    
    # Metadata
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: Optional[datetime] = None
    processing_time_ms: Optional[int] = None
