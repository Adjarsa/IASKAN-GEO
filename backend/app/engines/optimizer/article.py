"""
Article Optimizer Engine
Analyzes articles and generates optimization recommendations for LLM visibility
"""
import re
import httpx
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


# Structure indicators for LLM-friendly content
STRUCTURE_PATTERNS = {
    "faq_pattern": [
        r'\b(FAQ|Questions? fréquentes?|Frequently asked)\b',
        r'<script[^>]*type=["\']application/ld\+json["\'][^>]*>.*?"@type":\s*"FAQPage"',
    ],
    "how_to_pattern": [
        r'\b(Comment|How to|Étape \d|Step \d)\b',
        r'<script[^>]*type=["\']application/ld\+json["\'][^>]*>.*?"@type":\s*"HowTo"',
    ],
    "list_pattern": [
        r'<(ul|ol)>.*?</(ul|ol)>',
        r'\b(Top \d+|Les \d+ meilleur|Best \d+)\b',
    ],
    "table_pattern": [
        r'<table[^>]*>.*?</table>',
        r'\b(Comparatif|Comparaison|Versus|vs\.?)\b',
    ],
    "definition_pattern": [
        r'\b(Définition|Definition|Qu\'est-ce que|What is)\b',
        r'<script[^>]*type=["\']application/ld\+json["\'][^>]*>.*?"@type":\s*"DefinedTerm"',
    ]
}

# Authority signals
AUTHORITY_SIGNALS = {
    "author_info": [
        r'<script[^>]*type=["\']application/ld\+json["\'][^>]*>.*?"author"',
        r'\b(Par|By|Écrit par|Written by)\s+[A-Z][a-z]+',
        r'class=["\'][^"\']*author[^"\']*["\']',
    ],
    "expert_signals": [
        r'\b(Expert|Spécialiste|Consultant|PhD|Dr\.)\b',
        r'\b(certifié|certified|accrédité|accredited)\b',
    ],
    "date_signals": [
        r'\b(Mis à jour|Updated|Publié|Published)\s*(le|on)?\s*\d',
        r'<meta[^>]*name=["\']date["\']',
        r'<time[^>]*datetime',
    ],
    "source_citations": [
        r'\b(Source|Selon|According to)\s*:?\s*',
        r'\[(\d+|citation)\]',
        r'<blockquote',
    ]
}

# Content quality indicators
QUALITY_INDICATORS = {
    "depth": {
        "min_words": 1500,
        "ideal_words": 2500,
        "max_words": 5000
    },
    "structure": {
        "min_headings": 5,
        "ideal_heading_ratio": 0.03,  # headings per word
    },
    "media": {
        "has_images": True,
        "has_videos": False,  # bonus
        "alt_texts": True
    }
}


