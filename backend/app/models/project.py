"""
Project Models with enhanced configuration
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
import uuid


class PersonaConfig(BaseModel):
    """Target persona configuration"""
    name: str
    description: Optional[str] = None
    keywords: List[str] = []
    pain_points: List[str] = []
    decision_criteria: List[str] = []


class ScanConfig(BaseModel):
    """Scan configuration for a project"""
    level: str = "standard"  # quick, standard, advanced
    num_prompts: int = 50
    runs_per_query: int = 3
    ai_engines: List[str] = ["chatgpt"]
    query_types: Dict[str, float] = {
        "transactional": 0.30,
        "comparative": 0.25,
        "informational": 0.20,
        "local": 0.15,
        "exploratory": 0.10
    }
    variation_modes: List[str] = ["short", "long", "conversational"]
    include_personas: bool = True
    include_competitors: bool = True


class ProjectConfig(BaseModel):
    """Extended project configuration"""
    country: str = "FR"
    language: str = "fr"
    industry: str = ""
    personas: List[PersonaConfig] = []
    scan_config: ScanConfig = Field(default_factory=ScanConfig)
    brand_variants: List[str] = []  # Auto-generated brand name variants
    products: List[str] = []  # Product names for variant detection


class Project(BaseModel):
    """Enhanced Project model"""
    model_config = ConfigDict(extra="ignore")
    project_id: str = Field(default_factory=lambda: f"proj_{uuid.uuid4().hex[:12]}")
    user_id: str
    organization_id: Optional[str] = None  # For multi-tenant support
    name: str
    website_url: str
    brand_name: str
    logo_url: Optional[str] = None
    description: Optional[str] = None
    
    # Competitors
    competitors: List[str] = []  # User-defined competitors
    discovered_competitors: List[Dict[str, Any]] = []  # AI-discovered
    
    # Keywords and topics
    keywords: List[str] = []
    topics: List[str] = []  # Thematic clusters
    
    # Extended configuration
    config: ProjectConfig = Field(default_factory=ProjectConfig)
    
    # Metadata
    last_scan_at: Optional[datetime] = None
    total_scans: int = 0
    average_score: float = 0.0
    
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: Optional[datetime] = None
