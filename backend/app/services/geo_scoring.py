"""
GEO Scoring Service
Implements the IAskan Verified GEO Protocol scoring methodology
"""
from typing import Dict, List, Any
import logging

logger = logging.getLogger(__name__)


class GEOScoringEngine:
    """
    Engine for calculating GEO scores using the IAskan Verified GEO Protocol.
    
    Implements:
    - Stability Index: Measures consistency across multiple runs
    - Dominance Index: Measures brand position vs competitors
    - Trust Gap: Measures credibility vs competitors
    - Opportunity Score: Identifies improvement potential
    - R.A.T.E. Score: Relevance, Authority, Truthfulness, Endorsement
    """
    
    def calculate_stability_index(self, multi_run_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        IAskan Verified GEO Protocol - Stability Index
        Measures consistency of AI responses across multiple runs
        """
        if not multi_run_results or len(multi_run_results) < 2:
            return {"stability_score": 100.0, "variance": 0.0, "status": "insufficient_data"}
        
        # Group results by AI type
        ai_groups = {}
        for result in multi_run_results:
            ai_type = result.get("ai_type", "unknown")
            if ai_type not in ai_groups:
                ai_groups[ai_type] = []
            ai_groups[ai_type].append(result)
        
        stability_metrics = {
            "per_ai": {},
            "overall_variance": 0.0,
            "role_consistency": 0.0,
            "mention_consistency": 0.0
        }
        
        total_variance = 0
        total_groups = 0
        roles_consistent = 0
        mentions_consistent = 0
        
        for ai_type, results in ai_groups.items():
            if len(results) < 2:
                continue
            
            # Calculate role consistency
            roles = [r.get("role", "absent") for r in results]
            role_variance = len(set(roles)) / len(roles)
            
            # Calculate mention consistency
            mentions = [r.get("brand_mentioned", False) for r in results]
            mention_variance = len(set(mentions)) / len(mentions)
            
            # Calculate score variance
            scores = [r.get("role_score", 0) for r in results]
            avg_score = sum(scores) / len(scores)
            score_variance = sum((s - avg_score) ** 2 for s in scores) / len(scores)
            
            # Per-AI stability
            ai_stability = 100 - (role_variance * 30 + mention_variance * 30 + min(score_variance * 10, 40))
            
            stability_metrics["per_ai"][ai_type] = {
                "stability": round(max(0, ai_stability), 1),
                "role_variance": round(role_variance, 2),
                "mention_variance": round(mention_variance, 2),
                "runs_analyzed": len(results)
            }
            
            total_variance += (role_variance + mention_variance + score_variance) / 3
            total_groups += 1
            
            if role_variance < 0.5:
                roles_consistent += 1
            if mention_variance < 0.5:
                mentions_consistent += 1
        
        # Calculate overall stability
        if total_groups > 0:
            avg_variance = total_variance / total_groups
            stability_metrics["overall_variance"] = round(avg_variance, 3)
            stability_metrics["role_consistency"] = round((roles_consistent / total_groups) * 100, 1)
            stability_metrics["mention_consistency"] = round((mentions_consistent / total_groups) * 100, 1)
        
        # Final stability score (0-100)
        stability_score = 100 - (stability_metrics["overall_variance"] * 100)
        stability_score = max(0, min(100, stability_score))
        
        # Determine status
        if stability_score >= 80:
            status = "high"
        elif stability_score >= 60:
            status = "medium"
        else:
            status = "low"
        
        return {
            "stability_score": round(stability_score, 1),
            "variance": stability_metrics["overall_variance"],
            "status": status,
            "role_consistency": stability_metrics["role_consistency"],
            "mention_consistency": stability_metrics["mention_consistency"],
            "per_ai_stability": stability_metrics["per_ai"],
            "total_runs_analyzed": len(multi_run_results)
        }
    
    def calculate_advanced_indices(
        self,
        all_responses: List[Dict[str, Any]],
        brand_name: str,
        competitors: List[str]
    ) -> Dict[str, Any]:
        """
        IAskan Verified GEO Protocol - Advanced Indices Calculator
        Calculates: Stability Index, Dominance Index, Trust Gap, Opportunity Score
        """
        indices = {
            "stability_index": 0.0,
            "dominance_index": 0.0,
            "trust_gap": 0.0,
            "opportunity_score": 0.0
        }
        
        if not all_responses:
            return indices
        
        valid_responses = [r for r in all_responses if r.get("role") != "error"]
        if not valid_responses:
            return indices
        
        # ===== DOMINANCE INDEX =====
        # Measures how often brand appears before competitors
        dominance_scores = []
        for resp in valid_responses:
            if resp.get("brand_mentioned"):
                comp_analysis = resp.get("competitor_analysis", {})
                competitors_before = sum(1 for c, data in comp_analysis.items() if data.get("before_brand", False))
                total_comps = len(comp_analysis)
                if total_comps > 0:
                    dominance = 100 - (competitors_before / total_comps * 100)
                    dominance_scores.append(dominance)
        
        indices["dominance_index"] = round(sum(dominance_scores) / len(dominance_scores), 1) if dominance_scores else 0.0
        
        # ===== TRUST GAP =====
        # Measures credibility gap vs competitors
        brand_credibility = [r.get("credibility_score", 0) for r in valid_responses if r.get("brand_mentioned")]
        avg_brand_credibility = sum(brand_credibility) / len(brand_credibility) if brand_credibility else 0
        
        # Estimate competitor credibility
        competitor_mentions = 0
        for resp in valid_responses:
            comp_analysis = resp.get("competitor_analysis", {})
            competitor_mentions += sum(1 for c, data in comp_analysis.items() if data.get("mentioned", False))
        
        avg_competitor_presence = (competitor_mentions / (len(valid_responses) * len(competitors))) * 100 if competitors else 0
        indices["trust_gap"] = round(avg_brand_credibility - avg_competitor_presence, 1)
        
        # ===== OPPORTUNITY SCORE =====
        # Measures potential for improvement
        low_score_queries = sum(1 for r in valid_responses if r.get("role_score", 0) < 0.5)
        absent_queries = sum(1 for r in valid_responses if r.get("role") == "absent")
        
        opportunity_base = ((absent_queries + low_score_queries) / len(valid_responses)) * 100
        
        # Boost opportunity if competitors have weak presence too
        weak_competitor_queries = 0
        for resp in valid_responses:
            comp_analysis = resp.get("competitor_analysis", {})
            if all(not data.get("mentioned", False) for data in comp_analysis.values()):
                weak_competitor_queries += 1
        
        opportunity_boost = (weak_competitor_queries / len(valid_responses)) * 20 if valid_responses else 0
        indices["opportunity_score"] = round(min(100, opportunity_base + opportunity_boost), 1)
        
        return indices
    
    def calculate_rate_score(
        self,
        all_responses: List[Dict[str, Any]],
        stability_data: Dict[str, Any]
    ) -> Dict[str, float]:
        """
        IAskan Verified GEO Protocol - R.A.T.E. Score Calculator
        Weights: Relevance 30%, Authority 25%, Truthfulness 20%, Endorsement 25%
        """
        if not all_responses:
            return {"relevance": 0, "authority": 0, "truthfulness": 0, "endorsement": 0, "total": 0, "grade": "F"}
        
        valid_responses = [r for r in all_responses if r.get("role") != "error"]
        if not valid_responses:
            return {"relevance": 0, "authority": 0, "truthfulness": 0, "endorsement": 0, "total": 0, "grade": "F"}
        
        # ===== RELEVANCE (30%) =====
        mentioned = sum(1 for r in valid_responses if r.get("brand_mentioned", False))
        mention_rate = (mentioned / len(valid_responses)) * 100
        
        position_scores = [1 - r.get("position_ratio", 1) for r in valid_responses if r.get("brand_mentioned")]
        avg_position_score = (sum(position_scores) / len(position_scores)) * 100 if position_scores else 0
        
        relevance = (mention_rate * 0.6) + (avg_position_score * 0.4)
        
        # ===== AUTHORITY (25%) =====
        role_scores = [r.get("role_score", 0) for r in valid_responses]
        avg_role = (sum(role_scores) / len(role_scores)) * 100
        
        credibility_scores = [r.get("credibility_score", 50) for r in valid_responses if r.get("brand_mentioned")]
        avg_credibility = sum(credibility_scores) / len(credibility_scores) if credibility_scores else 50
        
        authority = (avg_role * 0.5) + (avg_credibility * 0.5)
        
        # ===== TRUTHFULNESS (20%) =====
        base_truthfulness = 85.0
        
        hallucination_penalties = sum(r.get("hallucination_penalty", 0) for r in valid_responses)
        truthfulness = max(0, base_truthfulness - (hallucination_penalties / len(valid_responses)))
        
        all_credibility_factors = []
        for r in valid_responses:
            all_credibility_factors.extend(r.get("credibility_factors", []))
        
        unique_factors = len(set(all_credibility_factors))
        truthfulness = min(100, truthfulness + (unique_factors * 2))
        
        # ===== ENDORSEMENT (25%) =====
        top_recs = sum(1 for r in valid_responses if r.get("role") == "top_recommendation")
        shortlists = sum(1 for r in valid_responses if r.get("role") == "shortlist")
        
        endorsement_base = ((top_recs * 2 + shortlists) / len(valid_responses)) * 100
        
        conversion_scores = [r.get("conversion_score", 0) for r in valid_responses if r.get("brand_mentioned")]
        avg_conversion = sum(conversion_scores) / len(conversion_scores) if conversion_scores else 0
        
        endorsement = (endorsement_base * 0.6) + (avg_conversion * 0.4)
        
        # ===== STABILITY ADJUSTMENT =====
        stability_score = stability_data.get("stability_score", 100)
        stability_factor = stability_score / 100
        
        # ===== TOTAL SCORE (Weighted) =====
        total = (
            relevance * 0.30 +
            authority * 0.25 +
            truthfulness * 0.20 +
            endorsement * 0.25
        ) * stability_factor
        
        # Determine grade
        if total >= 80:
            grade = "A"
        elif total >= 65:
            grade = "B"
        elif total >= 50:
            grade = "C"
        elif total >= 35:
            grade = "D"
        else:
            grade = "F"
        
        return {
            "relevance": round(relevance, 1),
            "authority": round(authority, 1),
            "truthfulness": round(truthfulness, 1),
            "endorsement": round(endorsement, 1),
            "total": round(total, 1),
            "grade": grade,
            "weights": {
                "relevance": "30%",
                "authority": "25%",
                "truthfulness": "20%",
                "endorsement": "25%"
            }
        }
    
    def calculate_ai_scores(self, all_responses: List[Dict[str, Any]]) -> Dict[str, float]:
        """Calculate individual AI engine scores"""
        ai_scores = {}
        ai_groups = {}
        
        for resp in all_responses:
            ai_type = resp.get("ai_type", "unknown")
            if ai_type not in ai_groups:
                ai_groups[ai_type] = []
            ai_groups[ai_type].append(resp)
        
        for ai_type, responses in ai_groups.items():
            valid = [r for r in responses if r.get("role") != "error"]
            if not valid:
                ai_scores[ai_type] = 0.0
                continue
            
            # Calculate mention rate
            mentioned = sum(1 for r in valid if r.get("brand_mentioned", False))
            mention_rate = (mentioned / len(valid)) * 100
            
            # Calculate average role score
            role_scores = [r.get("role_score", 0) for r in valid]
            avg_role = (sum(role_scores) / len(role_scores)) * 100
            
            # Combined score
            ai_scores[ai_type] = round((mention_rate * 0.5 + avg_role * 0.5), 1)
        
        return ai_scores
    
    def generate_recommendations(
        self,
        rate_score: Dict[str, float],
        ai_scores: Dict[str, float],
        indices: Dict[str, Any],
        stability_data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Generate actionable, prioritized recommendations based on analysis.
        """
        recommendations = []
        
        total_score = rate_score.get("total", 0)
        
        # Critical recommendations (score < 40)
        if total_score < 40:
            recommendations.append({
                "priority": "critical",
                "category": "visibility",
                "title": "Amélioration urgente de la visibilité IA",
                "description": f"Score global de {total_score}/100. Actions immédiates requises.",
                "actions": [
                    "Créer du contenu optimisé pour les requêtes IA",
                    "Renforcer la présence sur les sources citées par les LLMs",
                    "Développer une stratégie de contenu citable"
                ],
                "impact": "high",
                "effort": "medium"
            })
        
        # Relevance recommendations
        if rate_score.get("relevance", 0) < 50:
            recommendations.append({
                "priority": "high",
                "category": "relevance",
                "title": "Augmenter le taux de mention",
                "description": f"Pertinence à {rate_score.get('relevance', 0)}%. Votre marque n'apparaît pas assez.",
                "actions": [
                    "Diversifier les mots-clés ciblés",
                    "Créer du contenu pour différents types d'intentions",
                    "Optimiser la présence sur les plateformes d'avis"
                ],
                "impact": "high",
                "effort": "medium"
            })
        
        # Authority recommendations
        if rate_score.get("authority", 0) < 50:
            recommendations.append({
                "priority": "high",
                "category": "authority",
                "title": "Renforcer l'autorité de la marque",
                "description": f"Autorité à {rate_score.get('authority', 0)}%. Positionnement à améliorer.",
                "actions": [
                    "Obtenir des citations sur des sources autoritaires",
                    "Développer le thought leadership",
                    "Créer des études de cas et témoignages"
                ],
                "impact": "high",
                "effort": "high"
            })
        
        # AI-specific recommendations
        for ai_type, score in ai_scores.items():
            if score < 30:
                recommendations.append({
                    "priority": "medium",
                    "category": "ai_optimization",
                    "title": f"Optimiser pour {ai_type.title()}",
                    "description": f"Score {ai_type}: {score}%. Faible visibilité sur ce moteur.",
                    "actions": [
                        f"Analyser les sources préférées de {ai_type.title()}",
                        "Adapter le format de contenu",
                        "Augmenter la fréquence des mentions"
                    ],
                    "impact": "medium",
                    "effort": "medium"
                })
        
        # Stability recommendations
        stability_score = stability_data.get("stability_score", 100)
        if stability_score < 70:
            recommendations.append({
                "priority": "medium",
                "category": "stability",
                "title": "Améliorer la stabilité des réponses",
                "description": f"Stabilité à {stability_score}%. Résultats variables.",
                "actions": [
                    "Consolider le contenu de référence",
                    "Renforcer la cohérence des informations",
                    "Multiplier les sources de citation"
                ],
                "impact": "medium",
                "effort": "low"
            })
        
        # Opportunity recommendations
        opportunity = indices.get("opportunity_score", 0)
        if opportunity > 60:
            recommendations.append({
                "priority": "medium",
                "category": "opportunity",
                "title": "Exploiter les opportunités détectées",
                "description": f"Score d'opportunité: {opportunity}%. Potentiel de croissance.",
                "actions": [
                    "Cibler les requêtes sans concurrent dominant",
                    "Créer du contenu pour les niches identifiées",
                    "Développer une stratégie de différenciation"
                ],
                "impact": "high",
                "effort": "medium"
            })
        
        # Sort by priority
        priority_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        recommendations.sort(key=lambda x: priority_order.get(x.get("priority", "low"), 4))
        
        return recommendations[:10]  # Return top 10


# Singleton instance
geo_scoring_engine = GEOScoringEngine()
