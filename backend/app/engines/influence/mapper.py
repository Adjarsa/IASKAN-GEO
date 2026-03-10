"""
Influence Mapping Engine
Identifies influential sources and domains in AI responses
"""
import re
from typing import List, Dict, Any
from collections import defaultdict
from urllib.parse import urlparse
import logging

logger = logging.getLogger(__name__)


# Known influential domains by category
INFLUENTIAL_DOMAINS = {
    "tech_reviews": [
        "g2.com", "capterra.com", "trustpilot.com", "getapp.com", "softwareadvice.com",
        "techradar.com", "zdnet.com", "cnet.com", "pcmag.com", "tomsguide.com"
    ],
    "business_media": [
        "forbes.com", "entrepreneur.com", "inc.com", "businessinsider.com", "techcrunch.com",
        "lesechos.fr", "latribune.fr", "bfmtv.com", "usine-digitale.fr", "journaldunet.com"
    ],
    "industry_blogs": [
        "hubspot.com", "moz.com", "semrush.com", "ahrefs.com", "backlinko.com",
        "neilpatel.com", "searchengineland.com", "searchenginejournal.com"
    ],
    "directories": [
        "crunchbase.com", "angel.co", "clutch.co", "goodfirms.co", "appsumo.com"
    ],
    "social_proof": [
        "linkedin.com", "twitter.com", "facebook.com", "youtube.com", "reddit.com"
    ],
    "official_sources": [
        "wikipedia.org", "gov.fr", "europa.eu", "insee.fr"
    ]
}

# Reverse lookup for categorization
DOMAIN_CATEGORIES = {}
for category, domains in INFLUENTIAL_DOMAINS.items():
    for domain in domains:
        DOMAIN_CATEGORIES[domain] = category


