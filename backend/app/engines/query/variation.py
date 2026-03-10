"""
Prompt Variation Engine
Generates diverse prompt variations with semantic deduplication
"""
import re
import hashlib
from typing import List, Dict, Any, Callable
import logging

logger = logging.getLogger(__name__)


# Variation transformers
def variation_short(query: str) -> str:
    """Short version of query"""
    if " - " in query:
        return query.split(" - ")[0]
    elif " : " in query:
        return query.split(" : ")[0]
    return query[:50] if len(query) > 50 else query


def variation_long(query: str) -> str:
    """Long detailed version"""
    suffixes = [
        " - avis détaillé et recommandations professionnelles",
        " : guide complet avec comparatif",
        " - conseils d'experts 2026",
        " avec retours d'expérience et témoignages"
    ]
    import random
    return query + random.choice(suffixes)


def variation_conversational(query: str) -> str:
    """Conversational tone"""
    prefixes = [
        "Salut ! ",
        "Bonjour, ",
        "Hello, j'aurais besoin d'aide : ",
        "Dis-moi, "
    ]
    suffixes = [
        " J'aimerais avoir ton avis.",
        " Qu'en penses-tu ?",
        " Tu peux m'aider ?",
        " Merci d'avance !"
    ]
    import random
    return random.choice(prefixes) + query + random.choice(suffixes)


def variation_question(query: str) -> str:
    """Question format"""
    if query.endswith("?"):
        return query
    return query + " ?"


def variation_recommendation(query: str) -> str:
    """Recommendation request format"""
    prefixes = [
        "Peux-tu me recommander : ",
        "Que me conseilles-tu pour : ",
        "J'ai besoin de recommandations : ",
        "Quelles sont tes suggestions pour : "
    ]
    import random
    return random.choice(prefixes) + query


def variation_comparative(query: str) -> str:
    """Comparative angle"""
    if "meilleur" in query.lower() or "vs" in query.lower():
        return query
    return f"Quels sont les meilleurs {query} en 2026 ?"


def variation_problem_oriented(query: str) -> str:
    """Problem-oriented phrasing"""
    prefixes = [
        "J'ai un problème avec ",
        "Je cherche une solution pour ",
        "Comment résoudre : ",
        "J'ai besoin d'aide pour "
    ]
    import random
    return random.choice(prefixes) + query


def variation_benefit_oriented(query: str) -> str:
    """Benefit-oriented phrasing"""
    suffixes = [
        " pour gagner du temps",
        " pour améliorer ma productivité",
        " pour réduire mes coûts",
        " pour augmenter mes ventes"
    ]
    import random
    return query + random.choice(suffixes)


# Available variation types
VARIATION_TYPES: Dict[str, Callable[[str], str]] = {
    "short": variation_short,
    "long": variation_long,
    "conversational": variation_conversational,
    "question": variation_question,
    "recommendation": variation_recommendation,
    "comparative": variation_comparative,
    "problem_oriented": variation_problem_oriented,
    "benefit_oriented": variation_benefit_oriented
}


class PromptVariationEngine:
    """
    Engine for generating diverse prompt variations.
    Includes semantic deduplication using text similarity.
    """
    
    def __init__(self, similarity_threshold: float = 0.85):
        self.similarity_threshold = similarity_threshold
        self.variation_cache: Dict[str, List[str]] = {}
    
    def generate_variations(
        self,
        queries: List[Dict[str, Any]],
        variation_types: List[str] = None,
        max_variations_per_query: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Generate variations for a list of queries.
        
        Args:
            queries: List of query dicts with 'text' field
            variation_types: Types of variations to generate
            max_variations_per_query: Max variations per original query
            
        Returns:
            Extended list with original + variations
        """
        if variation_types is None:
            variation_types = ["short", "long", "conversational"]
        
        all_queries = []
        seen_hashes = set()
        
        for query in queries:
            original_text = query.get("text", "")
            
            # Add original
            query_hash = self._hash_text(original_text)
            if query_hash not in seen_hashes:
                seen_hashes.add(query_hash)
                all_queries.append(query)
            
            # Generate variations
            variations_added = 0
            for var_type in variation_types:
                if variations_added >= max_variations_per_query:
                    break
                
                transformer = VARIATION_TYPES.get(var_type)
                if not transformer:
                    continue
                
                try:
                    varied_text = transformer(original_text)
                    
                    # Check for similarity/duplicates
                    var_hash = self._hash_text(varied_text)
                    if var_hash in seen_hashes:
                        continue
                    
                    if self._is_too_similar(varied_text, [q["text"] for q in all_queries]):
                        continue
                    
                    seen_hashes.add(var_hash)
                    
                    # Create variation query object
                    variation = {
                        **query,
                        "text": varied_text,
                        "original_text": original_text,
                        "variation_type": var_type
                    }
                    all_queries.append(variation)
                    variations_added += 1
                    
                except Exception as e:
                    logger.warning(f"Error generating {var_type} variation: {e}")
        
        return all_queries
    
    def _hash_text(self, text: str) -> str:
        """Generate hash for text deduplication"""
        normalized = self._normalize_for_comparison(text)
        return hashlib.md5(normalized.encode()).hexdigest()
    
    def _normalize_for_comparison(self, text: str) -> str:
        """Normalize text for comparison"""
        text = text.lower()
        text = re.sub(r'[^\w\s]', '', text)
        text = ' '.join(sorted(text.split()))  # Sort words for order-independent comparison
        return text
    
    def _is_too_similar(self, new_text: str, existing_texts: List[str]) -> bool:
        """Check if new text is too similar to existing ones"""
        new_normalized = self._normalize_for_comparison(new_text)
        new_words = set(new_normalized.split())
        
        for existing in existing_texts:
            existing_normalized = self._normalize_for_comparison(existing)
            existing_words = set(existing_normalized.split())
            
            # Jaccard similarity
            if not new_words or not existing_words:
                continue
                
            intersection = len(new_words & existing_words)
            union = len(new_words | existing_words)
            
            if union > 0:
                similarity = intersection / union
                if similarity > self.similarity_threshold:
                    return True
        
        return False
    
    def get_variation_stats(self, queries: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Get statistics about query variations"""
        stats = {
            "total_queries": len(queries),
            "original_queries": 0,
            "variations": {},
            "intent_distribution": {}
        }
        
        for query in queries:
            var_type = query.get("variation_type", "original")
            intent = query.get("intent_type", "unknown")
            
            if var_type == "original":
                stats["original_queries"] += 1
            
            stats["variations"][var_type] = stats["variations"].get(var_type, 0) + 1
            stats["intent_distribution"][intent] = stats["intent_distribution"].get(intent, 0) + 1
        
        return stats


# Singleton instance
variation_engine = PromptVariationEngine()
