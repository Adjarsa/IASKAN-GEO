"""
Content Generation Router - GEO Optimized Content Creation
Migrated from server.py for better code organization
Includes FIX for fake geo_score formula
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
import asyncio
import logging
import os
import uuid
from concurrent.futures import ThreadPoolExecutor

from ..routers.auth import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["content"])

# Thread pool for LLM calls
content_executor = ThreadPoolExecutor(max_workers=2)

# Get API keys
EMERGENT_LLM_KEY = os.environ.get('EMERGENT_LLM_KEY')


# ================== MODELS ==================

class ContentGenerateRequest(BaseModel):
    project_id: Optional[str] = None
    content_type: str  # article, faq, entity, guide, comparison
    topic: str
    keywords: Optional[List[str]] = []
    brand_name: Optional[str] = ""


class ContentReformulateRequest(BaseModel):
    project_id: Optional[str] = None
    content: str
    brand_name: Optional[str] = ""


# ================== CONTENT PROMPTS ==================

def get_content_prompt(content_type: str, topic: str, brand_name: str, keywords: List[str]) -> str:
    """Get the appropriate prompt for content generation"""
    keywords_str = ', '.join(keywords) if keywords else 'aucun specifie'
    brand = brand_name or 'la marque'
    
    prompts = {
        "article": f"""Genere un article de blog optimise pour le GEO (Generative Engine Optimization) sur le sujet: "{topic}"
        
Marque a mettre en avant: {brand}
Mots-cles a integrer: {keywords_str}

L'article doit suivre les criteres E-E-A-T (Experience, Expertise, Authority, Trust):
- Inclure des definitions claires en debut de section
- Ajouter des donnees chiffrees et statistiques
- Utiliser des listes a puces pour la structure
- Inclure des citations d'experts ou sources fiables
- Adopter un ton factuel et professionnel

Structure requise:
1. Titre accrocheur (H1)
2. Introduction avec definition claire
3. 3-5 sections avec sous-titres (H2)
4. Listes a puces dans chaque section
5. Conclusion avec call-to-action
6. FAQ de 3 questions

Longueur: 800-1200 mots
Format: Markdown""",

        "faq": f"""Genere une FAQ optimisee GEO (Generative Engine Optimization) sur le sujet: "{topic}"

Marque concernee: {brand}
Mots-cles: {keywords_str}

La FAQ doit:
- Contenir 8-10 questions frequentes
- Questions formulees naturellement (comme un utilisateur les poserait)
- Reponses concises (2-4 phrases max)
- Inclure des chiffres et donnees factuelles
- Etre structuree en format Q/R clair

Format de chaque question:
**Q: [Question claire et naturelle]**
R: [Reponse directe, factuelle, avec donnee chiffree si possible]

Genere la FAQ en francais, format Markdown.""",

        "entity": f"""Genere une fiche d'entite optimisee GEO pour: "{topic}"

Marque/Entite: {brand or topic}

La fiche doit inclure (format structure):

# [Nom de l'entite]

