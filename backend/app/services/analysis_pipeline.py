"""
Analysis Pipeline Service
Main orchestrator for GEO analysis using modular services

This service implements the IAskan Verified GEO Protocol™ v2.1
and coordinates:
- Query Generation (from engines/query/)
- LLM Querying (from services/llm_connector.py)
- GEO Scoring (from services/geo_scoring.py)
- Competitive Intelligence (from services/competitive_intelligence.py)
- Semantic Analysis (from engines/semantic/)
- Content Gap Analysis (from engines/gap/)
"""
import asyncio
import logging
import re
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional
from urllib.parse import urlparse

import httpx
from bs4 import BeautifulSoup

from ..services.llm_connector import LLMConnector, llm_connector
from ..services.geo_scoring import GEOScoringEngine, geo_scoring_engine
from ..services.competitive_intelligence import CompetitiveIntelligenceEngine, competitive_intelligence_engine
from ..engines.query.generator import QueryGenerationEngine, query_engine
from ..engines.query.variation import PromptVariationEngine, variation_engine
from ..engines.semantic.analyzer import SemanticAnalysisEngine, semantic_engine
from ..engines.gap.finder import ContentGapEngine, gap_engine
from ..core.config import EMERGENT_LLM_KEY, SUBSCRIPTION_PLANS

logger = logging.getLogger(__name__)

# Query Type Distribution for multi-dimension analysis
QUERY_TYPE_DISTRIBUTION = {
    "transactional": 0.30,      # 30% - Purchase intent
    "comparative": 0.25,        # 25% - Brand comparison
    "informational": 0.20,      # 20% - General information
    "local": 0.10,              # 10% - Geographic searches
    "recommendation": 0.10,     # 10% - Best of / recommendations
    "review": 0.05              # 5% - Reviews and opinions
}