class ArticleOptimizerEngine:
    """
    Engine for analyzing and optimizing articles for LLM visibility.
    """
    
    def __init__(self, llm_client=None):
        self.llm_client = llm_client
    
    async def analyze_article(
        self,
        url: str = None,
        content: str = None,
        brand_name: str = None
    ) -> Dict[str, Any]:
        """
        Analyze an article for GEO optimization.
        
        Args:
            url: Article URL to fetch and analyze
            content: Raw article content (if URL not provided)
            brand_name: Brand name for context
            
        Returns:
            Complete optimization analysis
        """
        # Fetch content if URL provided
        if url and not content:
            content, metadata = await self._fetch_article(url)
        else:
            metadata = {}
        
        if not content:
            return {
                "success": False,
                "error": "Impossible de récupérer le contenu de l'article"
            }
        
        # Parse content
        parsed = self._parse_content(content)
        
        # Run all analyses
        structure_analysis = self._analyze_structure(parsed)
        authority_analysis = self._analyze_authority(parsed, content)
        citability_analysis = self._analyze_citability(parsed, content)
        freshness_analysis = self._analyze_freshness(parsed, metadata)
        semantic_analysis = self._analyze_semantic_coverage(parsed, brand_name)
        
        # Calculate scores
        scores = self._calculate_scores(
            structure_analysis,
            authority_analysis,
            citability_analysis,
            freshness_analysis,
            semantic_analysis
        )
        
        # Generate diagnostics
        diagnostics = self._generate_diagnostics(
            structure_analysis,
            authority_analysis,
            citability_analysis,
            freshness_analysis,
            semantic_analysis
        )
        
        # Generate action plan
        action_plan = self._generate_action_plan(diagnostics, scores)
        
        # Generate distribution strategy
        distribution_strategy = self._generate_distribution_strategy(parsed, scores)
        
        return {
            "success": True,
            "url": url,
            "title": parsed.get("title", ""),
            "scores": scores,
            "diagnostics": diagnostics,
            "action_plan": action_plan,
            "distribution_strategy": distribution_strategy,
            "quick_wins": self._identify_quick_wins(diagnostics),
            "missing_elements": self._identify_missing_elements(parsed),
            "keyword_opportunities": self._identify_keyword_opportunities(parsed, brand_name),
            "raw_analysis": {
                "structure": structure_analysis,
                "authority": authority_analysis,
                "citability": citability_analysis,
                "freshness": freshness_analysis,
                "semantic": semantic_analysis
            }
        }
    
    async def _fetch_article(self, url: str) -> tuple:
        """Fetch article content from URL"""
        try:
            async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
                response = await client.get(url, headers={
                    "User-Agent": "Mozilla/5.0 (compatible; IAskanBot/1.0)"
                })
                
                if response.status_code != 200:
                    return None, {}
                
                content = response.text
                metadata = {
                    "url": str(response.url),
                    "status": response.status_code,
                    "content_type": response.headers.get("content-type", ""),
                    "last_modified": response.headers.get("last-modified", "")
                }
                
                return content, metadata
                
        except Exception as e:
            logger.error(f"Error fetching article: {e}")
            return None, {}
    
    def _parse_content(self, html_content: str) -> Dict[str, Any]:
        """Parse HTML content and extract structured data"""
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Extract title
        title = ""
        title_tag = soup.find('title')
        if title_tag:
            title = title_tag.get_text(strip=True)
        h1_tag = soup.find('h1')
        if h1_tag:
            title = h1_tag.get_text(strip=True) or title
        
        # Extract meta description
        meta_desc = ""
        meta_tag = soup.find('meta', attrs={'name': 'description'})
        if meta_tag:
            meta_desc = meta_tag.get('content', '')
        
        # Extract headings
        headings = {
            'h1': [h.get_text(strip=True) for h in soup.find_all('h1')],
            'h2': [h.get_text(strip=True) for h in soup.find_all('h2')],
            'h3': [h.get_text(strip=True) for h in soup.find_all('h3')],
            'h4': [h.get_text(strip=True) for h in soup.find_all('h4')],
        }
        
        # Extract body text
        for script in soup(["script", "style", "nav", "footer", "header"]):
            script.decompose()
        
        body_text = soup.get_text(separator=' ', strip=True)
        word_count = len(body_text.split())
        
        # Extract images
        images = []
        for img in soup.find_all('img'):
            images.append({
                'src': img.get('src', ''),
                'alt': img.get('alt', ''),
                'has_alt': bool(img.get('alt', '').strip())
            })
        
        # Extract lists
        lists = {
            'ul': len(soup.find_all('ul')),
            'ol': len(soup.find_all('ol'))
        }
        
        # Extract tables
        tables = len(soup.find_all('table'))
        
        # Extract structured data (JSON-LD)
        json_ld = []
        for script in soup.find_all('script', type='application/ld+json'):
            try:
                import json
                data = json.loads(script.string)
                json_ld.append(data)
            except Exception:
                pass
        
        # Extract links
        internal_links = 0
        external_links = 0
        for a in soup.find_all('a', href=True):
            href = a['href']
            if href.startswith('http') and 'facebook.com' not in href:
                external_links += 1
            elif href.startswith('/') or href.startswith('#'):
                internal_links += 1
        
        return {
            "title": title,
            "meta_description": meta_desc,
            "headings": headings,
            "body_text": body_text,
            "word_count": word_count,
            "images": images,
            "lists": lists,
            "tables": tables,
            "json_ld": json_ld,
            "internal_links": internal_links,
            "external_links": external_links,
            "raw_html": html_content
        }
    
    def _analyze_structure(self, parsed: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze content structure"""
        headings = parsed.get("headings", {})
        word_count = parsed.get("word_count", 0)
        
        # Heading analysis
        total_headings = sum(len(h) for h in headings.values())
        has_h1 = len(headings.get('h1', [])) > 0
        h2_count = len(headings.get('h2', []))
        
        # Structure score components
        structure = {
            "has_h1": has_h1,
            "h2_count": h2_count,
            "total_headings": total_headings,
            "word_count": word_count,
            "heading_ratio": total_headings / max(word_count, 1),
            "has_lists": parsed.get("lists", {}).get("ul", 0) + parsed.get("lists", {}).get("ol", 0) > 0,
            "has_tables": parsed.get("tables", 0) > 0,
            "images_count": len(parsed.get("images", [])),
            "images_with_alt": sum(1 for img in parsed.get("images", []) if img.get("has_alt"))
        }
        
        # Check for LLM-friendly patterns
        raw_html = parsed.get("raw_html", "").lower()
        
        structure["has_faq"] = any(
            re.search(p, raw_html, re.IGNORECASE | re.DOTALL) 
            for p in STRUCTURE_PATTERNS["faq_pattern"]
        )
        structure["has_how_to"] = any(
            re.search(p, raw_html, re.IGNORECASE | re.DOTALL) 
            for p in STRUCTURE_PATTERNS["how_to_pattern"]
        )
        structure["has_definition"] = any(
            re.search(p, raw_html, re.IGNORECASE | re.DOTALL) 
            for p in STRUCTURE_PATTERNS["definition_pattern"]
        )
        
        return structure
    
    def _analyze_authority(self, parsed: Dict[str, Any], raw_html: str) -> Dict[str, Any]:
        """Analyze authority signals"""
        authority = {
            "has_author": False,
            "has_expert_signals": False,
            "has_date": False,
            "has_citations": False,
            "external_links": parsed.get("external_links", 0),
            "has_schema_org": len(parsed.get("json_ld", [])) > 0
        }
        
        html_lower = raw_html.lower()
        
        # Check authority signals
        for signal in AUTHORITY_SIGNALS["author_info"]:
            if re.search(signal, html_lower, re.IGNORECASE | re.DOTALL):
                authority["has_author"] = True
                break
        
        for signal in AUTHORITY_SIGNALS["expert_signals"]:
            if re.search(signal, html_lower, re.IGNORECASE):
                authority["has_expert_signals"] = True
                break
        
        for signal in AUTHORITY_SIGNALS["date_signals"]:
            if re.search(signal, html_lower, re.IGNORECASE | re.DOTALL):
                authority["has_date"] = True
                break
        
        for signal in AUTHORITY_SIGNALS["source_citations"]:
            if re.search(signal, html_lower, re.IGNORECASE):
                authority["has_citations"] = True
                break
        
        # Check Schema.org types
        authority["schema_types"] = []
        for ld in parsed.get("json_ld", []):
            if isinstance(ld, dict) and "@type" in ld:
                authority["schema_types"].append(ld["@type"])
        
        return authority
    
    def _analyze_citability(self, parsed: Dict[str, Any], raw_html: str) -> Dict[str, Any]:
        """Analyze how citable/quotable the content is"""
        body_text = parsed.get("body_text", "")
        
        # Find quotable sentences (short, factual statements)
        sentences = re.split(r'[.!?]+', body_text)
        quotable_sentences = [
            s.strip() for s in sentences 
            if 20 < len(s.strip()) < 150 and not s.strip().startswith(('Je', 'Nous', 'I ', 'We '))
        ]
        
        # Check for statistics/numbers
        has_statistics = bool(re.search(r'\d+[%€$]|\d+\s*(?:millions?|milliards?|users?|utilisateurs?)', body_text, re.IGNORECASE))
        
        # Check for clear definitions
        has_clear_definitions = bool(re.search(r'(?:est|are|is)\s+(?:un|une|a|an)\s+', body_text, re.IGNORECASE))
        
        return {
            "quotable_sentences_count": len(quotable_sentences),
            "sample_quotable": quotable_sentences[:5],
            "has_statistics": has_statistics,
            "has_clear_definitions": has_clear_definitions,
            "avg_sentence_length": sum(len(s.split()) for s in sentences) / max(len(sentences), 1)
        }
    
    def _analyze_freshness(self, parsed: Dict[str, Any], metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze content freshness"""
        freshness = {
            "last_modified": metadata.get("last_modified", ""),
            "year_mentions": [],
            "has_current_year": False,
            "appears_outdated": False
        }
        
        body_text = parsed.get("body_text", "")
        current_year = datetime.now().year
        
        # Find year mentions
        years = re.findall(r'\b(20\d{2})\b', body_text)
        freshness["year_mentions"] = list(set(years))
        freshness["has_current_year"] = str(current_year) in years or str(current_year - 1) in years
        
        # Check for outdated signals
        outdated_signals = [
            r'\b(obsolète|deprecated|ancien|old)\b',
            r'\b(201[0-8])\b'  # Years before 2019
        ]
        for signal in outdated_signals:
            if re.search(signal, body_text, re.IGNORECASE):
                freshness["appears_outdated"] = True
                break
        
        return freshness
    
    def _analyze_semantic_coverage(self, parsed: Dict[str, Any], brand_name: str = None) -> Dict[str, Any]:
        """Analyze semantic topic coverage"""
        body_text = parsed.get("body_text", "").lower()
        
        # Topic coverage
        topics_covered = []
        topic_keywords = {
            "features": ["fonctionnalité", "feature", "outil", "option"],
            "pricing": ["prix", "tarif", "coût", "gratuit"],
            "comparison": ["comparaison", "versus", "alternative", "concurrent"],
            "tutorial": ["comment", "étape", "tutoriel", "guide"],
            "review": ["avis", "test", "review", "évaluation"],
            "use_case": ["exemple", "cas d'usage", "use case", "scénario"]
        }
        
        for topic, keywords in topic_keywords.items():
            if any(kw in body_text for kw in keywords):
                topics_covered.append(topic)
        
        # Brand mention analysis
        brand_analysis = {}
        if brand_name:
            brand_lower = brand_name.lower()
            brand_analysis = {
                "mentioned": brand_lower in body_text,
                "mention_count": body_text.count(brand_lower),
                "in_title": brand_lower in parsed.get("title", "").lower(),
                "in_headings": any(
                    brand_lower in h.lower() 
                    for hs in parsed.get("headings", {}).values() 
                    for h in hs
                )
            }
        
        return {
            "topics_covered": topics_covered,
            "topic_count": len(topics_covered),
            "brand_analysis": brand_analysis
        }
    
    def _calculate_scores(
        self,
        structure: Dict,
        authority: Dict,
        citability: Dict,
        freshness: Dict,
        semantic: Dict
    ) -> Dict[str, float]:
        """Calculate optimization scores"""
        # Structure score (0-100)
        structure_score = 0
        if structure.get("has_h1"):
            structure_score += 15
        structure_score += min(25, structure.get("h2_count", 0) * 5)
        if structure.get("has_lists"):
            structure_score += 15
        if structure.get("has_tables"):
            structure_score += 10
        if structure.get("has_faq"):
            structure_score += 20
        if structure.get("images_count", 0) > 0:
            structure_score += 10
        if structure.get("word_count", 0) >= 1500:
            structure_score += 5
        
        # Authority score (0-100)
        authority_score = 0
        if authority.get("has_author"):
            authority_score += 25
        if authority.get("has_expert_signals"):
            authority_score += 20
        if authority.get("has_date"):
            authority_score += 15
        if authority.get("has_citations"):
            authority_score += 20
        if authority.get("has_schema_org"):
            authority_score += 20
        
        # Citability score (0-100)
        citability_score = 0
        quotable = citability.get("quotable_sentences_count", 0)
        citability_score += min(40, quotable * 4)
        if citability.get("has_statistics"):
            citability_score += 25
        if citability.get("has_clear_definitions"):
            citability_score += 20
        avg_len = citability.get("avg_sentence_length", 0)
        if 10 < avg_len < 25:
            citability_score += 15
        
        # Freshness score (0-100)
        freshness_score = 50  # Base
        if freshness.get("has_current_year"):
            freshness_score += 30
        if freshness.get("appears_outdated"):
            freshness_score -= 30
        if freshness.get("last_modified"):
            freshness_score += 20
        
        # Overall score
        overall = (
            structure_score * 0.30 +
            authority_score * 0.25 +
            citability_score * 0.25 +
            freshness_score * 0.20
        )
        
        return {
            "overall": round(min(100, overall), 1),
            "structure": round(min(100, structure_score), 1),
            "authority": round(min(100, authority_score), 1),
            "citability": round(min(100, citability_score), 1),
            "freshness": round(min(100, freshness_score), 1)
        }
    
    def _generate_diagnostics(
        self,
        structure: Dict,
        authority: Dict,
        citability: Dict,
        freshness: Dict,
        semantic: Dict
    ) -> List[Dict[str, Any]]:
        """Generate detailed diagnostics"""
        diagnostics = []
        
        # Structure diagnostics
        if not structure.get("has_h1"):
            diagnostics.append({
                "category": "structure",
                "severity": "critical",
                "issue": "Pas de balise H1",
                "recommendation": "Ajouter un titre H1 clair et optimisé avec le mot-clé principal"
            })
        
        if structure.get("h2_count", 0) < 3:
            diagnostics.append({
                "category": "structure",
                "severity": "high",
                "issue": f"Seulement {structure.get('h2_count', 0)} sous-titres H2",
                "recommendation": "Structurer le contenu avec au moins 5 sous-titres H2"
            })
        
        if not structure.get("has_faq"):
            diagnostics.append({
                "category": "structure",
                "severity": "high",
                "issue": "Pas de section FAQ",
                "recommendation": "Ajouter une FAQ structurée avec Schema.org FAQPage"
            })
        
        if not structure.get("has_lists"):
            diagnostics.append({
                "category": "structure",
                "severity": "medium",
                "issue": "Pas de listes à puces",
                "recommendation": "Utiliser des listes pour les énumérations (facilite la citation par les LLMs)"
            })
        
        # Authority diagnostics
        if not authority.get("has_author"):
            diagnostics.append({
                "category": "authority",
                "severity": "high",
                "issue": "Pas d'information sur l'auteur",
                "recommendation": "Ajouter une bio auteur avec expertise et crédibilité (E-E-A-T)"
            })
        
        if not authority.get("has_schema_org"):
            diagnostics.append({
                "category": "authority",
                "severity": "critical",
                "issue": "Pas de données structurées Schema.org",
                "recommendation": "Implémenter Schema.org (Article, FAQPage, HowTo selon le contenu)"
            })
        
        if not authority.get("has_citations"):
            diagnostics.append({
                "category": "authority",
                "severity": "medium",
                "issue": "Pas de sources citées",
                "recommendation": "Ajouter des citations vers des sources autoritaires"
            })
        
        # Citability diagnostics
        if citability.get("quotable_sentences_count", 0) < 5:
            diagnostics.append({
                "category": "citability",
                "severity": "high",
                "issue": "Peu de phrases facilement citables",
                "recommendation": "Rédiger des phrases courtes et factuelles qui peuvent être extraites"
            })
        
        if not citability.get("has_statistics"):
            diagnostics.append({
                "category": "citability",
                "severity": "medium",
                "issue": "Pas de statistiques ou chiffres",
                "recommendation": "Ajouter des données chiffrées et statistiques sourcées"
            })
        
        # Freshness diagnostics
        if freshness.get("appears_outdated"):
            diagnostics.append({
                "category": "freshness",
                "severity": "critical",
                "issue": "Le contenu semble obsolète",
                "recommendation": "Mettre à jour le contenu avec des informations actuelles et ajouter une date de mise à jour"
            })
        
        if not freshness.get("has_current_year"):
            diagnostics.append({
                "category": "freshness",
                "severity": "medium",
                "issue": "Pas de mention de l'année en cours",
                "recommendation": "Inclure des références temporelles actuelles (2026, cette année, etc.)"
            })
        
        return diagnostics
    
    def _generate_action_plan(
        self,
        diagnostics: List[Dict],
        scores: Dict
    ) -> Dict[str, Any]:
        """Generate prioritized action plan"""
        plan = {
            "immediate": [],  # Critical issues
            "short_term": [],  # High priority
            "medium_term": [],  # Medium priority
            "long_term": []  # Nice to have
        }
        
        for diag in diagnostics:
            action = {
                "category": diag["category"],
                "action": diag["recommendation"],
                "issue": diag["issue"]
            }
            
            if diag["severity"] == "critical":
                plan["immediate"].append(action)
            elif diag["severity"] == "high":
                plan["short_term"].append(action)
            elif diag["severity"] == "medium":
                plan["medium_term"].append(action)
            else:
                plan["long_term"].append(action)
        
        return plan
    
    def _generate_distribution_strategy(
        self,
        parsed: Dict,
        scores: Dict
    ) -> List[Dict[str, Any]]:
        """Generate content distribution recommendations"""
        strategy = []
        
        # Based on content type and scores
        if scores.get("overall", 0) >= 70:
            strategy.append({
                "channel": "Réseaux sociaux",
                "priority": "high",
                "action": "Partager sur LinkedIn, Twitter avec extraits clés",
                "timing": "Immédiat"
            })
        
        strategy.append({
            "channel": "Annuaires et agrégateurs",
            "priority": "medium",
            "action": "Soumettre aux plateformes type G2, Capterra si pertinent",
            "timing": "Court terme"
        })
        
        strategy.append({
            "channel": "Relations presse",
            "priority": "medium",
            "action": "Pitcher aux médias spécialisés du secteur",
            "timing": "Moyen terme"
        })
        
        if parsed.get("word_count", 0) >= 2000:
            strategy.append({
                "channel": "Content syndication",
                "priority": "low",
                "action": "Republier sur Medium, Dev.to ou plateformes sectorielles",
                "timing": "Long terme"
            })
        
        return strategy
    
    def _identify_quick_wins(self, diagnostics: List[Dict]) -> List[Dict[str, Any]]:
        """Identify quick wins from diagnostics"""
        quick_wins = []
        
        quick_patterns = [
            ("date", "Ajouter une date de mise à jour visible"),
            ("h1", "Optimiser le titre H1"),
            ("liste", "Transformer les paragraphes longs en listes"),
            ("schema", "Ajouter le balisage Schema.org de base")
        ]
        
        for keyword, action in quick_patterns:
            for diag in diagnostics:
                if keyword.lower() in diag.get("issue", "").lower() or keyword.lower() in diag.get("recommendation", "").lower():
                    quick_wins.append({
                        "action": action,
                        "effort": "low",
                        "impact": "high" if diag["severity"] in ["critical", "high"] else "medium"
                    })
                    break
        
        return quick_wins[:5]
    
    def _identify_missing_elements(self, parsed: Dict) -> List[str]:
        """Identify missing content elements"""
        missing = []
        
        if not parsed.get("json_ld"):
            missing.append("Données structurées Schema.org")
        if len(parsed.get("headings", {}).get("h2", [])) < 5:
            missing.append("Structure de titres complète (H2)")
        if not parsed.get("images"):
            missing.append("Images illustratives")
        if parsed.get("lists", {}).get("ul", 0) + parsed.get("lists", {}).get("ol", 0) == 0:
            missing.append("Listes à puces/numérotées")
        if not parsed.get("tables"):
            missing.append("Tableaux comparatifs")
        if parsed.get("external_links", 0) < 3:
            missing.append("Liens vers sources externes autoritaires")
        
        return missing
    
    def _identify_keyword_opportunities(self, parsed: Dict, brand_name: str = None) -> List[str]:
        """Identify keyword optimization opportunities"""
        opportunities = []
        
        title = parsed.get("title", "").lower()
        headings = parsed.get("headings", {})
        
        # Generic opportunities
        if "meilleur" not in title and "best" not in title:
            opportunities.append("Ajouter 'meilleur' ou 'top' dans le titre pour les requêtes comparatives")
        
        if "2026" not in title and "2025" not in title:
            opportunities.append("Inclure l'année dans le titre pour la fraîcheur")
        
        if "guide" not in title and "comment" not in title:
            opportunities.append("Utiliser des termes comme 'guide complet' ou 'comment faire'")
        
        # Brand-specific
        if brand_name:
            brand_lower = brand_name.lower()
            all_headings = [h.lower() for hs in headings.values() for h in hs]
            
            if brand_lower not in title:
                opportunities.append(f"Mentionner {brand_name} dans le titre")
            
            if not any(brand_lower in h for h in all_headings):
                opportunities.append(f"Créer un sous-titre H2 mentionnant {brand_name}")
        
        return opportunities[:5]
    
    def simulate_impact(
        self, 
        current_analysis: Dict[str, Any], 
        improvements: List[str]
    ) -> Dict[str, Any]:
        """
        Simulate the impact of implementing specific improvements.
        
        Args:
            current_analysis: The current optimization analysis
            improvements: List of improvement IDs to simulate
            
        Returns:
            Simulated score changes and projected results
        """
        current_score = current_analysis.get("overall_score", 50)
        current_scores = current_analysis.get("scores", {})
        
        # Impact values for each improvement type
        IMPACT_MAP = {
            # Content improvements
            "add_faq": {"content": 8, "structure": 5, "overall": 6},
            "improve_structure": {"structure": 10, "content": 3, "overall": 5},
            "add_definitions": {"content": 5, "authority": 3, "overall": 4},
            "expand_content": {"content": 12, "thoroughness": 15, "overall": 8},
            "add_introduction": {"content": 5, "relevance": 8, "overall": 5},
            
            # Authority improvements
            "add_author": {"authority": 12, "trust": 8, "overall": 7},
            "add_sources": {"authority": 10, "trust": 10, "overall": 8},
            "add_credentials": {"authority": 8, "trust": 5, "overall": 5},
            "update_date": {"freshness": 15, "authority": 5, "overall": 6},
            "add_expert_review": {"authority": 10, "trust": 8, "overall": 7},
            
            # Technical improvements
            "add_schema": {"technical": 12, "visibility": 8, "overall": 7},
            "improve_meta": {"technical": 5, "seo": 8, "overall": 5},
            "add_structured_data": {"technical": 10, "visibility": 10, "overall": 8},
            "optimize_headings": {"structure": 8, "seo": 5, "overall": 5},
            
            # Engagement improvements
            "add_media": {"engagement": 10, "content": 5, "overall": 6},
            "add_internal_links": {"engagement": 5, "seo": 5, "overall": 4},
            "add_cta": {"engagement": 8, "overall": 3},
        }
        
        # Calculate projected improvements
        total_impact = {"overall": 0}
        component_impacts = {}
        
        for improvement in improvements:
            impact = IMPACT_MAP.get(improvement, {"overall": 3})
            
            for component, value in impact.items():
                if component not in total_impact:
                    total_impact[component] = 0
                total_impact[component] += value
                
                if component != "overall":
                    if component not in component_impacts:
                        component_impacts[component] = 0
                    component_impacts[component] += value
        
        # Cap improvements (diminishing returns)
        for key in total_impact:
            total_impact[key] = min(total_impact[key], 35)  # Max 35 point improvement
        
        # Calculate projected scores
        projected_score = min(100, current_score + total_impact.get("overall", 0))
        projected_scores = {}
        
        for component, current in current_scores.items():
            improvement = component_impacts.get(component, 0)
            projected_scores[component] = min(100, current + improvement)
        
        # Determine new grade
        if projected_score >= 80:
            projected_grade = "A"
        elif projected_score >= 60:
            projected_grade = "B"
        elif projected_score >= 40:
            projected_grade = "C"
        else:
            projected_grade = "D"
        
        return {
            "simulation": {
                "current_score": current_score,
                "projected_score": projected_score,
                "score_improvement": projected_score - current_score,
                "projected_grade": projected_grade,
                "improvements_applied": improvements,
                "component_impacts": component_impacts,
                "current_scores": current_scores,
                "projected_scores": projected_scores
            },
            "recommendations": self._generate_implementation_order(improvements),
            "estimated_effort": self._estimate_total_effort(improvements),
            "confidence": self._calculate_confidence(len(improvements), current_score)
        }
    
    def _generate_implementation_order(self, improvements: List[str]) -> List[Dict]:
        """Generate recommended order for implementing improvements"""
        # Priority order (higher value = implement first)
        PRIORITY = {
            "add_schema": 10,
            "add_faq": 9,
            "add_author": 9,
            "improve_structure": 8,
            "add_sources": 8,
            "add_definitions": 7,
            "update_date": 7,
            "improve_meta": 6,
            "expand_content": 6,
            "add_media": 5,
            "add_internal_links": 4,
            "add_cta": 3,
        }
        
        ordered = sorted(
            improvements, 
            key=lambda x: PRIORITY.get(x, 5), 
            reverse=True
        )
        
        return [
            {
                "improvement": imp,
                "priority": i + 1,
                "impact": "high" if PRIORITY.get(imp, 5) >= 8 else "medium" if PRIORITY.get(imp, 5) >= 5 else "low"
            }
            for i, imp in enumerate(ordered)
        ]
    
    def _estimate_total_effort(self, improvements: List[str]) -> Dict:
        """Estimate total effort for all improvements"""
        EFFORT_MAP = {
            "add_faq": {"hours": 2, "difficulty": "easy"},
            "improve_structure": {"hours": 1, "difficulty": "easy"},
            "add_definitions": {"hours": 1, "difficulty": "easy"},
            "expand_content": {"hours": 4, "difficulty": "medium"},
            "add_introduction": {"hours": 0.5, "difficulty": "easy"},
            "add_author": {"hours": 1, "difficulty": "easy"},
            "add_sources": {"hours": 3, "difficulty": "medium"},
            "add_credentials": {"hours": 0.5, "difficulty": "easy"},
            "update_date": {"hours": 0.5, "difficulty": "easy"},
            "add_schema": {"hours": 2, "difficulty": "medium"},
            "improve_meta": {"hours": 1, "difficulty": "easy"},
            "add_media": {"hours": 3, "difficulty": "medium"},
            "add_internal_links": {"hours": 1, "difficulty": "easy"},
        }
        
        total_hours = sum(
            EFFORT_MAP.get(imp, {"hours": 2}).get("hours", 2) 
            for imp in improvements
        )
        
        difficulties = [
            EFFORT_MAP.get(imp, {"difficulty": "medium"}).get("difficulty")
            for imp in improvements
        ]
        
        if "hard" in difficulties:
            overall_difficulty = "hard"
        elif difficulties.count("medium") > len(difficulties) / 2:
            overall_difficulty = "medium"
        else:
            overall_difficulty = "easy"
        
        return {
            "total_hours": total_hours,
            "overall_difficulty": overall_difficulty,
            "estimated_timeline": f"{int(total_hours / 4)} - {int(total_hours / 2 + 1)} jours"
        }
    
    def _calculate_confidence(self, num_improvements: int, current_score: int) -> Dict:
        """Calculate confidence level of the simulation"""
        # More improvements = lower confidence due to interaction effects
        base_confidence = 95
        
        if num_improvements > 5:
            confidence = base_confidence - (num_improvements - 5) * 5
        else:
            confidence = base_confidence
        
        # Lower current scores have higher variance
        if current_score < 30:
            confidence -= 10
        elif current_score < 50:
            confidence -= 5
        
        confidence = max(60, min(95, confidence))
        
        return {
            "percentage": confidence,
            "level": "high" if confidence >= 85 else "medium" if confidence >= 70 else "low",
            "note": "Les résultats réels peuvent varier selon la qualité de l'implémentation"
        }


# Singleton instance
optimizer_engine = ArticleOptimizerEngine()
