"""
Competitive Intelligence Service
Analyzes competitor presence and performance in AI responses
"""
import re
from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


# Extended list of known brands across industries
KNOWN_BRANDS = [
    # Tech Giants
    "Apple", "Google", "Microsoft", "Amazon", "Meta", "Facebook", "IBM", "Oracle", "Salesforce",
    "Adobe", "SAP", "Cisco", "Intel", "AMD", "Nvidia", "Qualcomm",
    # Consumer Electronics
    "Samsung", "Sony", "LG", "Huawei", "Xiaomi", "OnePlus", "Oppo", "Vivo", "Realme",
    "Nokia", "Motorola", "Asus", "Acer", "Dell", "HP", "Lenovo", "MSI",
    # E-commerce & Marketplaces
    "Alibaba", "eBay", "Shopify", "Etsy", "Rakuten", "Cdiscount", "Fnac", "Darty",
    # Fashion & Retail
    "Nike", "Adidas", "Puma", "Zara", "H&M", "Uniqlo", "Gap", "Levis", "Primark",
    # Entertainment & Media
    "Netflix", "Disney", "HBO", "Spotify", "Apple Music", "YouTube", "TikTok", "Twitch",
    # Travel & Hospitality
    "Uber", "Airbnb", "Booking", "Expedia", "Tripadvisor", "Kayak", "Hotels.com",
    # Automotive
    "Tesla", "BMW", "Mercedes", "Audi", "Toyota", "Honda", "Ford", "Volkswagen", "Porsche", "Renault", "Peugeot", "Citroën",
    # Food & Beverage
    "Coca-Cola", "Pepsi", "McDonald's", "Starbucks", "KFC", "Burger King", "Subway",
    # Beauty & Personal Care
    "L'Oréal", "Sephora", "Estée Lauder", "Nivea", "Dove", "Garnier",
    # Home & Appliances
    "Dyson", "Philips", "Bosch", "Siemens", "IKEA", "Electrolux", "Whirlpool",
    # Sports & Outdoor
    "Decathlon", "Intersport", "Go Sport",
    # Telecom (French)
    "Orange", "SFR", "Bouygues", "Free", "Sosh", "RED", "B&You",
    # Finance & Insurance
    "PayPal", "Stripe", "Square", "Revolut", "N26", "Boursorama", "Fortuneo",
    # Software & SaaS
    "Slack", "Zoom", "Trello", "Asana", "Monday", "Notion", "Airtable", "HubSpot", "Mailchimp",
    "Zendesk", "Intercom", "Freshdesk", "Semrush", "Ahrefs", "Moz", "Majestic",
    # Cloud & Hosting
    "AWS", "Azure", "GCP", "OVH", "DigitalOcean", "Heroku", "Vercel", "Netlify",
    # AI & LLM Tools
    "ChatGPT", "OpenAI", "Claude", "Anthropic", "Gemini", "Perplexity", "Jasper", "Copy.ai"
]

# Common words to exclude from brand detection
COMMON_WORDS_FR_EN = {
    # French
    'le', 'la', 'les', 'un', 'une', 'des', 'du', 'de', 'et', 'ou', 'mais', 'donc',
    'il', 'elle', 'ils', 'elles', 'nous', 'vous', 'je', 'tu', 'ce', 'cette', 'ces',
    'qui', 'que', 'quoi', 'dont', 'où', 'est', 'sont', 'être', 'avoir', 'fait',
    'plus', 'moins', 'très', 'bien', 'peut', 'peuvent', 'doit', 'doivent',
    'meilleur', 'meilleure', 'meilleurs', 'meilleures', 'premier', 'première',
    # English
    'the', 'a', 'an', 'and', 'or', 'but', 'for', 'with', 'from', 'to', 'in', 'on',
    'also', 'just', 'like', 'such', 'some', 'many', 'most', 'other', 'another',
    # Generic terms
    'best', 'top', 'new', 'old', 'first', 'last', 'next', 'good', 'great',
    'free', 'online', 'digital', 'tool', 'tools', 'service', 'services',
    'solution', 'solutions', 'platform', 'software', 'app', 'application'
}


