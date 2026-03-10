"""
Semantic Analysis Engine
Analyzes AI responses for semantic patterns, topics, and clusters
"""
import re
from typing import List, Dict, Any, Tuple
from collections import defaultdict
import logging

logger = logging.getLogger(__name__)


# Topic categories for French market
TOPIC_CATEGORIES = {
    "pricing": ["prix", "tarif", "coût", "budget", "gratuit", "abonnement", "forfait", "offre"],
    "features": ["fonctionnalité", "feature", "outil", "option", "capacité", "module"],
    "quality": ["qualité", "performance", "fiabilité", "robuste", "stable", "professionnel"],
    "support": ["support", "aide", "assistance", "service client", "accompagnement", "formation"],
    "ease_of_use": ["facile", "simple", "intuitif", "ergonomique", "accessible", "rapide"],
    "integration": ["intégration", "api", "connecteur", "compatible", "synchronisation", "import"],
    "security": ["sécurité", "sécurisé", "rgpd", "confidentiel", "chiffrement", "protection"],
    "scalability": ["évolutif", "scalable", "croissance", "flexible", "adaptable"],
    "innovation": ["innovant", "moderne", "nouveau", "dernière génération", "ia", "automatisation"],
    "trust": ["confiance", "fiable", "recommandé", "populaire", "leader", "expert", "certifié"]
}

# Sentiment keywords
POSITIVE_KEYWORDS = [
    "excellent", "meilleur", "recommandé", "populaire", "leader", "performant",
    "efficace", "fiable", "innovant", "intuitif", "puissant", "complet",
    "professionnel", "qualité", "simple", "rapide", "moderne", "flexible"
]

NEGATIVE_KEYWORDS = [
    "limité", "cher", "complexe", "difficile", "lent", "problème",
    "manque", "insuffisant", "obsolète", "basique", "restrictif"
]

# Brand role in response
BRAND_ROLES = {
    "leader": ["leader", "numéro 1", "premier", "meilleur", "référence", "incontournable"],
    "recommended": ["recommandé", "conseillé", "suggéré", "à considérer", "bon choix"],
    "alternative": ["alternative", "autre option", "concurrent", "aussi", "également"],
    "mentioned": ["mentionné", "cité", "évoqué", "existe"],
    "not_mentioned": []
}