## Informations Generales
- **Type**: [Type d'entite: entreprise, produit, service, personne]
- **Secteur**: [Secteur d'activite]
- **Description**: [Description en 2-3 phrases]

## Identite
- **Date de creation**: [Si applicable]
- **Siege social**: [Localisation]
- **Fondateurs/Dirigeants**: [Noms]

## Activites Principales
[Liste des produits/services principaux]

## Points Cles
[5-7 points factuels importants]

## Liens Associes
[Entites liees, partenaires, concurrents]

Format: Markdown structure pour faciliter le parsing par les LLMs""",

        "guide": f"""Genere un guide definitif et exhaustif optimise GEO sur: "{topic}"

Marque a integrer: {brand}
Mots-cles: {keywords_str}

Le guide doit etre un contenu pilier ("pillar content") qui:
- Couvre le sujet de maniere exhaustive
- Etablit l'autorite de la marque
- Est structure pour etre facilement cite par les LLMs

Structure requise:
1. **Titre**: Guide Definitif: [Sujet] en [Annee]
2. **Meta-description**: 150-160 caracteres
3. **Introduction**: Pourquoi ce guide, pour qui, ce qu'on va apprendre
4. **Sommaire**: Liste des sections
5. **Sections principales** (5-8 sections):
   - Chaque section avec H2
   - Sous-sections avec H3
   - Listes a puces
   - Encadres "A retenir"
   - Donnees chiffrees
6. **Conclusion**: Resume + prochaines etapes
7. **Ressources**: Liens et references

Longueur: 1500-2000 mots
Format: Markdown""",

        "comparison": f"""Genere un comparatif structure et optimise GEO sur: "{topic}"

Marque a mettre en avant: {brand}
Mots-cles: {keywords_str}

Le comparatif doit:
- Comparer 3-5 options/solutions
- Utiliser un format tableau clair
- Inclure des criteres objectifs et mesurables
- Donner une recommandation finale

Structure:
1. **Introduction**: Contexte du comparatif
2. **Criteres de comparaison**: Liste des criteres evalues
3. **Tableau comparatif**: (format Markdown)
| Critere | Option 1 | Option 2 | Option 3 |
|---------|----------|----------|----------|
4. **Analyse detaillee**: Pour chaque option
5. **Verdict**: Recommendation selon les cas d'usage
6. **FAQ**: 3 questions sur le choix

Format: Markdown avec tableaux"""
    }
    
    return prompts.get(content_type, prompts["article"])


def calculate_real_geo_score(content: str, keywords: List[str], brand_name: str) -> int:
    """
    Calculate a REAL GEO score based on actual content analysis.
    FIXES the fake formula: min(95, 75 + keywords*2)
    
    Scoring criteria:
    - Structure (H1, H2, H3 headers): 0-20 points
    - Lists (bullet points, numbered): 0-15 points
    - Data (numbers, statistics): 0-15 points
    - Keywords presence: 0-15 points
    - Brand mentions: 0-10 points
    - Length adequacy: 0-10 points
    - FAQ presence: 0-10 points
    - Sources/citations: 0-5 points
    """
    score = 0
    content_lower = content.lower()
    
    # Structure score (0-20)
    h1_count = content.count('# ') - content.count('## ')
    h2_count = content.count('## ') - content.count('### ')
    h3_count = content.count('### ')
    
    if h1_count >= 1:
        score += 5
    if h2_count >= 3:
        score += 10
    elif h2_count >= 1:
        score += 5
    if h3_count >= 2:
        score += 5
    
    # Lists score (0-15)
    bullet_count = content.count('\n- ') + content.count('\n* ')
    numbered_count = len([line for line in content.split('\n') if line.strip() and line.strip()[0].isdigit() and '. ' in line[:4]])
    
    if bullet_count >= 5:
        score += 10
    elif bullet_count >= 2:
        score += 5
    if numbered_count >= 3:
        score += 5
    
    # Data/statistics score (0-15)
    import re
    numbers = re.findall(r'\b\d+(?:[,.]\d+)?(?:\s*%|\s*€|\s*\$)?\b', content)
    if len(numbers) >= 10:
        score += 15
    elif len(numbers) >= 5:
        score += 10
    elif len(numbers) >= 2:
        score += 5
    
    # Keywords presence (0-15)
    if keywords:
        keywords_found = sum(1 for kw in keywords if kw.lower() in content_lower)
        keywords_ratio = keywords_found / len(keywords) if keywords else 0
        score += int(keywords_ratio * 15)
    else:
        score += 8  # Default if no keywords specified
    
    # Brand mentions (0-10)
    if brand_name:
        brand_count = content_lower.count(brand_name.lower())
        if brand_count >= 3:
            score += 10
        elif brand_count >= 1:
            score += 5
    else:
        score += 5  # Default
    
    # Length adequacy (0-10)
    word_count = len(content.split())
    if 800 <= word_count <= 2000:
        score += 10
    elif 500 <= word_count <= 2500:
        score += 7
    elif word_count >= 300:
        score += 4
    
    # FAQ presence (0-10)
    if 'faq' in content_lower or 'questions' in content_lower or '**q:' in content_lower:
        score += 10
    
    # Sources/citations (0-5)
    citation_indicators = ['source', 'selon', "d'après", 'étude', 'rapport', 'recherche']
    if any(ind in content_lower for ind in citation_indicators):
        score += 5
    
    return min(100, max(0, score))


def get_content_tips(content_type: str) -> List[str]:
    """Get tips for each content type"""
    tips = {
        "article": [
            "Ajoutez des images avec alt-text descriptif",
            "Incluez des liens internes vers vos autres contenus",
            "Mettez a jour regulierement avec des donnees recentes"
        ],
        "faq": [
            "Ajoutez le schema FAQPage pour le structured data",
            "Liez chaque reponse a une page plus detaillee",
            "Testez les questions dans les moteurs IA"
        ],
        "entity": [
            "Ajoutez cette fiche sur votre page A propos",
            "Implementez le schema Organization",
            "Synchronisez avec Google Business Profile"
        ],
        "guide": [
            "Creez une table des matieres cliquable",
            "Ajoutez des ancres pour chaque section",
            "Proposez une version PDF telechargeable"
        ],
        "comparison": [
            "Mettez a jour les donnees chaque trimestre",
            "Ajoutez des liens d'affiliation si applicable",
            "Incluez des temoignages utilisateurs"
        ]
    }
    return tips.get(content_type, [])


async def call_llm_for_content(prompt: str) -> str:
    """Call LLM for content generation using Emergent LLM Key"""
    try:
        from ..services.llm_abstraction import LlmChat, UserMessage
        
        chat = LlmChat(
            api_key=EMERGENT_LLM_KEY,
            session_id=f"geo-content-{uuid.uuid4().hex[:8]}",
            system_message="Tu es un expert en content marketing et GEO (Generative Engine Optimization). Tu crees du contenu optimise pour etre cite par les LLMs comme ChatGPT, Claude, Gemini. Reponds toujours en francais avec un contenu riche, structure et factuel. Utilise le format Markdown."
        )
        
        chat = chat.with_model("openai", "gpt-4o")
        user_message = UserMessage(text=prompt)
        response = await chat.send_message(user_message)
        return response
        
    except Exception as e:
        logger.error(f"LLM call error: {e}")
        raise


# ================== ENDPOINTS ==================

@router.post("/content/generate")
async def generate_geo_content(request: ContentGenerateRequest, user: dict = Depends(get_current_user)):
    """Generate GEO-optimized content using AI"""
    
    prompt = get_content_prompt(
        content_type=request.content_type,
        topic=request.topic,
        brand_name=request.brand_name or "",
        keywords=request.keywords or []
    )
    
    try:
        generated_text = await call_llm_for_content(prompt)
        
        # Calculate REAL GEO score (not fake formula)
        geo_score = calculate_real_geo_score(
            content=generated_text,
            keywords=request.keywords or [],
            brand_name=request.brand_name or ""
        )
        
        return {
            "content": generated_text,
            "content_type": request.content_type,
            "topic": request.topic,
            "word_count": len(generated_text.split()),
            "geo_score": geo_score,  # REAL score, not min(95, 75 + keywords*2)
            "tips": get_content_tips(request.content_type),
            "generated_at": datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as e:
        logger.error(f"Content generation error: {e}")
        raise HTTPException(status_code=500, detail=f"Erreur de generation: {str(e)}")


@router.post("/content/reformulate")
async def reformulate_content(request: ContentReformulateRequest, user: dict = Depends(get_current_user)):
    """Reformulate and optimize existing content for GEO"""
    
    prompt = f"""Analyse et optimise le contenu suivant pour le GEO (Generative Engine Optimization).

CONTENU ORIGINAL:
{request.content}

MARQUE A INTEGRER: {request.brand_name or 'la marque'}

INSTRUCTIONS D'OPTIMISATION:
1. Restructure le contenu pour une meilleure "parsabilite" par les LLMs
2. Ajoute des definitions claires en debut de paragraphe
3. Integre des donnees chiffrees et statistiques pertinentes
4. Utilise des listes a puces pour les enumerations
5. Ajoute des sous-titres (H2, H3) pour la structure
6. Renforce les signaux E-E-A-T (Experience, Expertise, Authority, Trust)
7. Suggere des donnees structurees a implementer

Fournis:
1. Le contenu optimise en format Markdown
2. Une liste de 5 ameliorations appliquees

Format de reponse:
===CONTENU OPTIMISE===
[Contenu reformule]

===AMELIORATIONS===
- [Amelioration 1]
- [Amelioration 2]
- [Amelioration 3]
- [Amelioration 4]
- [Amelioration 5]"""

    try:
        result = await call_llm_for_content(prompt)
        
        # Parse the response
        optimized_content = result
        suggestions = []
        
        if "===CONTENU OPTIMISE===" in result and "===AMELIORATIONS===" in result:
            parts = result.split("===AMELIORATIONS===")
            optimized_content = parts[0].replace("===CONTENU OPTIMISE===", "").strip()
            if len(parts) > 1:
                suggestions_text = parts[1].strip()
                suggestions = [s.strip().lstrip("- ") for s in suggestions_text.split("\n") if s.strip() and s.strip().startswith("-")]
        
        return {
            "optimized_content": optimized_content,
            "suggestions": suggestions[:5],
            "original_length": len(request.content.split()),
            "optimized_length": len(optimized_content.split()),
            "reformulated_at": datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as e:
        logger.error(f"Reformulation error: {e}")
        raise HTTPException(status_code=500, detail=f"Erreur d'optimisation: {str(e)}")