class CompetitiveIntelligenceEngine:
    """
    Engine for competitive intelligence analysis.
    Identifies and tracks competitor mentions across AI responses.
    """
    
    def identify_competitors(
        self,
        all_responses: List[Dict[str, Any]],
        brand_name: str,
        user_competitors: List[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Analyze all AI responses to identify competitors mentioned.
        Uses multiple strategies:
        1. Known brands database
        2. User-defined competitors tracking
        3. NLP-based entity extraction
        """
        user_competitors = user_competitors or []
        all_competitors = {}
        brand_lower = brand_name.lower()
        brand_words = set(brand_lower.split())
        total_responses = len(all_responses)
        
        def normalize_brand(name: str) -> str:
            return name.strip().title()
        
        def is_own_brand(candidate: str) -> bool:
            candidate_lower = candidate.lower()
            candidate_words = set(candidate_lower.split())
            
            if candidate_lower == brand_lower:
                return True
            if candidate_lower in brand_lower or brand_lower in candidate_lower:
                return True
            if brand_words and candidate_words:
                overlap = len(brand_words & candidate_words) / max(len(brand_words), len(candidate_words))
                if overlap > 0.5:
                    return True
            return False
        
        # Process each AI response
        for response in all_responses:
            response_text = response.get("response_excerpt", "") or response.get("full_response", "") or ""
            ai_type = response.get("ai_type", "unknown")
            
            if not response_text or len(response_text) < 50:
                continue
            
            response_lower = response_text.lower()
            
            # Strategy 1: Check known brands
            for brand in KNOWN_BRANDS:
                brand_check = brand.lower()
                
                if is_own_brand(brand):
                    continue
                
                if brand_check in response_lower:
                    count = response_lower.count(brand_check)
                    normalized = normalize_brand(brand)
                    
                    if normalized in all_competitors:
                        all_competitors[normalized]["mentions"] += count
                        all_competitors[normalized]["ai_sources"].add(ai_type)
                        all_competitors[normalized]["responses_containing"] += 1
                    else:
                        all_competitors[normalized] = {
                            "name": normalized,
                            "mentions": count,
                            "ai_sources": {ai_type},
                            "discovered": True,
                            "user_defined": False,
                            "responses_containing": 1
                        }
            
            # Strategy 2: Check user-defined competitors
            for comp in user_competitors:
                comp_lower = comp.lower()
                if comp_lower in response_lower:
                    normalized = normalize_brand(comp)
                    
                    if normalized in all_competitors:
                        all_competitors[normalized]["mentions"] += 1
                        all_competitors[normalized]["ai_sources"].add(ai_type)
                        all_competitors[normalized]["responses_containing"] += 1
                        all_competitors[normalized]["user_defined"] = True
                    else:
                        all_competitors[normalized] = {
                            "name": normalized,
                            "mentions": 1,
                            "ai_sources": {ai_type},
                            "discovered": False,
                            "user_defined": True,
                            "responses_containing": 1
                        }
            
            # Strategy 3: Extract potential brands using NLP patterns
            potential_brands = self._extract_potential_brands(response_text)
            for potential in potential_brands:
                potential_lower = potential.lower()
                
                if is_own_brand(potential):
                    continue
                
                if any(potential_lower == kb.lower() for kb in KNOWN_BRANDS):
                    continue
                
                if len(potential.split()) == 1 and len(potential) < 4:
                    continue
                
                normalized = normalize_brand(potential)
                
                # Only add if mentioned at least twice
                if response_lower.count(potential_lower) >= 2:
                    if normalized in all_competitors:
                        all_competitors[normalized]["mentions"] += 1
                        all_competitors[normalized]["ai_sources"].add(ai_type)
                        all_competitors[normalized]["responses_containing"] += 1
                    else:
                        all_competitors[normalized] = {
                            "name": normalized,
                            "mentions": 1,
                            "ai_sources": {ai_type},
                            "discovered": True,
                            "user_defined": False,
                            "responses_containing": 1
                        }
        
        # Calculate visibility scores and convert to list
        result = []
        for name, data in all_competitors.items():
            mentions = data["mentions"]
            responses_containing = data.get("responses_containing", 1)
            ai_sources_count = len(data["ai_sources"])
            
            # Visibility score calculation
            visibility_score = min(100, (
                (mentions * 3) +
                (responses_containing * 5) +
                (ai_sources_count * 10)
            ))
            
            presence_rate = round((responses_containing / max(total_responses, 1)) * 100, 1)
            
            result.append({
                "name": data["name"],
                "mentions": mentions,
                "ai_sources": list(data["ai_sources"]),
                "discovered": data["discovered"],
                "user_defined": data.get("user_defined", False),
                "visibility_score": visibility_score,
                "presence_rate": presence_rate,
                "responses_containing": responses_containing
            })
        
        # Sort by visibility score
        result.sort(key=lambda x: (-x["visibility_score"], -x["mentions"]))
        
        return result[:15]
    
    def _extract_potential_brands(self, text: str) -> List[str]:
        """Extract potential brand names using pattern matching"""
        potential = []
        
        # Find capitalized words that might be brands
        cap_pattern = r'\b([A-Z][a-zA-Z]{2,}(?:\s+[A-Z][a-zA-Z]+)?)\b'
        matches = re.findall(cap_pattern, text)
        
        for match in matches:
            match_lower = match.lower()
            if match_lower not in COMMON_WORDS_FR_EN and len(match) >= 3:
                potential.append(match)
        
        return potential
    
    def calculate_competitive_gap(
        self,
        all_responses: List[Dict[str, Any]],
        brand_name: str,
        competitors: List[str]
    ) -> Dict[str, Any]:
        """
        Calculate competitive gap analysis.
        Shows where brand is stronger/weaker vs competitors.
        """
        brand_lower = brand_name.lower()
        
        brand_stats = {
            "total_mentions": 0,
            "responses_with_mention": 0,
            "avg_position": 0,
            "top_positions": 0
        }
        
        competitor_stats = {comp: {
            "total_mentions": 0,
            "responses_with_mention": 0,
            "beats_brand": 0
        } for comp in competitors}
        
        positions = []
        
        for response in all_responses:
            response_text = (response.get("response_excerpt", "") or "").lower()
            
            # Brand analysis
            if brand_lower in response_text:
                brand_stats["total_mentions"] += response_text.count(brand_lower)
                brand_stats["responses_with_mention"] += 1
                
                pos = response_text.find(brand_lower)
                positions.append(pos / max(len(response_text), 1))
                
                if pos < len(response_text) * 0.2:
                    brand_stats["top_positions"] += 1
            
            # Competitor analysis
            brand_pos = response_text.find(brand_lower) if brand_lower in response_text else float('inf')
            
            for comp in competitors:
                comp_lower = comp.lower()
                if comp_lower in response_text:
                    competitor_stats[comp]["total_mentions"] += response_text.count(comp_lower)
                    competitor_stats[comp]["responses_with_mention"] += 1
                    
                    comp_pos = response_text.find(comp_lower)
                    if comp_pos < brand_pos:
                        competitor_stats[comp]["beats_brand"] += 1
        
        # Calculate average position
        brand_stats["avg_position"] = round(sum(positions) / len(positions), 3) if positions else 1.0
        
        # Calculate overall competitive position
        total_responses = len(all_responses)
        brand_presence = brand_stats["responses_with_mention"] / max(total_responses, 1)
        
        competitive_position = "dominant"
        threats = []
        opportunities = []
        
        for comp, stats in competitor_stats.items():
            comp_presence = stats["responses_with_mention"] / max(total_responses, 1)
            beat_rate = stats["beats_brand"] / max(stats["responses_with_mention"], 1) if stats["responses_with_mention"] > 0 else 0
            
            if comp_presence > brand_presence * 1.2:
                competitive_position = "challenged"
                threats.append({
                    "competitor": comp,
                    "presence_rate": round(comp_presence * 100, 1),
                    "beat_rate": round(beat_rate * 100, 1)
                })
            elif comp_presence < brand_presence * 0.5 and brand_presence > 0:
                opportunities.append({
                    "competitor": comp,
                    "gap": round((brand_presence - comp_presence) * 100, 1)
                })
        
        if len(threats) > len(competitors) / 2:
            competitive_position = "at_risk"
        
        return {
            "brand_stats": brand_stats,
            "competitor_stats": competitor_stats,
            "competitive_position": competitive_position,
            "threats": threats,
            "opportunities": opportunities,
            "total_responses_analyzed": total_responses
        }
    
    def generate_competitive_recommendations(
        self,
        gap_analysis: Dict[str, Any],
        brand_name: str
    ) -> List[Dict[str, Any]]:
        """Generate recommendations based on competitive analysis"""
        recommendations = []
        
        position = gap_analysis.get("competitive_position", "unknown")
        threats = gap_analysis.get("threats", [])
        opportunities = gap_analysis.get("opportunities", [])
        
        if position == "at_risk":
            recommendations.append({
                "priority": "critical",
                "category": "competitive",
                "title": "Position concurrentielle menacée",
                "description": f"{len(threats)} concurrent(s) dominent les résultats IA.",
                "actions": [
                    "Analyser la stratégie de contenu des leaders",
                    "Renforcer les points de différenciation",
                    "Accélérer la production de contenu autoritaire"
                ]
            })
        
        for threat in threats[:3]:
            recommendations.append({
                "priority": "high",
                "category": "competitor_response",
                "title": f"Répondre à {threat['competitor']}",
                "description": f"Présence de {threat['presence_rate']}%, devant votre marque dans {threat['beat_rate']}% des cas.",
                "actions": [
                    f"Créer du contenu comparatif {brand_name} vs {threat['competitor']}",
                    "Identifier les sources de citation de ce concurrent",
                    "Développer des avantages différenciateurs"
                ]
            })
        
        for opp in opportunities[:3]:
            recommendations.append({
                "priority": "medium",
                "category": "opportunity",
                "title": f"Capitaliser sur l'avance vs {opp['competitor']}",
                "description": f"Écart de {opp['gap']}% en votre faveur.",
                "actions": [
                    "Consolider la présence sur ce segment",
                    "Développer des contenus de leadership",
                    "Augmenter la fréquence des mentions"
                ]
            })
        
        return recommendations


# Singleton instance
competitive_intelligence_engine = CompetitiveIntelligenceEngine()
