"""
Content Gap & Opportunity Finder Engine
Identifies content gaps and opportunities from GEO analysis
"""
from typing import List, Dict, Any
from collections import defaultdict
import logging

logger = logging.getLogger(__name__)


class ContentGapEngine:
    """
    Engine for identifying content gaps and opportunities.
    Analyzes where competitors dominate and brand is weak/absent.
    """
    
    def __init__(self):
        pass
    
    def analyze_gaps(
        self,
        queries: List[Dict[str, Any]],
        responses: List[Dict[str, Any]],
        brand_name: str,
        competitors: List[str] = None
    ) -> Dict[str, Any]:
        """
        Analyze content gaps from query/response data.
        
        Returns:
        - Topics where brand is absent but competitors present
        - High-value queries with no brand mention
        - Quick wins (easy opportunities)
        """
        competitors = competitors or []
        brand_lower = brand_name.lower()
        competitor_lowers = [c.lower() for c in competitors]
        
        gaps = []
        opportunities = []
        quick_wins = []
        
        topic_performance = defaultdict(lambda: {
            "brand_mentions": 0,
            "competitor_mentions": 0,
            "total_queries": 0,
            "queries": []
        })
        
        for i, query in enumerate(queries):
            response = responses[i] if i < len(responses) else {}
            response_text = (response.get("response_excerpt", "") or "").lower()
            intent_type = query.get("intent_type", "informational")
            query_text = query.get("text", "")
            
            # Check brand and competitor presence
            brand_present = brand_lower in response_text
            competitors_present = any(c in response_text for c in competitor_lowers)
            
            # Track topic performance
            topic_performance[intent_type]["total_queries"] += 1
            topic_performance[intent_type]["queries"].append(query_text)
            
            if brand_present:
                topic_performance[intent_type]["brand_mentions"] += 1
            if competitors_present:
                topic_performance[intent_type]["competitor_mentions"] += 1
            
            # Identify gap: competitor present but brand absent
            if competitors_present and not brand_present:
                gap_score = self._calculate_gap_score(query, response)
                
                gaps.append({
                    "query": query_text,
                    "intent_type": intent_type,
                    "gap_score": gap_score,
                    "competitors_mentioned": [c for c in competitors if c.lower() in response_text],
                    "recommendation": self._generate_gap_recommendation(query, intent_type)
                })
            
            # Identify opportunity: neither present
            elif not brand_present and not competitors_present:
                opp_score = self._calculate_opportunity_score(query, response)
                
                if opp_score > 50:
                    opportunities.append({
                        "query": query_text,
                        "intent_type": intent_type,
                        "opportunity_score": opp_score,
                        "reasoning": "Aucun concurrent majeur n'est cité - opportunité de se positionner",
                        "action": self._generate_opportunity_action(query, intent_type)
                    })
            
            # Identify quick win: brand mentioned but poorly positioned
            elif brand_present:
                position = self._estimate_position(response_text, brand_lower)
                if position > 3:  # Not in top 3
                    quick_wins.append({
                        "query": query_text,
                        "intent_type": intent_type,
                        "current_position": position,
                        "improvement_potential": "high" if position <= 5 else "medium",
                        "action": f"Améliorer le contenu lié à '{query_text[:50]}' pour remonter dans les recommandations"
                    })
        
        # Calculate topic gaps
        topic_gaps = []
        for topic, data in topic_performance.items():
            if data["total_queries"] > 0:
                brand_rate = data["brand_mentions"] / data["total_queries"]
                competitor_rate = data["competitor_mentions"] / data["total_queries"]
                
                if competitor_rate > brand_rate:
                    topic_gaps.append({
                        "topic": topic,
                        "brand_presence_rate": round(brand_rate * 100, 1),
                        "competitor_presence_rate": round(competitor_rate * 100, 1),
                        "gap_severity": "critical" if brand_rate < 0.2 else "high" if brand_rate < 0.4 else "medium",
                        "sample_queries": data["queries"][:3]
                    })
        
        # Sort by scores
        gaps.sort(key=lambda x: -x["gap_score"])
        opportunities.sort(key=lambda x: -x["opportunity_score"])
        topic_gaps.sort(key=lambda x: x["brand_presence_rate"])
        
        return {
            "content_gaps": gaps[:15],
            "opportunities": opportunities[:15],
            "quick_wins": quick_wins[:10],
            "topic_gaps": topic_gaps,
            "summary": {
                "total_gaps": len(gaps),
                "total_opportunities": len(opportunities),
                "total_quick_wins": len(quick_wins),
                "critical_topics": len([t for t in topic_gaps if t["gap_severity"] == "critical"])
            }
        }
    
    def _calculate_gap_score(self, query: Dict[str, Any], response: Dict[str, Any]) -> float:
        """Calculate gap severity score (0-100)"""
        score = 50  # Base score
        
        # Intent type weight
        intent_weights = {
            "transactional": 30,
            "comparative": 25,
            "informational": 15,
            "local": 20,
            "exploratory": 10
        }
        score += intent_weights.get(query.get("intent_type", "informational"), 15)
        
        # Response quality indicator
        response_text = response.get("response_excerpt", "")
        if len(response_text) > 500:  # Detailed response
            score += 10
        
        return min(100, score)
    
    def _calculate_opportunity_score(self, query: Dict[str, Any], response: Dict[str, Any]) -> float:
        """Calculate opportunity value score (0-100)"""
        score = 40  # Base score
        
        # Intent type weight (transactional = higher opportunity)
        intent_weights = {
            "transactional": 25,
            "comparative": 20,
            "informational": 15,
            "local": 20,
            "exploratory": 10
        }
        score += intent_weights.get(query.get("intent_type", "informational"), 15)
        
        # Query quality score if available
        if query.get("quality_score", 0) > 70:
            score += 15
        
        return min(100, score)
    
    def _estimate_position(self, response_text: str, brand: str) -> int:
        """Estimate brand position in response (1 = first mention)"""
        if brand not in response_text:
            return 99
        
        # Find position relative to text length
        pos = response_text.find(brand)
        text_len = len(response_text)
        
        if text_len == 0:
            return 99
        
        relative_pos = pos / text_len
        
        if relative_pos < 0.15:
            return 1
        elif relative_pos < 0.30:
            return 2
        elif relative_pos < 0.50:
            return 3
        elif relative_pos < 0.70:
            return 4
        else:
            return 5
    
    def _generate_gap_recommendation(self, query: Dict[str, Any], intent_type: str) -> str:
        """Generate specific recommendation for a content gap"""
        recommendations = {
            "transactional": "Créer une page de tarification ou landing page ciblant cette intention d'achat",
            "comparative": "Publier un comparatif détaillé ou une page 'alternative à [concurrent]'",
            "informational": "Créer un guide complet ou article de blog sur ce sujet",
            "local": "Optimiser la page locale / Google Business pour cette recherche",
            "exploratory": "Ajouter une section FAQ ou guide de recommandations"
        }
        return recommendations.get(intent_type, "Créer du contenu ciblant cette requête")
    
    def _generate_opportunity_action(self, query: Dict[str, Any], intent_type: str) -> str:
        """Generate action for an opportunity"""
        actions = {
            "transactional": "Créer une landing page optimisée pour les conversions",
            "comparative": "Publier un comparatif montrant vos avantages",
            "informational": "Créer un contenu éducatif de référence (guide, tutoriel)",
            "local": "Renforcer la présence locale et les avis",
            "exploratory": "Créer du contenu 'conseil' et FAQ"
        }
        return actions.get(intent_type, "Créer du contenu pertinent")
    
    def generate_action_plan(
        self,
        gaps: List[Dict[str, Any]],
        opportunities: List[Dict[str, Any]],
        quick_wins: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Generate a prioritized 30/60/90 day action plan.
        """
        action_plan = {
            "30_days": {
                "title": "Actions immédiates (30 jours)",
                "priority": "critical",
                "actions": []
            },
            "60_days": {
                "title": "Actions court-terme (60 jours)",
                "priority": "high",
                "actions": []
            },
            "90_days": {
                "title": "Actions moyen-terme (90 jours)",
                "priority": "medium",
                "actions": []
            }
        }
        
        # Quick wins go to 30 days
        for qw in quick_wins[:5]:
            action_plan["30_days"]["actions"].append({
                "type": "quick_win",
                "action": qw["action"],
                "query": qw["query"],
                "expected_impact": "Amélioration de position rapide"
            })
        
        # High-score gaps go to 30-60 days
        for gap in gaps[:5]:
            if gap["gap_score"] >= 70:
                action_plan["30_days"]["actions"].append({
                    "type": "content_gap",
                    "action": gap["recommendation"],
                    "query": gap["query"],
                    "competitors": gap["competitors_mentioned"]
                })
            else:
                action_plan["60_days"]["actions"].append({
                    "type": "content_gap",
                    "action": gap["recommendation"],
                    "query": gap["query"]
                })
        
        # Opportunities go to 60-90 days
        for opp in opportunities[:5]:
            if opp["opportunity_score"] >= 70:
                action_plan["60_days"]["actions"].append({
                    "type": "opportunity",
                    "action": opp["action"],
                    "query": opp["query"],
                    "reasoning": opp["reasoning"]
                })
            else:
                action_plan["90_days"]["actions"].append({
                    "type": "opportunity",
                    "action": opp["action"],
                    "query": opp["query"]
                })
        
        return action_plan


# Singleton instance
gap_engine = ContentGapEngine()
