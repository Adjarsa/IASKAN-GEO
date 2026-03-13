"""
GEO Strategy Engine
Generates personalized optimization recommendations based on R.A.T.E scores
and creates actionable plans by category (Content, Technical, Authority, Engagement)
"""
from typing import Dict, List, Any, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class GEOStrategyEngine:
    """
    Engine to generate GEO optimization strategies based on analysis results.
    Uses R.A.T.E™ scoring methodology:
    - Relevance: How well content matches AI queries
    - Authority: Trust signals and expertise indicators
    - Thoroughness: Depth and completeness of content
    - Engagement: User interaction and freshness signals
    """
    
    # Priority thresholds
    CRITICAL_THRESHOLD = 40
    WARNING_THRESHOLD = 60
    GOOD_THRESHOLD = 80
    
    # Recommendation templates by category
    CONTENT_RECOMMENDATIONS = {
        "low_word_count": {
            "title": "Enrichir le contenu",
            "description": "Le contenu est trop court pour être considéré comme une source d'autorité par les LLMs.",
            "actions": [
                "Ajouter des sections détaillées sur les sous-thèmes clés",
                "Inclure des exemples concrets et des cas d'usage",
                "Développer une section FAQ complète"
            ],
            "impact": "high",
            "effort": "medium",
            "timeline": "2-4 semaines"
        },
        "missing_structure": {
            "title": "Améliorer la structure",
            "description": "Les LLMs préfèrent le contenu bien structuré avec des titres clairs.",
            "actions": [
                "Ajouter des sous-titres H2/H3 descriptifs",
                "Créer une table des matières",
                "Utiliser des listes à puces pour les points clés"
            ],
            "impact": "high",
            "effort": "low",
            "timeline": "1-2 jours"
        },
        "no_faq": {
            "title": "Ajouter une section FAQ",
            "description": "Les FAQs sont souvent citées directement par les LLMs.",
            "actions": [
                "Identifier les 5-10 questions les plus fréquentes",
                "Rédiger des réponses concises et précises",
                "Implémenter le schema FAQ structuré"
            ],
            "impact": "high",
            "effort": "medium",
            "timeline": "3-5 jours"
        },
        "weak_introduction": {
            "title": "Renforcer l'introduction",
            "description": "L'introduction doit résumer le contenu en 2-3 phrases citables.",
            "actions": [
                "Écrire un résumé concis dès le premier paragraphe",
                "Inclure les mots-clés principaux naturellement",
                "Répondre à la question principale immédiatement"
            ],
            "impact": "medium",
            "effort": "low",
            "timeline": "1 jour"
        },
        "no_definitions": {
            "title": "Ajouter des définitions claires",
            "description": "Les définitions explicites sont souvent extraites par les LLMs.",
            "actions": [
                "Définir les termes clés au début de l'article",
                "Utiliser le format 'X est Y qui Z'",
                "Ajouter le schema DefinedTerm"
            ],
            "impact": "medium",
            "effort": "low",
            "timeline": "1-2 jours"
        }
    }
    
    AUTHORITY_RECOMMENDATIONS = {
        "no_author": {
            "title": "Ajouter les informations auteur",
            "description": "L'attribution à un expert augmente la crédibilité auprès des LLMs.",
            "actions": [
                "Créer une bio auteur avec credentials",
                "Ajouter le schema Person/Author",
                "Lier vers les profils sociaux professionnels"
            ],
            "impact": "high",
            "effort": "low",
            "timeline": "1-2 jours"
        },
        "no_sources": {
            "title": "Citer des sources fiables",
            "description": "Les citations de sources autoritaires renforcent la confiance.",
            "actions": [
                "Ajouter des références à des études",
                "Citer des experts reconnus du domaine",
                "Inclure des liens vers des sources officielles"
            ],
            "impact": "high",
            "effort": "medium",
            "timeline": "1 semaine"
        },
        "outdated_content": {
            "title": "Mettre à jour le contenu",
            "description": "Les LLMs privilégient le contenu récemment mis à jour.",
            "actions": [
                "Actualiser les statistiques et données",
                "Revoir les informations obsolètes",
                "Afficher clairement la date de mise à jour"
            ],
            "impact": "high",
            "effort": "medium",
            "timeline": "2-3 jours"
        },
        "no_credentials": {
            "title": "Afficher les credentials",
            "description": "Les signaux d'expertise augmentent l'autorité perçue.",
            "actions": [
                "Mentionner les certifications pertinentes",
                "Ajouter les années d'expérience",
                "Inclure les publications ou récompenses"
            ],
            "impact": "medium",
            "effort": "low",
            "timeline": "1 jour"
        }
    }
    
    TECHNICAL_RECOMMENDATIONS = {
        "no_schema": {
            "title": "Implémenter le Schema.org",
            "description": "Les données structurées aident les LLMs à comprendre le contenu.",
            "actions": [
                "Ajouter Article schema",
                "Implémenter FAQ schema si applicable",
                "Ajouter Organization schema"
            ],
            "impact": "high",
            "effort": "medium",
            "timeline": "1-2 jours"
        },
        "slow_loading": {
            "title": "Optimiser la vitesse",
            "description": "Les pages rapides sont mieux indexées et crawlées.",
            "actions": [
                "Optimiser les images (WebP, lazy loading)",
                "Minifier CSS/JS",
                "Activer la mise en cache"
            ],
            "impact": "medium",
            "effort": "medium",
            "timeline": "1 semaine"
        },
        "no_meta": {
            "title": "Optimiser les meta tags",
            "description": "Les meta descriptions influencent les extraits LLM.",
            "actions": [
                "Écrire une meta description optimisée",
                "Ajouter les Open Graph tags",
                "Optimiser le title tag"
            ],
            "impact": "medium",
            "effort": "low",
            "timeline": "1 jour"
        },
        "mobile_issues": {
            "title": "Améliorer l'expérience mobile",
            "description": "Le contenu mobile-first est prioritaire pour les crawlers.",
            "actions": [
                "Vérifier la responsivité",
                "Optimiser la taille des polices",
                "Éviter les éléments non compatibles mobile"
            ],
            "impact": "medium",
            "effort": "medium",
            "timeline": "3-5 jours"
        }
    }
    
    ENGAGEMENT_RECOMMENDATIONS = {
        "no_cta": {
            "title": "Ajouter des calls-to-action",
            "description": "L'engagement utilisateur est un signal de qualité.",
            "actions": [
                "Ajouter des CTAs contextuels",
                "Proposer du contenu connexe",
                "Inclure des formulaires de contact"
            ],
            "impact": "medium",
            "effort": "low",
            "timeline": "1-2 jours"
        },
        "no_multimedia": {
            "title": "Enrichir avec du multimédia",
            "description": "Images et vidéos augmentent le temps passé sur la page.",
            "actions": [
                "Ajouter des images explicatives",
                "Créer des infographies",
                "Intégrer des vidéos explicatives"
            ],
            "impact": "medium",
            "effort": "high",
            "timeline": "2-4 semaines"
        },
        "no_internal_links": {
            "title": "Améliorer le maillage interne",
            "description": "Les liens internes distribuent l'autorité et aident la navigation.",
            "actions": [
                "Lier vers les articles connexes",
                "Créer des pillar pages",
                "Ajouter une navigation contextuelle"
            ],
            "impact": "medium",
            "effort": "low",
            "timeline": "2-3 jours"
        }
    }
    
    def __init__(self):
        self.recommendations_db = {
            "content": self.CONTENT_RECOMMENDATIONS,
            "authority": self.AUTHORITY_RECOMMENDATIONS,
            "technical": self.TECHNICAL_RECOMMENDATIONS,
            "engagement": self.ENGAGEMENT_RECOMMENDATIONS
        }
    
    def generate_strategy(self, analysis_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate a comprehensive GEO strategy based on analysis results.
        
        Args:
            analysis_result: The analysis data with scores and diagnostics
            
        Returns:
            Strategy with prioritized recommendations and action plan
        """
        try:
            # Extract scores
            scores = self._extract_scores(analysis_result)
            diagnostics = analysis_result.get("diagnostics", {})
            
            # Generate recommendations for each category
            recommendations = []
            
            # Content recommendations
            content_recs = self._generate_content_recommendations(scores, diagnostics)
            recommendations.extend(content_recs)
            
            # Authority recommendations
            authority_recs = self._generate_authority_recommendations(scores, diagnostics)
            recommendations.extend(authority_recs)
            
            # Technical recommendations
            technical_recs = self._generate_technical_recommendations(scores, diagnostics)
            recommendations.extend(technical_recs)
            
            # Engagement recommendations
            engagement_recs = self._generate_engagement_recommendations(scores, diagnostics)
            recommendations.extend(engagement_recs)
            
            # Sort by priority and impact
            recommendations = self._prioritize_recommendations(recommendations)
            
            # Generate action plan
            action_plan = self._generate_action_plan(recommendations, scores)
            
            # Generate summary
            summary = self._generate_summary(scores, recommendations)
            
            return {
                "success": True,
                "strategy": {
                    "scores": scores,
                    "summary": summary,
                    "recommendations": recommendations,
                    "action_plan": action_plan,
                    "quick_wins": self._get_quick_wins(recommendations),
                    "generated_at": datetime.utcnow().isoformat()
                }
            }
            
        except Exception as e:
            logger.error(f"Strategy generation error: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _extract_scores(self, analysis_result: Dict) -> Dict[str, float]:
        """Extract and normalize scores from analysis result."""
        scores = {}
        
        # Global score
        scores["global"] = analysis_result.get("global_score", 0)
        scores["grade"] = analysis_result.get("grade", "N/A")
        
        # R.A.T.E components
        rate_scores = analysis_result.get("rate_scores", {})
        scores["relevance"] = rate_scores.get("relevance", 0)
        scores["authority"] = rate_scores.get("authority", 0)
        scores["thoroughness"] = rate_scores.get("thoroughness", 0)
        scores["engagement"] = rate_scores.get("engagement", 0)
        
        # Additional metrics
        scores["visibility"] = analysis_result.get("visibility_score", 0)
        scores["citation_rate"] = analysis_result.get("citation_rate", 0)
        
        return scores
    
    def _generate_content_recommendations(
        self, 
        scores: Dict, 
        diagnostics: Dict
    ) -> List[Dict]:
        """Generate content-related recommendations."""
        recommendations = []
        
        thoroughness = scores.get("thoroughness", 50)
        relevance = scores.get("relevance", 50)
        
        # Check word count
        if thoroughness < 50:
            rec = self.CONTENT_RECOMMENDATIONS["low_word_count"].copy()
            rec["category"] = "content"
            rec["priority"] = "critical" if thoroughness < 30 else "high"
            rec["current_score"] = thoroughness
            recommendations.append(rec)
        
        # Check structure
        if diagnostics.get("structure_score", 100) < 60:
            rec = self.CONTENT_RECOMMENDATIONS["missing_structure"].copy()
            rec["category"] = "content"
            rec["priority"] = "high"
            rec["current_score"] = diagnostics.get("structure_score", 0)
            recommendations.append(rec)
        
        # Check FAQ
        if not diagnostics.get("has_faq", False):
            rec = self.CONTENT_RECOMMENDATIONS["no_faq"].copy()
            rec["category"] = "content"
            rec["priority"] = "high"
            recommendations.append(rec)
        
        # Check introduction
        if relevance < 60:
            rec = self.CONTENT_RECOMMENDATIONS["weak_introduction"].copy()
            rec["category"] = "content"
            rec["priority"] = "medium"
            rec["current_score"] = relevance
            recommendations.append(rec)
        
        # Check definitions
        if not diagnostics.get("has_definitions", False):
            rec = self.CONTENT_RECOMMENDATIONS["no_definitions"].copy()
            rec["category"] = "content"
            rec["priority"] = "medium"
            recommendations.append(rec)
        
        return recommendations
    
    def _generate_authority_recommendations(
        self, 
        scores: Dict, 
        diagnostics: Dict
    ) -> List[Dict]:
        """Generate authority-related recommendations."""
        recommendations = []
        
        authority = scores.get("authority", 50)
        
        # Check author
        if not diagnostics.get("has_author", False):
            rec = self.AUTHORITY_RECOMMENDATIONS["no_author"].copy()
            rec["category"] = "authority"
            rec["priority"] = "critical" if authority < 40 else "high"
            recommendations.append(rec)
        
        # Check sources
        if not diagnostics.get("has_sources", False) or diagnostics.get("source_count", 0) < 3:
            rec = self.AUTHORITY_RECOMMENDATIONS["no_sources"].copy()
            rec["category"] = "authority"
            rec["priority"] = "high"
            recommendations.append(rec)
        
        # Check freshness
        if diagnostics.get("days_since_update", 365) > 180:
            rec = self.AUTHORITY_RECOMMENDATIONS["outdated_content"].copy()
            rec["category"] = "authority"
            rec["priority"] = "high"
            recommendations.append(rec)
        
        # Check credentials
        if authority < 50 and not diagnostics.get("has_credentials", False):
            rec = self.AUTHORITY_RECOMMENDATIONS["no_credentials"].copy()
            rec["category"] = "authority"
            rec["priority"] = "medium"
            recommendations.append(rec)
        
        return recommendations
    
    def _generate_technical_recommendations(
        self, 
        scores: Dict, 
        diagnostics: Dict
    ) -> List[Dict]:
        """Generate technical recommendations."""
        recommendations = []
        
        # Check schema
        if not diagnostics.get("has_schema", False):
            rec = self.TECHNICAL_RECOMMENDATIONS["no_schema"].copy()
            rec["category"] = "technical"
            rec["priority"] = "high"
            recommendations.append(rec)
        
        # Check meta tags
        if not diagnostics.get("has_meta_description", False):
            rec = self.TECHNICAL_RECOMMENDATIONS["no_meta"].copy()
            rec["category"] = "technical"
            rec["priority"] = "medium"
            recommendations.append(rec)
        
        # Check mobile
        if diagnostics.get("mobile_score", 100) < 80:
            rec = self.TECHNICAL_RECOMMENDATIONS["mobile_issues"].copy()
            rec["category"] = "technical"
            rec["priority"] = "medium"
            rec["current_score"] = diagnostics.get("mobile_score", 0)
            recommendations.append(rec)
        
        return recommendations
    
    def _generate_engagement_recommendations(
        self, 
        scores: Dict, 
        diagnostics: Dict
    ) -> List[Dict]:
        """Generate engagement-related recommendations."""
        recommendations = []
        
        engagement = scores.get("engagement", 50)
        
        # Check multimedia
        if diagnostics.get("image_count", 0) < 2:
            rec = self.ENGAGEMENT_RECOMMENDATIONS["no_multimedia"].copy()
            rec["category"] = "engagement"
            rec["priority"] = "medium" if engagement > 40 else "high"
            recommendations.append(rec)
        
        # Check internal links
        if diagnostics.get("internal_link_count", 0) < 3:
            rec = self.ENGAGEMENT_RECOMMENDATIONS["no_internal_links"].copy()
            rec["category"] = "engagement"
            rec["priority"] = "medium"
            recommendations.append(rec)
        
        return recommendations
    
    def _prioritize_recommendations(self, recommendations: List[Dict]) -> List[Dict]:
        """Sort recommendations by priority and impact."""
        priority_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        impact_order = {"high": 0, "medium": 1, "low": 2}
        
        return sorted(
            recommendations,
            key=lambda x: (
                priority_order.get(x.get("priority", "low"), 3),
                impact_order.get(x.get("impact", "low"), 2)
            )
        )
    
    def _generate_action_plan(
        self, 
        recommendations: List[Dict], 
        scores: Dict
    ) -> Dict[str, Any]:
        """Generate a phased action plan."""
        plan = {
            "phase_1": {
                "name": "Quick Wins (1-7 jours)",
                "description": "Actions à impact rapide et faible effort",
                "actions": []
            },
            "phase_2": {
                "name": "Optimisations (2-4 semaines)",
                "description": "Améliorations structurelles importantes",
                "actions": []
            },
            "phase_3": {
                "name": "Stratégie Long Terme (1-3 mois)",
                "description": "Transformations profondes pour l'autorité",
                "actions": []
            }
        }
        
        for rec in recommendations:
            effort = rec.get("effort", "medium")
            impact = rec.get("impact", "medium")
            
            action = {
                "title": rec.get("title"),
                "category": rec.get("category"),
                "impact": impact,
                "actions": rec.get("actions", [])[:2]  # Top 2 actions
            }
            
            if effort == "low" and impact in ["high", "medium"]:
                plan["phase_1"]["actions"].append(action)
            elif effort == "medium" or (effort == "low" and impact == "low"):
                plan["phase_2"]["actions"].append(action)
            else:
                plan["phase_3"]["actions"].append(action)
        
        return plan
    
    def _get_quick_wins(self, recommendations: List[Dict]) -> List[Dict]:
        """Extract quick wins (low effort, high impact)."""
        return [
            r for r in recommendations
            if r.get("effort") == "low" and r.get("impact") in ["high", "medium"]
        ][:5]
    
    def _generate_summary(self, scores: Dict, recommendations: List[Dict]) -> Dict:
        """Generate an executive summary of the strategy."""
        global_score = scores.get("global", 0)
        
        # Determine overall status
        if global_score >= 80:
            status = "excellent"
            status_fr = "Excellent"
            message = "Votre contenu est bien optimisé pour les LLMs. Quelques ajustements peuvent encore améliorer votre visibilité."
        elif global_score >= 60:
            status = "good"
            status_fr = "Bon"
            message = "Votre contenu a un bon potentiel. Des optimisations ciblées peuvent significativement améliorer vos résultats."
        elif global_score >= 40:
            status = "needs_work"
            status_fr = "À améliorer"
            message = "Plusieurs aspects importants nécessitent votre attention pour améliorer la visibilité LLM."
        else:
            status = "critical"
            status_fr = "Critique"
            message = "Des actions urgentes sont nécessaires pour améliorer la visibilité de votre contenu."
        
        # Count recommendations by priority
        priority_counts = {}
        for rec in recommendations:
            priority = rec.get("priority", "medium")
            priority_counts[priority] = priority_counts.get(priority, 0) + 1
        
        # Identify main improvement areas
        categories = {}
        for rec in recommendations:
            cat = rec.get("category", "other")
            categories[cat] = categories.get(cat, 0) + 1
        
        main_focus = sorted(categories.items(), key=lambda x: x[1], reverse=True)[:2]
        
        return {
            "status": status,
            "status_label": status_fr,
            "global_score": global_score,
            "message": message,
            "total_recommendations": len(recommendations),
            "priority_breakdown": priority_counts,
            "main_focus_areas": [area[0] for area in main_focus],
            "estimated_improvement": min(30, len(recommendations) * 3)  # Estimated score improvement
        }
    
    def generate_from_scores(
        self,
        global_score: float,
        relevance: float = None,
        authority: float = None,
        thoroughness: float = None,
        engagement: float = None,
        diagnostics: Dict = None
    ) -> Dict[str, Any]:
        """
        Generate strategy from individual scores (simpler interface).
        """
        analysis_result = {
            "global_score": global_score,
            "rate_scores": {
                "relevance": relevance or global_score,
                "authority": authority or global_score * 0.9,
                "thoroughness": thoroughness or global_score * 0.95,
                "engagement": engagement or global_score * 0.85
            },
            "diagnostics": diagnostics or {}
        }
        
        return self.generate_strategy(analysis_result)
