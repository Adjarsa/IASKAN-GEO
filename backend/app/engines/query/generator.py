"""
Query Generation Engine
Generates intelligent, diverse queries for GEO analysis
"""
import random
from typing import List, Dict, Any, Optional
from datetime import datetime
import re
import logging

logger = logging.getLogger(__name__)


# Query type distribution for realistic simulation
QUERY_TYPE_DISTRIBUTION = {
    "transactional": 0.30,    # 30% - "acheter", "prix", "commander"
    "comparative": 0.25,      # 25% - "vs", "comparaison", "meilleur"
    "informational": 0.20,    # 20% - "qu'est-ce que", "comment"
    "local": 0.15,            # 15% - "près de moi", "en France"
    "exploratory": 0.10       # 10% - "recommandations", "suggestions"
}

# Query templates by type (French market focused)
QUERY_TEMPLATES = {
    "transactional": [
        "Acheter {keyword} - meilleur prix",
        "Commander {keyword} en ligne",
        "Où acheter {keyword} pas cher ?",
        "Prix {keyword} - comparatif",
        "Devis {keyword} professionnel",
        "Tarif {keyword} entreprise",
        "Abonnement {keyword} - offre",
        "Achat {keyword} B2B",
        "Obtenir {keyword} rapidement",
        "Solution {keyword} à télécharger"
    ],
    "comparative": [
        "Quel est le meilleur {keyword} ?",
        "{keyword} : comparaison des solutions",
        "Top 10 {keyword} en {year}",
        "Alternative à {competitor} pour {keyword}",
        "{brand} vs {competitor} : avis",
        "Comparatif {keyword} 2026",
        "Meilleur {keyword} qualité prix",
        "{keyword} : quel outil choisir ?",
        "Classement {keyword} entreprise",
        "Benchmark {keyword} B2B"
    ],
    "informational": [
        "Qu'est-ce que {keyword} ?",
        "Comment choisir un bon {keyword} ?",
        "Guide complet {keyword}",
        "Avis sur {keyword} - que vaut-il ?",
        "Avantages et inconvénients {keyword}",
        "Comment fonctionne {keyword} ?",
        "Pourquoi utiliser {keyword} ?",
        "Les bases de {keyword}",
        "Tutoriel {keyword} débutant",
        "Définition {keyword} et usages"
    ],
    "local": [
        "Meilleur {keyword} en France",
        "{keyword} entreprise française",
        "Solution {keyword} européenne",
        "{keyword} près de chez moi",
        "Fournisseur {keyword} local",
        "{keyword} Paris / Lyon / Marseille",
        "Agence {keyword} France",
        "Prestataire {keyword} francophone",
        "{keyword} made in France",
        "Expert {keyword} région"
    ],
    "exploratory": [
        "Je cherche un {keyword}, que recommandez-vous ?",
        "Suggestions pour {keyword}",
        "Quelle solution {keyword} pour mon entreprise ?",
        "Besoin de conseils sur {keyword}",
        "Recommandations {keyword} B2B",
        "Aide pour choisir {keyword}",
        "Quelles options pour {keyword} ?",
        "Conseils {keyword} startup",
        "Que pensez-vous de {keyword} ?",
        "Quel {keyword} pour PME ?"
    ]
}

# Industry-specific query additions
INDUSTRY_QUERIES = {
    "saas": [
        "Meilleur {keyword} SaaS",
        "Solution cloud {keyword}",
        "{keyword} en mode SaaS",
        "Logiciel {keyword} en ligne"
    ],
    "ecommerce": [
        "Plateforme {keyword} e-commerce",
        "{keyword} pour boutique en ligne",
        "Solution {keyword} Shopify",
        "Plugin {keyword} WooCommerce"
    ],
    "marketing": [
        "Outil {keyword} marketing",
        "Agence {keyword} digital",
        "Stratégie {keyword} 2026",
        "{keyword} automation marketing"
    ],
    "finance": [
        "Solution {keyword} fintech",
        "{keyword} secteur bancaire",
        "Logiciel {keyword} comptabilité",
        "{keyword} conformité RGPD"
    ],
    "healthcare": [
        "Solution {keyword} santé",
        "{keyword} médical certifié",
        "Logiciel {keyword} hôpital",
        "{keyword} télémédecine"
    ]
}

# Persona-based query modifiers
PERSONA_MODIFIERS = {
    "startup": ["startup", "jeune entreprise", "scale-up", "early stage"],
    "pme": ["PME", "petite entreprise", "TPE", "indépendant"],
    "enterprise": ["grande entreprise", "enterprise", "groupe", "multinationale"],
    "freelance": ["freelance", "auto-entrepreneur", "consultant", "indépendant"],
    "agency": ["agence", "prestataire", "cabinet", "société de services"]
}