class AnalysisPipelineService:
    """
    Main analysis pipeline service implementing IAskan Verified GEO Protocol™
    """
    
    def __init__(self):
        self.llm_connector = llm_connector
        self.geo_scoring = geo_scoring_engine
        self.competitive_intel = competitive_intelligence_engine
        self.query_generator = query_engine
        self.variation_engine = variation_engine
        self.semantic_analyzer = semantic_engine
        self.gap_finder = gap_engine
    
    async def run_full_analysis(
        self,
        analysis_id: str,
        project: Dict[str, Any],
        plan_config: Dict[str, Any],
        update_callback: Optional[callable] = None
    ) -> Dict[str, Any]:
        """
        Execute the complete GEO analysis pipeline.
        
        Args:
            analysis_id: Unique analysis identifier
            project: Project data including brand_name, keywords, competitors, etc.
            plan_config: Subscription plan configuration
            update_callback: Optional async callback for progress updates
            
        Returns:
            Complete analysis results
        """
        try:
            # Extract configuration
            ai_engines = plan_config.get("ai_engines", ["chatgpt"])
            num_prompts = plan_config.get("num_prompts", 10)
            runs_per_query = plan_config.get("runs_per_query", 3)
            total_api_calls = num_prompts * runs_per_query * len(ai_engines)
            
            brand_name = project.get("brand_name", "")
            keywords = project.get("keywords", [])
            competitors = project.get("competitors", [])
            website_url = project.get("website_url", "")
            products = project.get("products", [])
            
            if not brand_name:
                raise ValueError("Nom de marque requis")
            
            # ===== PRE-PHASE: Generate Brand Variants =====
            await self._update_phase(update_callback, analysis_id, "initializing")
            brand_variants = self._generate_brand_variants(brand_name, products)
            
            # ===== PRE-PHASE: Site Enrichment Analysis =====
            site_enrichment = {}
            if website_url:
                await self._update_phase(update_callback, analysis_id, "site_analysis")
                site_enrichment = await self._analyze_site_enrichment(website_url)
            
            # ===== PHASE 1: Generate Multi-Dimension Queries =====
            await self._update_phase(update_callback, analysis_id, "query_generation")
            queries = self._generate_queries_multi_dimension(brand_name, keywords, competitors, num_prompts)
            
            logger.info(f"Generated {len(queries)} queries for analysis")
            
            # ===== PHASE 2: Multi-Run AI Querying =====
            await self._update_phase(update_callback, analysis_id, "ai_querying", {
                "total_queries": len(queries),
                "total_api_calls": total_api_calls
            })
            
            all_responses = []
            ai_scores = {ai: [] for ai in ai_engines}
            query_results = []
            brand_mention_details = []
            
            for query_idx, query in enumerate(queries):
                query_text = query["text"]
                query_type = query["type"]
                query_all_responses = []
                
                for ai in ai_engines:
                    ai_run_responses = []
                    
                    # Execute multi-runs for stability
                    for run_id in range(1, runs_per_query + 1):
                        response = await self.llm_connector.query_llm(
                            query_text=query_text,
                            ai_type=ai,
                            run_id=run_id,
                            brand_name=brand_name,
                            competitors=competitors
                        )
                        
                        # Enhanced brand variant detection
                        response_text = response.get("full_response", "") or response.get("response_excerpt", "")
                        advanced_mentions = self._detect_brand_mentions_advanced(response_text, brand_name, brand_variants)
                        response["advanced_mentions"] = advanced_mentions
                        response["query_type"] = query_type
                        
                        # Track detailed mentions
                        if advanced_mentions.get("total_mentions", 0) > 0:
                            brand_mention_details.append({
                                "query_type": query_type,
                                "ai_type": ai,
                                "run_id": run_id,
                                "mention_quality": advanced_mentions.get("mention_quality"),
                                "variants_found": advanced_mentions.get("variants_found", []),
                                "total_mentions": advanced_mentions.get("total_mentions", 0)
                            })
                        
                        ai_run_responses.append(response)
                        all_responses.append(response)
                        
                        if response.get("role") != "error":
                            score = response.get("role_score", 0) * 100
                            ai_scores[ai].append(score)
                    
                    query_all_responses.extend(ai_run_responses)
                
                # Aggregate query results
                mention_count = sum(
                    1 for r in query_all_responses 
                    if r.get("brand_mentioned", False) or r.get("advanced_mentions", {}).get("total_mentions", 0) > 0
                )
                
                query_result = {
                    "query_text": query_text,
                    "query_type": query_type,
                    "keyword": query.get("keyword", ""),
                    "runs_per_ai": runs_per_query,
                    "avg_score": round(sum(r.get("role_score", 0) for r in query_all_responses) / len(query_all_responses) * 100, 1) if query_all_responses else 0,
                    "mention_rate": round((mention_count / len(query_all_responses) * 100), 1) if query_all_responses else 0,
                    "stability": {
                        "roles": list(set(r.get("role", "absent") for r in query_all_responses)),
                        "consistent": len(set(r.get("role", "absent") for r in query_all_responses)) <= 2
                    }
                }
                query_results.append(query_result)
                
                # Update progress
                if update_callback:
                    await update_callback(analysis_id, {"queries_processed": query_idx + 1})
            
            # ===== PHASE 3: Calculate Stability Index =====
            await self._update_phase(update_callback, analysis_id, "calculating_indices")
            stability_data = self.geo_scoring.calculate_stability_index(all_responses)
            
            # ===== PHASE 4: Calculate Advanced Indices =====
            indices = self.geo_scoring.calculate_advanced_indices(all_responses, brand_name, competitors)
            indices["stability_index"] = stability_data.get("stability_score", 0)
            
            # ===== PHASE 5: Calculate R.A.T.E. Score =====
            rate_score = self.geo_scoring.calculate_rate_score(all_responses, stability_data)
            
            # ===== PHASE 6: Calculate Per-AI Scores =====
            final_ai_scores = {}
            for ai, scores in ai_scores.items():
                final_ai_scores[ai] = round(sum(scores) / len(scores), 1) if scores else 0
            
            # ===== PHASE 7: Generate Recommendations =====
            recommendations = self.geo_scoring.generate_recommendations(
                rate_score, final_ai_scores, indices, stability_data
            )
            
            # ===== PHASE 8: Query Type Analysis =====
            query_type_breakdown = self._analyze_query_types(query_results)
            
            # ===== PHASE 9: Competitive Intelligence =====
            await self._update_phase(update_callback, analysis_id, "competitive_analysis")
            discovered_competitors = self.competitive_intel.identify_competitors(
                all_responses, brand_name, competitors
            )
            
            competitive_gap = self.competitive_intel.calculate_competitive_gap(
                all_responses, brand_name, competitors
            )
            
            # Build competitor comparison
            competitor_comparison = self._build_competitor_comparison(
                discovered_competitors, competitors
            )
            
            # ===== PHASE 10: Semantic Analysis =====
            semantic_results = self.semantic_analyzer.analyze_batch(all_responses, brand_name)
            
            # ===== PHASE 11: Content Gap Analysis =====
            content_gaps = self.gap_finder.analyze_gaps(queries, all_responses, brand_name, competitors)
            
            # ===== PHASE 12: Brand Analysis Summary =====
            brand_analysis = self._summarize_brand_mentions(brand_variants, brand_mention_details)
            
            # ===== PHASE 13: Add Site Enrichment Recommendations =====
            if site_enrichment and site_enrichment.get("recommendations"):
                for enrichment_rec in site_enrichment.get("recommendations", [])[:3]:
                    recommendations.append({
                        "priority": enrichment_rec.get("priority", "medium"),
                        "category": "site_enrichment",
                        "title": enrichment_rec.get("action", ""),
                        "description": enrichment_rec.get("impact", ""),
                        "impact": enrichment_rec.get("priority", "moyen"),
                        "effort": "faible",
                        "metrics_impacted": ["citability", "authority"]
                    })
            
            # ===== FINALIZE: Build Complete Results =====
            analysis_summary = {
                "total_prompts": num_prompts,
                "runs_per_query": runs_per_query,
                "total_api_calls": total_api_calls,
                "total_responses": len(all_responses),
                "ai_engines_used": ai_engines,
                "competitors_analyzed": list(set(competitors[:5] + [c["name"] for c in discovered_competitors[:10]])),
                "discovered_competitors": discovered_competitors[:10],
                "user_defined_competitors": competitors[:5],
                "protocol_version": "IAskan Verified GEO Protocol™ v2.1",
                "methodology": {
                    "formula": f"{num_prompts} prompts × {runs_per_query} runs × {len(ai_engines)} IA = {total_api_calls} requêtes",
                    "multi_runs": True,
                    "runs_per_prompt": runs_per_query,
                    "multi_ai": len(ai_engines) > 1,
                    "query_distribution": QUERY_TYPE_DISTRIBUTION,
                    "analysis_layers": ["presence", "role", "credibility", "conversion"],
                    "anti_hallucination": True,
                    "brand_variants_detection": True,
                    "site_enrichment_analysis": bool(site_enrichment)
                }
            }
            
            await self._update_phase(update_callback, analysis_id, "completed")
            
            return {
                "analysis_id": analysis_id,
                "status": "completed",
                "global_score": rate_score["total"],
                "grade": rate_score.get("grade", "N/A"),
                "rate_score": rate_score,
                "ai_scores": final_ai_scores,
                "query_scores": query_results,
                "recommendations": recommendations,
                "competitor_comparison": competitor_comparison,
                "indices": indices,
                "stability_data": stability_data,
                "query_type_breakdown": query_type_breakdown,
                "analysis_summary": analysis_summary,
                "site_enrichment": site_enrichment,
                "brand_analysis": brand_analysis,
                "semantic_analysis": semantic_results,
                "content_gaps": content_gaps,
                "competitive_gap": competitive_gap,
                "completed_at": datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            logger.error(f"Analysis pipeline error: {e}")
            raise
    
    async def _update_phase(
        self,
        callback: Optional[callable],
        analysis_id: str,
        phase: str,
        extra_data: Dict = None
    ):
        """Update analysis phase via callback"""
        if callback:
            data = {"current_phase": phase}
            if extra_data:
                data.update(extra_data)
            await callback(analysis_id, data)
    
    def _generate_brand_variants(self, brand_name: str, products: List[str] = None) -> List[str]:
        """Generate brand name variants for detection"""
        products = products or []
        variants = [brand_name]
        brand_lower = brand_name.lower()
        
        # Case variations
        variants.extend([brand_lower, brand_name.upper(), brand_name.title()])
        
        # Common typos
        if len(brand_name) > 3:
            # Double letter typos
            for i in range(len(brand_name) - 1):
                if brand_name[i] == brand_name[i + 1]:
                    variants.append(brand_name[:i] + brand_name[i + 1:])
            
            # Missing letter
            for i in range(len(brand_name)):
                variants.append(brand_name[:i] + brand_name[i + 1:])
        
        # Without spaces/hyphens
        if " " in brand_name or "-" in brand_name:
            variants.append(brand_name.replace(" ", "").replace("-", ""))
            variants.append(brand_name.replace("-", " "))
            variants.append(brand_name.replace(" ", "-"))
        
        # Abbreviations (first letters)
        words = brand_name.split()
        if len(words) > 1:
            abbrev = "".join(w[0].upper() for w in words)
            variants.append(abbrev)
        
        # Add products as variants
        variants.extend(products[:5])
        
        return list(set(v for v in variants if v and len(v) >= 2))
    
    def _detect_brand_mentions_advanced(
        self,
        response_text: str,
        brand_name: str,
        brand_variants: List[str]
    ) -> Dict[str, Any]:
        """Detect brand mentions using variants"""
        if not response_text:
            return {"total_mentions": 0, "variants_found": [], "mention_quality": "absent"}
        
        response_lower = response_text.lower()
        mentions = 0
        variants_found = []
        
        for variant in brand_variants:
            variant_lower = variant.lower()
            count = response_lower.count(variant_lower)
            if count > 0:
                mentions += count
                variants_found.append(variant)
        
        # Determine mention quality
        if mentions == 0:
            quality = "absent"
        elif brand_name.lower() in response_lower:
            quality = "exact"
        elif variants_found:
            quality = "variant"
        else:
            quality = "partial"
        
        return {
            "total_mentions": mentions,
            "variants_found": variants_found[:5],
            "mention_quality": quality
        }
    
    def _generate_queries_multi_dimension(
        self,
        brand_name: str,
        keywords: List[str],
        competitors: List[str],
        num_queries: int
    ) -> List[Dict[str, Any]]:
        """Generate queries across multiple intent types"""
        queries = []
        
        # Calculate queries per type
        queries_per_type = {}
        remaining = num_queries
        
        for qtype, ratio in QUERY_TYPE_DISTRIBUTION.items():
            count = int(num_queries * ratio)
            queries_per_type[qtype] = count
            remaining -= count
        
        # Distribute remaining to largest types
        for qtype in ["transactional", "comparative"]:
            if remaining > 0:
                queries_per_type[qtype] += 1
                remaining -= 1
        
        # Generate queries for each type
        for qtype, count in queries_per_type.items():
            type_queries = self._generate_queries_for_type(
                qtype, brand_name, keywords, competitors, count
            )
            queries.extend(type_queries)
        
        return queries[:num_queries]
    
    def _generate_queries_for_type(
        self,
        query_type: str,
        brand_name: str,
        keywords: List[str],
        competitors: List[str],
        count: int
    ) -> List[Dict[str, Any]]:
        """Generate queries for a specific intent type"""
        templates = {
            "transactional": [
                f"Où acheter {brand_name} ?",
                f"Prix de {brand_name}",
                f"Acheter {brand_name} en ligne",
                f"Meilleure offre {brand_name}",
            ],
            "comparative": [
                f"{brand_name} vs {competitors[0] if competitors else 'concurrent'}",
                f"Différence entre {brand_name} et {competitors[0] if competitors else 'autres'}",
                f"Comparatif {brand_name}",
                f"Alternative à {competitors[0] if competitors else brand_name}",
            ],
            "informational": [
                f"Qu'est-ce que {brand_name} ?",
                f"Comment fonctionne {brand_name} ?",
                f"{brand_name} avis",
                f"Caractéristiques de {brand_name}",
            ],
            "local": [
                f"{brand_name} près de moi",
                f"Boutique {brand_name} Paris",
                f"Magasin {brand_name}",
            ],
            "recommendation": [
                f"Meilleur {keywords[0] if keywords else 'produit'} 2025",
                f"Top solutions {keywords[0] if keywords else 'du marché'}",
                f"Recommandation {keywords[0] if keywords else 'expert'}",
            ],
            "review": [
                f"Avis {brand_name}",
                f"Test {brand_name}",
                f"Retour d'expérience {brand_name}",
            ]
        }
        
        base_templates = templates.get(query_type, templates["informational"])
        queries = []
        
        # Add base templates
        for template in base_templates[:count]:
            queries.append({
                "text": template,
                "type": query_type,
                "keyword": brand_name
            })
        
        # Add keyword variations
        for keyword in keywords[:count - len(queries)]:
            if query_type == "transactional":
                queries.append({"text": f"Acheter {keyword}", "type": query_type, "keyword": keyword})
            elif query_type == "informational":
                queries.append({"text": f"Qu'est-ce que {keyword} ?", "type": query_type, "keyword": keyword})
            elif query_type == "recommendation":
                queries.append({"text": f"Meilleur {keyword}", "type": query_type, "keyword": keyword})
            else:
                queries.append({"text": f"{keyword} {brand_name}", "type": query_type, "keyword": keyword})
        
        return queries[:count]
    
    def _analyze_query_types(self, query_results: List[Dict]) -> Dict[str, Any]:
        """Analyze results by query type"""
        breakdown = {}
        
        for qtype in QUERY_TYPE_DISTRIBUTION.keys():
            type_queries = [q for q in query_results if q.get("query_type") == qtype]
            if type_queries:
                breakdown[qtype] = {
                    "count": len(type_queries),
                    "avg_score": round(sum(q.get("avg_score", 0) for q in type_queries) / len(type_queries), 1),
                    "mention_rate": round(sum(q.get("mention_rate", 0) for q in type_queries) / len(type_queries), 1)
                }
        
        return breakdown
    
    def _build_competitor_comparison(
        self,
        discovered_competitors: List[Dict],
        user_competitors: List[str]
    ) -> List[Dict]:
        """Build comprehensive competitor comparison"""
        comparison = []
        already_added = set()
        
        for comp in discovered_competitors[:10]:
            comp_name = comp["name"]
            already_added.add(comp_name.lower())
            comparison.append({
                "competitor": comp_name,
                "mentions": comp.get("mentions", 0),
                "visibility_rate": comp.get("visibility_score", 0),
                "presence_rate": comp.get("presence_rate", 0),
                "ai_sources": comp.get("ai_sources", []),
                "discovered": comp.get("discovered", True),
                "user_defined": comp.get("user_defined", False),
                "responses_containing": comp.get("responses_containing", 0)
            })
        
        # Add user-defined competitors not discovered
        for comp in user_competitors[:5]:
            if comp.lower() not in already_added:
                comparison.append({
                    "competitor": comp,
                    "mentions": 0,
                    "visibility_rate": 0,
                    "presence_rate": 0,
                    "ai_sources": [],
                    "discovered": False,
                    "user_defined": True,
                    "responses_containing": 0
                })
        
        return comparison
    
    def _summarize_brand_mentions(
        self,
        brand_variants: List[str],
        mention_details: List[Dict]
    ) -> Dict[str, Any]:
        """Summarize brand mention analysis"""
        quality_counts = {}
        variants_found_counts = {}
        
        for detail in mention_details:
            quality = detail.get("mention_quality", "unknown")
            quality_counts[quality] = quality_counts.get(quality, 0) + 1
            for variant in detail.get("variants_found", []):
                variants_found_counts[variant] = variants_found_counts.get(variant, 0) + 1
        
        return {
            "variants_used": brand_variants[:20],
            "mention_details": mention_details[:50],
            "mention_quality_distribution": quality_counts,
            "variants_found_summary": dict(sorted(variants_found_counts.items(), key=lambda x: -x[1])[:10])
        }
    
    async def _analyze_site_enrichment(self, url: str) -> Dict[str, Any]:
        """Analyze website for GEO optimization opportunities"""
        result = {
            "url": url,
            "analyzed": False,
            "signals": {},
            "recommendations": []
        }
        
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.get(url, follow_redirects=True)
                if response.status_code != 200:
                    return result
                
                soup = BeautifulSoup(response.text, "html.parser")
                
                # Check for schema.org markup
                schema_scripts = soup.find_all("script", type="application/ld+json")
                has_schema = len(schema_scripts) > 0
                
                # Check for FAQ section
                faq_elements = soup.find_all(["h2", "h3"], string=re.compile(r"FAQ|Questions|Fréquentes", re.I))
                has_faq = len(faq_elements) > 0
                
                # Check for trust signals
                trust_signals = []
                trust_patterns = ["certifié", "garanti", "sécurisé", "ssl", "avis", "client", "témoignage"]
                page_text = soup.get_text().lower()
                for pattern in trust_patterns:
                    if pattern in page_text:
                        trust_signals.append(pattern)
                
                # Check meta tags
                meta_desc = soup.find("meta", attrs={"name": "description"})
                has_meta_desc = meta_desc is not None and len(meta_desc.get("content", "")) > 50
                
                result["analyzed"] = True
                result["signals"] = {
                    "has_schema_markup": has_schema,
                    "has_faq_section": has_faq,
                    "trust_signals": trust_signals[:5],
                    "has_meta_description": has_meta_desc
                }
                
                # Generate recommendations
                if not has_schema:
                    result["recommendations"].append({
                        "priority": "high",
                        "action": "Ajouter des données structurées Schema.org",
                        "impact": "Améliore la compréhension du contenu par les IA"
                    })
                
                if not has_faq:
                    result["recommendations"].append({
                        "priority": "medium",
                        "action": "Ajouter une section FAQ",
                        "impact": "Augmente les chances d'être cité pour les questions fréquentes"
                    })
                
                if not has_meta_desc:
                    result["recommendations"].append({
                        "priority": "medium",
                        "action": "Optimiser la meta description",
                        "impact": "Améliore le contexte fourni aux IA"
                    })
                
        except Exception as e:
            logger.warning(f"Site enrichment analysis failed for {url}: {e}")
        
        return result


# Singleton instance
analysis_pipeline = AnalysisPipelineService()