class InfluenceMappingEngine:
    """
    Engine for mapping influential sources in AI responses.
    Identifies which domains/sources are most frequently cited and their impact.
    """
    
    def __init__(self):
        self.source_cache: Dict[str, Dict[str, Any]] = {}
    
    def analyze_responses(
        self,
        responses: List[Dict[str, Any]],
        brand_name: str
    ) -> Dict[str, Any]:
        """
        Analyze responses to map influential sources.
        
        Returns influence map with:
        - Top domains
        - Source categories
        - Brand co-occurrence
        - Cross-AI validation
        """
        all_sources = defaultdict(lambda: {
            "mentions": 0,
            "ai_sources": set(),
            "cooccurrence_with_brand": 0,
            "contexts": [],
            "urls": set()
        })
        
        brand_lower = brand_name.lower()
        
        for response in responses:
            response_text = response.get("response_excerpt", "") or response.get("text", "")
            ai_type = response.get("ai_type", "unknown")
            
            if not response_text:
                continue
            
            # Extract sources from this response
            sources = self._extract_sources(response_text)
            brand_mentioned = brand_lower in response_text.lower()
            
            for source in sources:
                domain = source["domain"]
                all_sources[domain]["mentions"] += 1
                all_sources[domain]["ai_sources"].add(ai_type)
                all_sources[domain]["urls"].add(source.get("url", domain))
                
                if brand_mentioned:
                    all_sources[domain]["cooccurrence_with_brand"] += 1
                
                if source.get("context"):
                    all_sources[domain]["contexts"].append(source["context"][:100])
        
        # Calculate influence scores and categorize
        influence_map = []
        category_stats = defaultdict(lambda: {"count": 0, "total_mentions": 0})
        
        for domain, data in all_sources.items():
            category = DOMAIN_CATEGORIES.get(domain, "other")
            ai_count = len(data["ai_sources"])
            
            # Influence score formula
            influence_score = min(100, (
                (data["mentions"] * 5) +
                (ai_count * 15) +  # Cross-AI bonus
                (data["cooccurrence_with_brand"] * 10) +
                (10 if category in ["tech_reviews", "business_media"] else 0)  # Authority bonus
            ))
            
            influence_map.append({
                "domain": domain,
                "mentions": data["mentions"],
                "ai_sources": list(data["ai_sources"]),
                "cross_ai_count": ai_count,
                "cooccurrence_with_brand": data["cooccurrence_with_brand"],
                "influence_score": influence_score,
                "category": category,
                "sample_urls": list(data["urls"])[:3],
                "sample_contexts": data["contexts"][:2]
            })
            
            category_stats[category]["count"] += 1
            category_stats[category]["total_mentions"] += data["mentions"]
        
        # Sort by influence score
        influence_map.sort(key=lambda x: -x["influence_score"])
        
        return {
            "top_sources": influence_map[:20],
            "category_distribution": dict(category_stats),
            "total_unique_sources": len(influence_map),
            "cross_ai_sources": [s for s in influence_map if s["cross_ai_count"] >= 2][:10],
            "brand_cooccurrence_sources": [s for s in influence_map if s["cooccurrence_with_brand"] > 0][:10],
            "recommendations": self._generate_recommendations(influence_map, brand_name)
        }
    
    def _extract_sources(self, text: str) -> List[Dict[str, Any]]:
        """Extract URLs and domains from text"""
        sources = []
        
        # Extract full URLs
        url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'
        urls = re.findall(url_pattern, text)
        
        for url in urls:
            try:
                parsed = urlparse(url)
                domain = parsed.netloc.replace("www.", "")
                
                # Get context around URL
                url_pos = text.find(url)
                context_start = max(0, url_pos - 50)
                context_end = min(len(text), url_pos + len(url) + 50)
                context = text[context_start:context_end]
                
                sources.append({
                    "url": url,
                    "domain": domain,
                    "context": context
                })
            except Exception:
                continue
        
        # Extract domain mentions (without full URL)
        domain_pattern = r'\b([a-zA-Z0-9-]+\.(?:com|fr|io|org|net|co|eu))\b'
        domain_matches = re.findall(domain_pattern, text.lower())
        
        existing_domains = {s["domain"] for s in sources}
        for domain in domain_matches:
            if domain not in existing_domains:
                # Get context
                domain_pos = text.lower().find(domain)
                if domain_pos >= 0:
                    context_start = max(0, domain_pos - 50)
                    context_end = min(len(text), domain_pos + len(domain) + 50)
                    context = text[context_start:context_end]
                else:
                    context = ""
                
                sources.append({
                    "url": f"https://{domain}",
                    "domain": domain,
                    "context": context
                })
        
        return sources
    
    def _generate_recommendations(
        self,
        influence_map: List[Dict[str, Any]],
        brand_name: str
    ) -> List[Dict[str, Any]]:
        """Generate recommendations based on influence mapping"""
        recommendations = []
        
        # Find top sources where brand is NOT mentioned
        top_without_brand = [
            s for s in influence_map[:10] 
            if s["cooccurrence_with_brand"] == 0
        ]
        
        for source in top_without_brand[:5]:
            recommendations.append({
                "priority": "high",
                "type": "presence",
                "action": f"Obtenir une présence sur {source['domain']}",
                "reason": f"Source influente (score: {source['influence_score']}) citée par {source['cross_ai_count']} IA sans mention de votre marque",
                "category": source["category"]
            })
        
        # Check category gaps
        present_categories = {s["category"] for s in influence_map if s["cooccurrence_with_brand"] > 0}
        important_categories = ["tech_reviews", "business_media", "industry_blogs"]
        
        for category in important_categories:
            if category not in present_categories:
                recommendations.append({
                    "priority": "medium",
                    "type": "category_gap",
                    "action": f"Développer présence dans la catégorie '{category}'",
                    "reason": "Votre marque n'est pas associée à cette catégorie influente",
                    "suggested_sources": INFLUENTIAL_DOMAINS.get(category, [])[:5]
                })
        
        return recommendations
    
    def get_influence_graph(
        self,
        influence_map: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Generate data for influence graph visualization.
        Nodes are sources, edges represent co-citation.
        """
        nodes = []
        edges = []
        
        for i, source in enumerate(influence_map[:30]):
            nodes.append({
                "id": source["domain"],
                "label": source["domain"],
                "value": source["influence_score"],
                "category": source["category"],
                "color": self._category_color(source["category"])
            })
        
        # Simple edge creation based on category
        for i, s1 in enumerate(influence_map[:30]):
            for j, s2 in enumerate(influence_map[:30]):
                if i < j and s1["category"] == s2["category"]:
                    edges.append({
                        "source": s1["domain"],
                        "target": s2["domain"],
                        "value": 1
                    })
        
        return {"nodes": nodes, "edges": edges}
    
    def _category_color(self, category: str) -> str:
        """Get color for category in visualizations"""
        colors = {
            "tech_reviews": "#7c3aed",
            "business_media": "#06b6d4",
            "industry_blogs": "#10b981",
            "directories": "#f59e0b",
            "social_proof": "#ec4899",
            "official_sources": "#6366f1",
            "other": "#94a3b8"
        }
        return colors.get(category, "#94a3b8")


# Singleton instance
influence_engine = InfluenceMappingEngine()