class QueryGenerationEngine:
    """
    Engine for generating intelligent, diverse queries for GEO analysis.
    Uses templates, enrichment, and quality scoring.
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.year = datetime.now().year
    
    def generate_queries(
        self,
        brand_name: str,
        keywords: List[str],
        competitors: List[str] = None,
        num_queries: int = 50,
        industry: str = None,
        personas: List[Dict[str, Any]] = None,
        query_type_distribution: Dict[str, float] = None
    ) -> List[Dict[str, Any]]:
        """
        Generate diverse queries based on brand, keywords, and configuration.
        
        Returns list of query objects with metadata.
        """
        queries = []
        competitors = competitors or []
        personas = personas or []
        distribution = query_type_distribution or QUERY_TYPE_DISTRIBUTION
        
        # Calculate queries per type
        queries_per_type = {}
        for query_type, ratio in distribution.items():
            queries_per_type[query_type] = max(1, int(num_queries * ratio))
        
        # Generate queries for each type
        for query_type, count in queries_per_type.items():
            type_queries = self._generate_type_queries(
                query_type=query_type,
                brand_name=brand_name,
                keywords=keywords,
                competitors=competitors,
                count=count,
                industry=industry,
                personas=personas
            )
            queries.extend(type_queries)
        
        # Deduplicate and score
        queries = self._deduplicate_queries(queries)
        queries = self._score_queries(queries, brand_name, keywords)
        
        # Sort by quality score and limit
        queries.sort(key=lambda x: x.get("quality_score", 0), reverse=True)
        
        return queries[:num_queries]
    
    def _generate_type_queries(
        self,
        query_type: str,
        brand_name: str,
        keywords: List[str],
        competitors: List[str],
        count: int,
        industry: str = None,
        personas: List[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Generate queries for a specific type"""
        queries = []
        templates = QUERY_TEMPLATES.get(query_type, [])
        
        # Add industry-specific templates
        if industry and industry.lower() in INDUSTRY_QUERIES:
            templates = templates + INDUSTRY_QUERIES[industry.lower()]
        
        for i in range(count):
            # Select template
            template = random.choice(templates) if templates else "{keyword}"
            
            # Select keyword
            keyword = random.choice(keywords) if keywords else brand_name
            
            # Select competitor for comparative queries
            competitor = random.choice(competitors) if competitors else "concurrents"
            
            # Fill template
            query_text = template.format(
                keyword=keyword,
                brand=brand_name,
                competitor=competitor,
                year=self.year
            )
            
            # Add persona modifier sometimes
            persona_name = None
            if personas and random.random() < 0.3:
                persona = random.choice(personas)
                persona_name = persona.get("name", "")
                modifier = random.choice(persona.get("keywords", []) + [persona_name])
                if modifier:
                    query_text = f"{query_text} pour {modifier}"
            
            queries.append({
                "text": query_text,
                "original_text": query_text,
                "intent_type": query_type,
                "keyword": keyword,
                "persona": persona_name,
                "variation_type": "original"
            })
        
        return queries
    
    def _deduplicate_queries(self, queries: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate queries based on normalized text"""
        seen = set()
        unique_queries = []
        
        for query in queries:
            # Normalize for comparison
            normalized = self._normalize_text(query["text"])
            
            if normalized not in seen:
                seen.add(normalized)
                unique_queries.append(query)
        
        return unique_queries
    
    def _normalize_text(self, text: str) -> str:
        """Normalize text for deduplication"""
        text = text.lower()
        text = re.sub(r'[^\w\s]', '', text)
        text = ' '.join(text.split())
        return text
    
    def _score_queries(
        self,
        queries: List[Dict[str, Any]],
        brand_name: str,
        keywords: List[str]
    ) -> List[Dict[str, Any]]:
        """Score queries based on quality criteria"""
        for query in queries:
            score = 50  # Base score
            text = query["text"].lower()
            
            # Length score (optimal: 30-80 chars)
            length = len(query["text"])
            if 30 <= length <= 80:
                score += 15
            elif 20 <= length <= 100:
                score += 10
            
            # Contains keyword
            for kw in keywords:
                if kw.lower() in text:
                    score += 10
                    break
            
            # Natural language score
            if "?" in query["text"]:
                score += 5
            if any(word in text for word in ["comment", "pourquoi", "quel", "quoi"]):
                score += 5
            
            # Intent alignment
            intent = query["intent_type"]
            if intent == "comparative" and any(w in text for w in ["vs", "comparaison", "meilleur", "alternative"]):
                score += 10
            elif intent == "transactional" and any(w in text for w in ["acheter", "prix", "tarif", "commander"]):
                score += 10
            elif intent == "informational" and any(w in text for w in ["comment", "qu'est", "guide", "tutoriel"]):
                score += 10
            
            query["quality_score"] = min(100, score)
        
        return queries
    
    def import_custom_queries(
        self,
        custom_queries: List[str],
        default_intent: str = "informational"
    ) -> List[Dict[str, Any]]:
        """Import custom queries from user input"""
        queries = []
        
        for text in custom_queries:
            text = text.strip()
            if not text:
                continue
            
            # Auto-detect intent
            intent = self._detect_intent(text)
            
            queries.append({
                "text": text,
                "original_text": text,
                "intent_type": intent or default_intent,
                "keyword": "",
                "persona": None,
                "variation_type": "custom",
                "quality_score": 70  # Default score for custom queries
            })
        
        return queries
    
    def _detect_intent(self, text: str) -> str:
        """Auto-detect query intent from text"""
        text_lower = text.lower()
        
        if any(w in text_lower for w in ["acheter", "prix", "tarif", "commander", "devis", "abonnement"]):
            return "transactional"
        elif any(w in text_lower for w in ["vs", "comparaison", "comparer", "meilleur", "top", "alternative"]):
            return "comparative"
        elif any(w in text_lower for w in ["france", "français", "local", "près de", "région", "paris"]):
            return "local"
        elif any(w in text_lower for w in ["recommand", "suggestion", "conseil", "aide", "avis"]):
            return "exploratory"
        else:
            return "informational"


# Singleton instance
query_engine = QueryGenerationEngine()
