"""
LLM Connector Service
Centralized service for querying multiple LLM providers
Part of the IAskan Verified GEO Protocol

UPDATED: March 2026 - Real Perplexity API integration (sonar-pro)
"""
import asyncio
import logging
import os
import httpx
from typing import Dict, List, Any, Optional
from datetime import datetime, timezone
import uuid
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger(__name__)

# Thread pool for LLM calls to avoid blocking the event loop
llm_executor = ThreadPoolExecutor(max_workers=4)

# LLM Model Configuration
LLM_CONFIG = {
    "chatgpt": {
        "provider": "openai",
        "model": "gpt-4o",
        "display_name": "ChatGPT"
    },
    "claude": {
        "provider": "anthropic", 
        "model": "claude-sonnet-4-5-20250929",
        "display_name": "Claude"
    },
    "gemini": {
        "provider": "gemini",
        "model": "gemini-2.0-flash",
        "display_name": "Gemini"
    },
    "perplexity": {
        "provider": "perplexity",  # FIXED: Real Perplexity API
        "model": "sonar-pro",       # FIXED: sonar-pro model
        "display_name": "Perplexity",
        "api_base": "https://api.perplexity.ai"
    }
}

# Default system message for GEO analysis
GEO_SYSTEM_MESSAGE = """Tu es un assistant intelligent qui répond aux questions des utilisateurs de manière naturelle, 
objective et informative. Réponds en mentionnant les marques, entreprises ou solutions pertinentes si applicable. 
Sois précis et factuel dans tes recommandations."""


def get_api_key():
    """Get the API key for LLM calls"""
    return os.environ.get('EMERGENT_LLM_KEY') or os.environ.get('OPENAI_API_KEY')


def get_perplexity_api_key():
    """Get the Perplexity API key"""
    return os.environ.get('PERPLEXITY_API_KEY')


