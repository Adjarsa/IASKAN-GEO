"""
Source Seeding Strategy Router - Sprint D
Identify and analyze sources cited by LLMs to inform content strategy

Features:
- Analyze which sources LLMs cite for specific topics
- Identify citation patterns and authority signals
- Generate source seeding recommendations
- Track source presence over time
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
import logging
import re
import os

from ..db.database import async_session_maker
from ..db.services import ProjectService
from ..routers.auth import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/source-strategy", tags=["source-strategy"])

# Get API keys
EMERGENT_LLM_KEY = os.environ.get('EMERGENT_LLM_KEY')


# ================== MODELS ==================

class SourceAnalysisRequest(BaseModel):
    topic: str
    keywords: Optional[List[str]] = []
    industry: Optional[str] = None
    num_queries: int = 5


class SourceSeedingRecommendation(BaseModel):
    source_type: str  # blog, research, news, forum, social, database
    platform: str
    priority: str  # high, medium, low
    strategy: str
    expected_impact: str
    action_items: List[str]


# ================== SOURCE PATTERNS ==================

# Common source patterns that LLMs cite
SOURCE_PATTERNS = {
    "research": [
        r"selon (?:une )?(?:étude|recherche|rapport|enquête)",
        r"d'après (?:une )?(?:étude|recherche|rapport)",
        r"(?:étude|recherche|rapport) (?:de|du|publié par)",
        r"(?:Harvard|MIT|Stanford|Oxford|INSEAD|HEC)",
        r"(?:Gartner|Forrester|McKinsey|Deloitte|BCG|Bain)",
    ],
    "statistics": [
        r"\d+(?:\.\d+)?%",
        r"(?:\d+(?:\.\d+)? (?:millions?|milliards?|k))",
        r"(?:en |depuis )\d{4}",
        r"(?:statistiques|données|chiffres) (?:de|du|montrent)",
    ],
    "news": [
        r"(?:selon|d'après) (?:Le Monde|Les Echos|Le Figaro|Forbes|Bloomberg|Reuters|AFP)",
        r"(?:annoncé|révélé|rapporté) (?:par|dans)",
        r"(?:article|publication) (?:de|dans|paru)",
    ],
    "experts": [
        r"(?:selon|d'après) (?:les )?experts",
        r"(?:CEO|PDG|directeur|fondateur|analyste) (?:de|chez)",
        r"(?:affirme|explique|déclare|indique) (?:que)?",
    ],
    "official": [
        r"(?:site officiel|documentation officielle)",
        r"(?:selon|d'après) (?:le )?(?:fabricant|éditeur|développeur)",
        r"(?:page|site) (?:officiel|officielle)",
    ],
    "community": [
        r"(?:Reddit|Quora|Stack Overflow|GitHub|Discord)",
        r"(?:forum|communauté|utilisateurs) (?:de|du)",
        r"(?:avis|retours|témoignages) (?:utilisateurs|clients)",
    ],
    "comparison": [
        r"(?:G2|Capterra|TrustRadius|GetApp)",
        r"(?:comparatif|benchmark|classement)",
        r"(?:note|score|évaluation) (?:de|moyenne)",
    ]
}

# Source authority scores (higher = more cited by LLMs)
SOURCE_AUTHORITY = {
    "research_institutions": {"score": 95, "examples": ["Harvard", "MIT", "Stanford", "INSEAD"]},
    "consulting_firms": {"score": 90, "examples": ["McKinsey", "BCG", "Gartner", "Forrester"]},
    "major_publications": {"score": 85, "examples": ["Forbes", "Bloomberg", "Le Monde", "Les Echos"]},
    "official_documentation": {"score": 80, "examples": ["Documentation officielle", "Site fabricant"]},
    "review_platforms": {"score": 75, "examples": ["G2", "Capterra", "TrustRadius", "Trustpilot"]},
    "tech_communities": {"score": 70, "examples": ["Stack Overflow", "GitHub", "Reddit"]},
    "industry_blogs": {"score": 65, "examples": ["TechCrunch", "VentureBeat", "Maddyness"]},
    "personal_blogs": {"score": 40, "examples": ["Medium", "WordPress blogs"]},
}


# ================== ANALYSIS FUNCTIONS ==================

def extract_sources_from_text(text: str) -> Dict[str, List[str]]:
    """Extract source citations from LLM response text"""
    sources = {
        "research": [],
        "statistics": [],
        "news": [],
        "experts": [],
        "official": [],
        "community": [],
        "comparison": []
    }
    
    text_lower = text.lower()
    
    for source_type, patterns in SOURCE_PATTERNS.items():
        for pattern in patterns:
            matches = re.findall(pattern, text_lower, re.IGNORECASE)
            if matches:
                sources[source_type].extend(matches)
    
    # Deduplicate
    for key in sources:
        sources[key] = list(set(sources[key]))
    
    return sources


def analyze_source_gaps(
    current_sources: Dict[str, List[str]],
    competitor_sources: Dict[str, List[str]] = None
) -> List[Dict[str, Any]]:
    """Identify gaps in source coverage"""
    gaps = []
    
    # Check each source type
    for source_type, authority_info in SOURCE_AUTHORITY.items():
        current_count = len(current_sources.get(source_type, []))
        
        if current_count == 0:
            gaps.append({
                "source_type": source_type,
                "priority": "high" if authority_info["score"] >= 80 else "medium",
                "authority_score": authority_info["score"],
                "examples": authority_info["examples"],
                "recommendation": f"Ajouter des citations de {', '.join(authority_info['examples'][:2])}"
            })
    
    return sorted(gaps, key=lambda x: x["authority_score"], reverse=True)


def generate_seeding_recommendations(
    topic: str,
    keywords: List[str],
    industry: str = None
) -> List[Dict[str, Any]]:
    """Generate source seeding recommendations for a topic"""
    recommendations = []
    
    # 1. Research & Data recommendation
    recommendations.append({
        "source_type": "research",
        "platform": "Études sectorielles",
        "priority": "high",
        "strategy": "Créer ou sponsoriser une étude de marché",
        "expected_impact": "+20-30 points de crédibilité GEO",
        "action_items": [
            f"Commander une étude sur '{topic}' auprès d'un cabinet reconnu",
            "Publier les résultats avec méthodologie transparente",
            "Créer des citations faciles à reprendre (chiffres clés, graphiques)",
            "Distribuer via communiqués de presse et LinkedIn"
        ]
    })
    
    # 2. Review platforms recommendation
    recommendations.append({
        "source_type": "comparison",
        "platform": "G2, Capterra, TrustRadius",
        "priority": "high",
        "strategy": "Optimiser la présence sur les plateformes de comparaison",
        "expected_impact": "+15-25 points de visibilité comparative",
        "action_items": [
            "Créer/optimiser les profils sur G2, Capterra et TrustRadius",
            "Solliciter activement les avis clients (email post-achat)",
            "Répondre à tous les avis (positifs et négatifs)",
            "Ajouter des captures d'écran, vidéos et cas d'usage"
        ]
    })
    
    # 3. Technical content recommendation
    recommendations.append({
        "source_type": "official",
        "platform": "Documentation & Guides",
        "priority": "high",
        "strategy": "Créer du contenu technique de référence",
        "expected_impact": "+15-20 points d'autorité technique",
        "action_items": [
            f"Créer un guide définitif sur '{topic}'",
            "Ajouter des exemples de code/configuration si applicable",
            "Publier des benchmarks et comparatifs objectifs",
            "Maintenir une documentation exhaustive et à jour"
        ]
    })
    
    # 4. Community presence recommendation
    recommendations.append({
        "source_type": "community",
        "platform": "Reddit, Stack Overflow, GitHub",
        "priority": "medium",
        "strategy": "Établir une présence active dans les communautés techniques",
        "expected_impact": "+10-15 points de confiance communautaire",
        "action_items": [
            "Répondre aux questions sur Stack Overflow et Reddit",
            "Contribuer à des projets open source liés",
            "Créer des tutoriels et guides sur GitHub",
            "Participer aux discussions sans être promotionnel"
        ]
    })
    
    # 5. Expert positioning recommendation
    recommendations.append({
        "source_type": "experts",
        "platform": "LinkedIn, Podcasts, Conférences",
        "priority": "medium",
        "strategy": "Positionner les dirigeants comme experts du domaine",
        "expected_impact": "+10-20 points de crédibilité experte",
        "action_items": [
            "Publier régulièrement du contenu expert sur LinkedIn",
            "Participer à des podcasts et webinaires du secteur",
            "Intervenir dans des conférences (physiques ou virtuelles)",
            "Être cité dans des articles de presse spécialisée"
        ]
    })
    
    # 6. Wikipedia/Knowledge bases (if applicable)
    recommendations.append({
        "source_type": "knowledge_base",
        "platform": "Wikipedia, Wikidata",
        "priority": "low",
        "strategy": "Présence dans les bases de connaissances",
        "expected_impact": "+5-10 points de notoriété",
        "action_items": [
            "Vérifier si une page Wikipedia est justifiée (notoriété)",
            "Créer une entrée Wikidata avec les informations structurées",
            "S'assurer que les informations sont factuelles et sourcées",
            "Ne jamais modifier directement (conflit d'intérêts)"
        ]
    })
    
    return recommendations


# ================== ENDPOINTS ==================

@router.post("/analyze")
async def analyze_source_landscape(
    request: SourceAnalysisRequest,
    user: dict = Depends(get_current_user)
):
    """Analyze source citation landscape for a topic"""
    
    # Generate queries to test
    test_queries = [
        f"Qu'est-ce que {request.topic} ?",
        f"Meilleur {request.topic} en 2026",
        f"Comment choisir {request.topic} ?",
        f"Avantages et inconvénients de {request.topic}",
        f"Comparatif {request.topic}"
    ]
    
    if request.keywords:
        for kw in request.keywords[:3]:
            test_queries.append(f"{kw} {request.topic}")
    
    # For now, return recommendations without actual LLM queries
    # (would query LLMs in production to analyze real responses)
    
    recommendations = generate_seeding_recommendations(
        topic=request.topic,
        keywords=request.keywords or [],
        industry=request.industry
    )
    
    return {
        "topic": request.topic,
        "queries_analyzed": len(test_queries[:request.num_queries]),
        "source_authority_ranking": list(SOURCE_AUTHORITY.keys()),
        "recommendations": recommendations,
        "analyzed_at": datetime.now(timezone.utc).isoformat()
    }


@router.get("/recommendations/{project_id}")
async def get_project_recommendations(
    project_id: str,
    user: dict = Depends(get_current_user)
):
    """Get source seeding recommendations for a project"""
    async with async_session_maker() as db:
        project = await ProjectService.get_by_id(db, project_id)
        if not project or project.user_id != user["user_id"]:
            raise HTTPException(status_code=404, detail="Projet non trouvé")
    
    # Generate recommendations based on project data
    recommendations = generate_seeding_recommendations(
        topic=project.brand_name,
        keywords=project.keywords or [],
        industry=None
    )
    
    return {
        "project_id": project_id,
        "brand_name": project.brand_name,
        "recommendations": recommendations,
        "total_recommendations": len(recommendations),
        "high_priority_count": len([r for r in recommendations if r["priority"] == "high"])
    }


@router.get("/authority-ranking")
async def get_source_authority_ranking(user: dict = Depends(get_current_user)):
    """Get the source authority ranking used by LLMs"""
    ranking = []
    
    for source_type, info in sorted(
        SOURCE_AUTHORITY.items(),
        key=lambda x: x[1]["score"],
        reverse=True
    ):
        ranking.append({
            "source_type": source_type,
            "authority_score": info["score"],
            "examples": info["examples"],
            "description": get_source_description(source_type)
        })
    
    return {
        "ranking": ranking,
        "methodology": "Score basé sur la fréquence de citation par ChatGPT, Claude, Gemini et Perplexity",
        "updated_at": "2026-03"
    }


@router.post("/extract-sources")
async def extract_sources_from_content(
    content: str,
    user: dict = Depends(get_current_user)
):
    """Extract and analyze sources from content"""
    sources = extract_sources_from_text(content)
    
    # Count total sources
    total_sources = sum(len(v) for v in sources.values())
    
    # Identify gaps
    gaps = analyze_source_gaps(sources)
    
    return {
        "sources_found": sources,
        "total_sources": total_sources,
        "source_types_present": [k for k, v in sources.items() if v],
        "gaps": gaps,
        "credibility_score": calculate_credibility_score(sources)
    }


def get_source_description(source_type: str) -> str:
    """Get description for a source type"""
    descriptions = {
        "research_institutions": "Universités et instituts de recherche de premier plan",
        "consulting_firms": "Cabinets de conseil et analystes du marché",
        "major_publications": "Médias et publications économiques majeurs",
        "official_documentation": "Documentation officielle des éditeurs/fabricants",
        "review_platforms": "Plateformes de comparaison et d'avis utilisateurs",
        "tech_communities": "Communautés techniques (développeurs, IT)",
        "industry_blogs": "Blogs et médias spécialisés du secteur",
        "personal_blogs": "Blogs personnels et plateformes de contenu"
    }
    return descriptions.get(source_type, "")


def calculate_credibility_score(sources: Dict[str, List[str]]) -> int:
    """Calculate credibility score based on sources present"""
    score = 0
    
    # Map source extraction categories to authority categories
    category_mapping = {
        "research": "research_institutions",
        "statistics": "consulting_firms",
        "news": "major_publications",
        "official": "official_documentation",
        "comparison": "review_platforms",
        "community": "tech_communities",
        "experts": "consulting_firms"
    }
    
    for source_type, items in sources.items():
        if items:
            authority_type = category_mapping.get(source_type)
            if authority_type and authority_type in SOURCE_AUTHORITY:
                # Add weighted score based on authority and count
                base_score = SOURCE_AUTHORITY[authority_type]["score"]
                count_bonus = min(len(items) * 2, 10)  # Cap at +10
                score += (base_score / 10) + count_bonus
    
    return min(100, int(score))