class SemanticAnalysisEngine:
    """
    Engine for semantic analysis of AI responses.
    Extracts topics, sentiment, brand roles, and creates semantic clusters.
    """
    
    def __init__(self):
        self.topic_scores: Dict[str, float] = {}
    
    def analyze_response(
        self,
        response_text: str,
        brand_name: str,
        query_text: str = ""
    ) -> Dict[str, Any]:
        """
        Analyze a single AI response for semantic content.
        
        Returns comprehensive analysis with topics, sentiment, brand role, etc.
        """
        response_lower = response_text.lower()
        brand_lower = brand_name.lower()
        
        analysis = {
            "topics": self._extract_topics(response_lower),
            "sentiment": self._analyze_sentiment(response_lower),
            "brand_role": self._detect_brand_role(response_lower, brand_lower),
            "brand_context": self._extract_brand_context(response_text, brand_name),
            "key_arguments": self._extract_arguments(response_lower, brand_lower),
            "entities_mentioned": self._extract_entities(response_text),
            "sources_cited": self._extract_sources(response_text),
            "recommendation_strength": self._calculate_recommendation_strength(response_lower, brand_lower)
        }
        
        return analysis
    
    def analyze_batch(
        self,
        responses: List[Dict[str, Any]],
        brand_name: str
    ) -> Dict[str, Any]:
        """
        Analyze multiple responses and aggregate results.
        """
        all_topics = defaultdict(float)
        all_sentiments = {"positive": 0, "negative": 0, "neutral": 0}
        all_roles = defaultdict(int)
        all_arguments = defaultdict(int)
        total_recommendation_strength = 0
        
        for response in responses:
            response_text = response.get("response_excerpt", "") or response.get("text", "")
            if not response_text:
                continue
            
            analysis = self.analyze_response(response_text, brand_name)
            
            # Aggregate topics
            for topic, score in analysis["topics"].items():
                all_topics[topic] += score
            
            # Aggregate sentiment
            sentiment = analysis["sentiment"]["overall"]
            all_sentiments[sentiment] += 1
            
            # Aggregate roles
            role = analysis["brand_role"]["role"]
            all_roles[role] += 1
            
            # Aggregate arguments
            for arg in analysis["key_arguments"]:
                all_arguments[arg] += 1
            
            total_recommendation_strength += analysis["recommendation_strength"]
        
        # Normalize topic scores
        num_responses = len(responses) or 1
        normalized_topics = {k: round(v / num_responses, 2) for k, v in all_topics.items()}
        
        # Calculate topic coverage (how many topics the brand is associated with)
        topic_coverage = len([t for t, s in normalized_topics.items() if s > 0.3])
        
        return {
            "topic_distribution": dict(sorted(normalized_topics.items(), key=lambda x: -x[1])),
            "topic_coverage": topic_coverage,
            "sentiment_distribution": all_sentiments,
            "dominant_sentiment": max(all_sentiments, key=all_sentiments.get),
            "brand_role_distribution": dict(all_roles),
            "dominant_role": max(all_roles, key=all_roles.get) if all_roles else "not_mentioned",
            "common_arguments": dict(sorted(all_arguments.items(), key=lambda x: -x[1])[:10]),
            "avg_recommendation_strength": round(total_recommendation_strength / num_responses, 2),
            "total_responses_analyzed": num_responses
        }
    
    def create_semantic_clusters(
        self,
        queries: List[Dict[str, Any]],
        responses: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Create semantic clusters from queries and responses.
        Groups similar queries/topics together.
        """
        clusters = []
        
        # Group by intent type first
        intent_groups = defaultdict(list)
        for i, query in enumerate(queries):
            intent = query.get("intent_type", "informational")
            intent_groups[intent].append({
                "query": query,
                "response": responses[i] if i < len(responses) else {}
            })
        
        # Create cluster for each intent
        for intent, items in intent_groups.items():
            # Extract common topics for this cluster
            cluster_topics = defaultdict(float)
            cluster_keywords = set()
            
            for item in items:
                query_text = item["query"].get("text", "").lower()
                response_text = item["response"].get("response_excerpt", "").lower() if item["response"] else ""
                
                # Extract keywords from query
                words = re.findall(r'\b\w{4,}\b', query_text)
                cluster_keywords.update(words[:5])
                
                # Extract topics from response
                topics = self._extract_topics(response_text)
                for topic, score in topics.items():
                    cluster_topics[topic] += score
            
            # Normalize scores
            num_items = len(items) or 1
            cluster_topics = {k: round(v / num_items, 2) for k, v in cluster_topics.items()}
            
            clusters.append({
                "cluster_id": f"cluster_{intent}",
                "name": self._intent_to_cluster_name(intent),
                "intent_type": intent,
                "query_count": len(items),
                "keywords": list(cluster_keywords)[:10],
                "topics": dict(sorted(cluster_topics.items(), key=lambda x: -x[1])[:5]),
                "avg_score": sum(item["response"].get("score", 0) for item in items) / num_items if items else 0
            })
        
        return clusters
    
    def _extract_topics(self, text: str) -> Dict[str, float]:
        """Extract topic scores from text"""
        topics = {}
        
        for topic, keywords in TOPIC_CATEGORIES.items():
            score = 0
            for keyword in keywords:
                if keyword in text:
                    score += text.count(keyword) * 0.2
            topics[topic] = min(1.0, score)
        
        return {k: v for k, v in topics.items() if v > 0}
    
    def _analyze_sentiment(self, text: str) -> Dict[str, Any]:
        """Analyze sentiment of text"""
        positive_count = sum(1 for word in POSITIVE_KEYWORDS if word in text)
        negative_count = sum(1 for word in NEGATIVE_KEYWORDS if word in text)
        
        total = positive_count + negative_count
        if total == 0:
            return {"overall": "neutral", "positive_score": 0, "negative_score": 0}
        
        positive_score = positive_count / total
        negative_score = negative_count / total
        
        if positive_score > 0.6:
            overall = "positive"
        elif negative_score > 0.4:
            overall = "negative"
        else:
            overall = "neutral"
        
        return {
            "overall": overall,
            "positive_score": round(positive_score, 2),
            "negative_score": round(negative_score, 2),
            "positive_keywords_found": positive_count,
            "negative_keywords_found": negative_count
        }
    
    def _detect_brand_role(self, text: str, brand: str) -> Dict[str, Any]:
        """Detect what role the brand plays in the response"""
        if brand not in text:
            return {"role": "not_mentioned", "confidence": 1.0}
        
        # Find brand position and context
        brand_pos = text.find(brand)
        context_start = max(0, brand_pos - 100)
        context_end = min(len(text), brand_pos + len(brand) + 100)
        context = text[context_start:context_end]
        
        # Detect role based on context
        for role, indicators in BRAND_ROLES.items():
            if role == "not_mentioned":
                continue
            for indicator in indicators:
                if indicator in context:
                    return {"role": role, "confidence": 0.8, "indicator": indicator}
        
        return {"role": "mentioned", "confidence": 0.5}
    
    def _extract_brand_context(self, text: str, brand: str) -> List[str]:
        """Extract text snippets around brand mentions"""
        brand_lower = brand.lower()
        text_lower = text.lower()
        contexts = []
        
        start = 0
        while True:
            pos = text_lower.find(brand_lower, start)
            if pos == -1:
                break
            
            context_start = max(0, pos - 50)
            context_end = min(len(text), pos + len(brand) + 50)
            context = text[context_start:context_end].strip()
            
            # Clean up context
            context = re.sub(r'\s+', ' ', context)
            if context:
                contexts.append(f"...{context}...")
            
            start = pos + 1
        
        return contexts[:5]  # Max 5 contexts
    
    def _extract_arguments(self, text: str, brand: str) -> List[str]:
        """Extract key arguments/reasons mentioned about the brand"""
        arguments = []
        
        # Common argument patterns
        argument_patterns = [
            (r'(?:parce que?|car)\s+([^.]{10,50})', "reason"),
            (r'(?:grâce à|thanks to)\s+([^.]{10,50})', "benefit"),
            (r'(?:permet de|allows?)\s+([^.]{10,50})', "capability"),
            (r'(?:idéal pour|ideal for|parfait pour)\s+([^.]{10,30})', "use_case")
        ]
        
        for pattern, arg_type in argument_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches[:2]:
                arguments.append(match.strip())
        
        return arguments[:5]
    
    def _extract_entities(self, text: str) -> List[str]:
        """Extract named entities (brands, products, etc.)"""
        # Simple pattern for capitalized words (potential brands/products)
        pattern = r'\b([A-Z][a-zA-Z0-9]+(?:\s+[A-Z][a-zA-Z0-9]+)?)\b'
        matches = re.findall(pattern, text)
        
        # Filter common words
        skip_words = {"Le", "La", "Les", "Un", "Une", "Des", "Ce", "Cette", "The", "A", "An"}
        entities = [m for m in matches if m not in skip_words and len(m) > 2]
        
        return list(set(entities))[:10]
    
    def _extract_sources(self, text: str) -> List[str]:
        """Extract URLs and source references"""
        # URL pattern
        url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'
        urls = re.findall(url_pattern, text)
        
        # Domain pattern
        domain_pattern = r'\b([a-zA-Z0-9-]+\.(?:com|fr|io|org|net|co))\b'
        domains = re.findall(domain_pattern, text.lower())
        
        return list(set(urls + domains))[:10]
    
    def _calculate_recommendation_strength(self, text: str, brand: str) -> float:
        """Calculate how strongly the brand is recommended"""
        if brand not in text:
            return 0.0
        
        score = 0.3  # Base score for being mentioned
        
        # Strong recommendation indicators
        strong_indicators = ["recommandé", "conseillé", "meilleur choix", "numéro 1", "leader"]
        for indicator in strong_indicators:
            if indicator in text:
                score += 0.2
        
        # Position bonus (earlier mentions are better)
        brand_pos = text.find(brand)
        if brand_pos < len(text) * 0.2:
            score += 0.2
        elif brand_pos < len(text) * 0.4:
            score += 0.1
        
        return min(1.0, score)
    
    def _intent_to_cluster_name(self, intent: str) -> str:
        """Convert intent type to readable cluster name"""
        names = {
            "transactional": "Intentions d'achat",
            "comparative": "Comparaisons",
            "informational": "Recherche d'information",
            "local": "Recherche locale",
            "exploratory": "Exploration/Découverte"
        }
        return names.get(intent, intent.title())


# Singleton instance
semantic_engine = SemanticAnalysisEngine()