class LLMConnector:
    """
    Service for connecting to multiple LLM providers.
    Handles model configuration, request execution, and error handling.
    """
    
    def __init__(self, api_key: str = None, system_message: str = None):
        self.api_key = api_key or get_api_key()
        self.system_message = system_message or GEO_SYSTEM_MESSAGE
        self._using_emergent = False
        self._init_llm_backend()
    
    def _init_llm_backend(self):
        """Initialize LLM backend - try emergentintegrations first, fallback to OpenAI"""
        try:
            from emergentintegrations.llm.chat import LlmChat, UserMessage
            self._LlmChat = LlmChat
            self._UserMessage = UserMessage
            self._using_emergent = True
            logger.info("LLMConnector: Using emergentintegrations")
        except ImportError:
            import openai
            self._openai = openai
            self._using_emergent = False
            logger.info("LLMConnector: Using native OpenAI SDK")
    
    async def query_llm(
        self,
        query_text: str,
        ai_type: str = "chatgpt",
        run_id: int = 1,
        brand_name: str = "",
        competitors: List[str] = None
    ) -> Dict[str, Any]:
        """
        Query a single LLM and return the response with brand analysis.
        """
        competitors = competitors or []
        
        try:
            config = LLM_CONFIG.get(ai_type, LLM_CONFIG["chatgpt"])
            session_id = f"geo_{ai_type}_{uuid.uuid4().hex[:8]}_{run_id}"
            
            # Special handling for Perplexity - use real Perplexity API
            if config.get("provider") == "perplexity":
                response_text = await self._query_with_perplexity(query_text, config)
            elif self._using_emergent:
                # Use emergentintegrations for other providers
                response_text = await self._query_with_emergent(query_text, config, session_id)
            else:
                # Use native OpenAI SDK
                response_text = await self._query_with_openai(query_text, config)
            
            # Analyze response for brand and competitor mentions
            analysis = self._analyze_response(
                response_text=response_text,
                brand_name=brand_name,
                competitors=competitors
            )
            
            return {
                "ai_type": ai_type,
                "run_id": run_id,
                "query_text": query_text[:200],
                "response_excerpt": response_text[:500],
                "response_length": len(response_text),
                "full_response": response_text,
                **analysis,
                "analyzed_at": datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error querying {ai_type} (run {run_id}): {e}")
            return {
                "ai_type": ai_type,
                "run_id": run_id,
                "error": str(e),
                "brand_mentioned": False,
                "role": "error",
                "role_score": 0.0,
                "credibility_score": 0.0,
                "conversion_score": 0.0
            }
    
    async def _query_with_emergent(self, query_text: str, config: dict, session_id: str) -> str:
        """Query using emergentintegrations - async native"""
        chat = self._LlmChat(
            api_key=self.api_key,
            session_id=session_id,
            system_message=self.system_message
        )
        chat.with_model(config["provider"], config["model"])
        
        user_message = self._UserMessage(text=query_text)
        
        # Use send_message directly if it's async, otherwise wrap properly
        try:
            # Try async method first
            if hasattr(chat, 'send_message_async'):
                response = await chat.send_message_async(user_message)
            else:
                # Fallback: run sync method in executor without nested asyncio.run
                loop = asyncio.get_event_loop()
                response = await loop.run_in_executor(
                    llm_executor,
                    lambda: chat.send_message_sync(user_message) if hasattr(chat, 'send_message_sync') else str(chat.send_message(user_message))
                )
        except Exception as e:
            logger.warning(f"Emergent LLM error, trying alternative: {e}")
            # Fallback to OpenAI if emergent fails
            return await self._query_with_openai(query_text, config)
        
        return response if isinstance(response, str) else str(response)
    
    async def _query_with_openai(self, query_text: str, config: dict) -> str:
        """Query using native OpenAI SDK"""
        client = self._openai.OpenAI(api_key=self.api_key)
        
        # Run in thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        
        def sync_call():
            response = client.chat.completions.create(
                model=config.get("model", "gpt-4o"),
                messages=[
                    {"role": "system", "content": self.system_message},
                    {"role": "user", "content": query_text}
                ],
                max_tokens=1000
            )
            return response.choices[0].message.content
        
        return await loop.run_in_executor(llm_executor, sync_call)
    
    async def _query_with_perplexity(self, query_text: str, config: dict) -> str:
        """Query using real Perplexity API (sonar-pro model)"""
        perplexity_key = get_perplexity_api_key()
        
        if not perplexity_key:
            logger.warning("Perplexity API key not found, falling back to OpenAI")
            return await self._query_with_openai(query_text, {"model": "gpt-4o-mini"})
        
        api_base = config.get("api_base", "https://api.perplexity.ai")
        model = config.get("model", "sonar-pro")
        
        headers = {
            "Authorization": f"Bearer {perplexity_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": self.system_message},
                {"role": "user", "content": query_text}
            ],
            "max_tokens": 1000,
            "temperature": 0.7
        }
        
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{api_base}/chat/completions",
                    headers=headers,
                    json=payload
                )
                response.raise_for_status()
                data = response.json()
                
                # Extract response text
                if "choices" in data and len(data["choices"]) > 0:
                    content = data["choices"][0].get("message", {}).get("content", "")
                    logger.info(f"Perplexity API response received ({len(content)} chars)")
                    return content
                else:
                    logger.error(f"Unexpected Perplexity response format: {data}")
                    return "Error: Unexpected response format from Perplexity"
                    
        except httpx.HTTPStatusError as e:
            logger.error(f"Perplexity API HTTP error: {e.response.status_code} - {e.response.text}")
            raise
        except httpx.RequestError as e:
            logger.error(f"Perplexity API connection error: {e}")
            raise
        except Exception as e:
            logger.error(f"Perplexity API error: {e}")
            raise
    
    async def query_all_llms(
        self,
        query_text: str,
        brand_name: str,
        competitors: List[str] = None,
        ai_types: List[str] = None,
        run_id: int = 1
    ) -> List[Dict[str, Any]]:
        """
        Query multiple LLMs in parallel.
        
        Args:
            query_text: The query to send
            brand_name: Brand to analyze
            competitors: List of competitors
            ai_types: List of AI types to query (default: ['chatgpt', 'claude', 'gemini'])
            run_id: Run identifier
            
        Returns:
            List of response dicts from each LLM
        """
        ai_types = ai_types or ["chatgpt", "claude", "gemini"]
        
        tasks = [
            self.query_llm(
                query_text=query_text,
                ai_type=ai_type,
                run_id=run_id,
                brand_name=brand_name,
                competitors=competitors
            )
            for ai_type in ai_types
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Handle any exceptions
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                processed_results.append({
                    "ai_type": ai_types[i],
                    "run_id": run_id,
                    "error": str(result),
                    "brand_mentioned": False
                })
            else:
                processed_results.append(result)
        
        return processed_results
    
    def _analyze_response(
        self,
        response_text: str,
        brand_name: str,
        competitors: List[str]
    ) -> Dict[str, Any]:
        """
        Analyze LLM response for brand presence, role, credibility, and conversion signals.
        
        Implements the 4-layer IAskan Verified GEO Protocol:
        - Layer 1: Presence Analysis
        - Layer 2: Role Analysis  
        - Layer 3: Credibility Analysis
        - Layer 4: Conversion Analysis
        
        UPDATED Sprint C: Enhanced brand detection with variants and fuzzy matching
        """
        response_lower = response_text.lower()
        brand_lower = brand_name.lower() if brand_name else ""
        response_length = len(response_lower)
        
        # ===== LAYER 1: ENHANCED PRESENCE ANALYSIS (Sprint C) =====
        brand_detection = self._detect_brand_advanced(response_lower, brand_name)
        brand_mentioned = brand_detection["mentioned"]
        mention_count = brand_detection["mention_count"]
        first_position = brand_detection["first_position"]
        position_ratio = (first_position / response_length) if brand_mentioned and response_length > 0 else 1.0
        detection_method = brand_detection["detection_method"]
        variants_found = brand_detection["variants_found"]
        brand_lower = brand_name.lower() if brand_name else ""
        
        # ===== LAYER 2: ROLE ANALYSIS =====
        role, role_score = self._analyze_role(response_lower, brand_lower, first_position, position_ratio)
        
        # ===== LAYER 3: CREDIBILITY ANALYSIS =====
        credibility_score, credibility_factors = self._analyze_credibility(response_lower, brand_mentioned)
        
        # ===== LAYER 4: CONVERSION ANALYSIS =====
        conversion_score, conversion_signals = self._analyze_conversion(response_lower, brand_mentioned, role)
        
        # ===== ANTI-HALLUCINATION CHECK =====
        hallucination_flags, hallucination_penalty = self._check_hallucination(response_lower, brand_mentioned)
        
        # ===== COMPETITOR ANALYSIS =====
        competitor_positions = self._analyze_competitors(response_lower, competitors, first_position, response_length, brand_mentioned)
        
        return {
            # Layer 1: Presence (Enhanced Sprint C)
            "brand_mentioned": brand_mentioned,
            "mention_count": mention_count,
            "first_position": first_position,
            "position_ratio": round(position_ratio, 3),
            "detection_method": detection_method,
            "variants_found": variants_found,
            # Layer 2: Role
            "role": role,
            "role_score": round(role_score, 2),
            # Layer 3: Credibility
            "credibility_score": round(credibility_score, 1),
            "credibility_factors": credibility_factors,
            # Layer 4: Conversion
            "conversion_score": round(conversion_score, 1),
            "conversion_signals": conversion_signals,
            # Anti-hallucination
            "hallucination_flags": hallucination_flags,
            "hallucination_penalty": hallucination_penalty,
            # Competitors
            "competitor_analysis": competitor_positions
        }
    
    def _detect_brand_advanced(self, response_lower: str, brand_name: str) -> Dict[str, Any]:
        """
        Enhanced brand detection using multiple methods (Sprint C)
        
        Detection hierarchy:
        1. Exact match
        2. Case-insensitive variants (Title, UPPER, etc.)
        3. Acronym detection (e.g., "CRM" for "Customer Relationship Management")
        4. Common typos and phonetic variants
        5. Word boundary matching (prevents "brand" matching "rebranding")
        """
        if not brand_name:
            return {
                "mentioned": False,
                "mention_count": 0,
                "first_position": -1,
                "detection_method": "none",
                "variants_found": []
            }
        
        brand_lower = brand_name.lower()
        variants_found = []
        first_position = -1
        total_mentions = 0
        detection_method = "not_found"
        
        # Generate brand variants
        variants = self._generate_brand_variants(brand_name)
        
        # Check each variant
        for variant, var_type in variants:
            var_lower = variant.lower()
            if var_lower in response_lower:
                count = response_lower.count(var_lower)
                total_mentions += count
                variants_found.append({"variant": variant, "type": var_type, "count": count})
                
                # Track first position
                pos = response_lower.find(var_lower)
                if first_position == -1 or pos < first_position:
                    first_position = pos
                    detection_method = var_type
        
        # Additional: Word boundary check for exact brand name
        import re
        word_pattern = r'\b' + re.escape(brand_lower) + r'\b'
        word_matches = re.findall(word_pattern, response_lower)
        if word_matches and not variants_found:
            total_mentions = len(word_matches)
            first_position = response_lower.find(brand_lower)
            detection_method = "word_boundary"
            variants_found.append({"variant": brand_name, "type": "word_boundary", "count": len(word_matches)})
        
        return {
            "mentioned": total_mentions > 0,
            "mention_count": total_mentions,
            "first_position": first_position,
            "detection_method": detection_method,
            "variants_found": variants_found
        }
    
    def _generate_brand_variants(self, brand_name: str) -> List[tuple]:
        """
        Generate brand name variants for detection
        Returns list of (variant, type) tuples
        """
        variants = []
        brand_lower = brand_name.lower()
        
        # 1. Exact match
        variants.append((brand_name, "exact"))
        variants.append((brand_lower, "lowercase"))
        variants.append((brand_name.upper(), "uppercase"))
        variants.append((brand_name.title(), "titlecase"))
        
        # 2. Without spaces (for multi-word brands)
        if ' ' in brand_name:
            no_space = brand_name.replace(' ', '')
            variants.append((no_space, "no_space"))
            # CamelCase variant
            camel = ''.join(word.capitalize() for word in brand_name.split())
            variants.append((camel, "camelcase"))
        
        # 3. Acronym (first letter of each word)
        if ' ' in brand_name:
            words = brand_name.split()
            if len(words) >= 2:
                acronym = ''.join(w[0].upper() for w in words)
                if len(acronym) >= 2:
                    variants.append((acronym, "acronym"))
        
        # 4. Common typos (missing double letters, swapped letters)
        for i, char in enumerate(brand_lower):
            if i > 0 and brand_lower[i] == brand_lower[i-1]:
                # Try without the double letter
                typo = brand_lower[:i] + brand_lower[i+1:]
                if len(typo) >= 3:
                    variants.append((typo, "typo_double"))
        
        # 5. With/without common suffixes
        suffixes_to_remove = ['.com', '.fr', '.ai', '.io', ' inc', ' corp', ' ltd']
        for suffix in suffixes_to_remove:
            if brand_lower.endswith(suffix):
                base = brand_name[:-len(suffix)]
                variants.append((base, "no_suffix"))
        
        # 6. Phonetic variants (common substitutions)
        phonetic_subs = [('ph', 'f'), ('f', 'ph'), ('c', 'k'), ('k', 'c')]
        for old, new in phonetic_subs:
            if old in brand_lower:
                phonetic = brand_lower.replace(old, new)
                variants.append((phonetic, "phonetic"))
        
        return variants
    
    def _analyze_role(
        self,
        response_lower: str,
        brand_lower: str,
        first_position: int,
        position_ratio: float
    ) -> tuple:
        """Analyze what role the brand plays in the response"""
        if not brand_lower or brand_lower not in response_lower:
            return "absent", 0.0
        
        response_length = len(response_lower)
        
        # Analyze surrounding context
        context_start = max(0, first_position - 100)
        context_end = min(response_length, first_position + 200)
        context = response_lower[context_start:context_end]
        
        # Role indicators
        top_indicators = ["meilleur", "leader", "recommande", "premier", "numéro 1", "#1", "top", "incontournable", "référence"]
        shortlist_indicators = ["également", "aussi", "autre option", "alternative", "parmi les", "fait partie"]
        comparison_indicators = ["comparé", "versus", "vs", "face à", "contrairement", "différent"]
        negative_indicators = ["éviter", "déconseille", "problème", "inconvénient", "moins bon", "attention"]
        
        has_top = any(ind in context for ind in top_indicators)
        has_shortlist = any(ind in context for ind in shortlist_indicators)
        has_comparison = any(ind in context for ind in comparison_indicators)
        has_negative = any(ind in context for ind in negative_indicators)
        
        if has_negative:
            return "discouraged", 0.1
        elif position_ratio < 0.15 and has_top:
            return "top_recommendation", 1.0
        elif position_ratio < 0.30 and (has_top or has_shortlist):
            return "shortlist", 0.85
        elif position_ratio < 0.50 or has_shortlist:
            return "comparison", 0.60
        elif has_comparison:
            return "mentioned", 0.40
        else:
            return "cited", 0.25
    
    def _analyze_credibility(self, response_lower: str, brand_mentioned: bool) -> tuple:
        """Analyze credibility signals in the response"""
        credibility_score = 50.0  # Base score
        credibility_factors = []
        
        if not brand_mentioned:
            return credibility_score, credibility_factors
        
        credibility_signals = {
            "numbers": any(char.isdigit() for char in response_lower),
            "statistics": any(word in response_lower for word in ["étude", "recherche", "statistique", "pourcentage", "%", "données"]),
            "testimonials": any(word in response_lower for word in ["avis", "témoignage", "utilisateur", "client", "retour"]),
            "certifications": any(word in response_lower for word in ["certifié", "certification", "norme", "iso", "agréé"]),
            "facts": any(word in response_lower for word in ["fondé en", "depuis", "année", "expérience", "historique"]),
            "sources": any(word in response_lower for word in ["selon", "d'après", "source", "rapport", "étude"])
        }
        
        for signal, present in credibility_signals.items():
            if present:
                credibility_score += 8
                credibility_factors.append(signal)
        
        return min(100, credibility_score), credibility_factors
    
    def _analyze_conversion(self, response_lower: str, brand_mentioned: bool, role: str) -> tuple:
        """Analyze conversion potential signals"""
        conversion_score = 0.0
        conversion_signals = []
        
        if not brand_mentioned:
            return conversion_score, conversion_signals
        
        conversion_indicators = {
            "cta": any(word in response_lower for word in ["essayer", "tester", "visiter", "contacter", "découvrir"]),
            "urgency": any(word in response_lower for word in ["maintenant", "aujourd'hui", "profiter", "offre"]),
            "benefit": any(word in response_lower for word in ["avantage", "bénéfice", "économie", "gain", "amélioration"]),
            "trust": any(word in response_lower for word in ["fiable", "confiance", "sécurisé", "garanti"]),
            "social_proof": any(word in response_lower for word in ["populaire", "utilisé par", "choisi par", "apprécié"])
        }
        
        for signal, present in conversion_indicators.items():
            if present:
                conversion_score += 20
                conversion_signals.append(signal)
        
        # Boost based on role
        if role == "top_recommendation":
            conversion_score += 30
        elif role == "shortlist":
            conversion_score += 15
        
        return min(100, conversion_score), conversion_signals
    
    def _check_hallucination(self, response_lower: str, brand_mentioned: bool) -> tuple:
        """Check for potential hallucination indicators"""
        hallucination_flags = []
        hallucination_penalty = 0
        
        if not brand_mentioned:
            return hallucination_flags, hallucination_penalty
        
        # Check for inconsistencies
        if "n'existe pas" in response_lower or "ne connais pas" in response_lower:
            hallucination_flags.append("existence_doubt")
            hallucination_penalty += 30
        
        if ("meilleur" in response_lower and "éviter" in response_lower):
            hallucination_flags.append("contradiction")
            hallucination_penalty += 20
        
        return hallucination_flags, hallucination_penalty
    
    def _analyze_competitors(
        self,
        response_lower: str,
        competitors: List[str],
        brand_position: int,
        response_length: int,
        brand_mentioned: bool
    ) -> Dict[str, Dict[str, Any]]:
        """Analyze competitor mentions in the response"""
        competitor_positions = {}
        
        for comp in competitors[:5]:  # Limit to top 5
            comp_lower = comp.lower()
            if comp_lower in response_lower:
                comp_pos = response_lower.find(comp_lower)
                comp_ratio = comp_pos / response_length if response_length > 0 else 1
                competitor_positions[comp] = {
                    "mentioned": True,
                    "position_ratio": round(comp_ratio, 3),
                    "before_brand": comp_pos < brand_position if brand_mentioned else True
                }
            else:
                competitor_positions[comp] = {
                    "mentioned": False,
                    "position_ratio": 1.0,
                    "before_brand": False
                }
        
        return competitor_positions


# Singleton instance
llm_connector = LLMConnector()
