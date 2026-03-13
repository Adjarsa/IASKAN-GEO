from fastapi import FastAPI, APIRouter, HTTPException, Request, Response, Depends
from fastapi.responses import StreamingResponse, RedirectResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict, EmailStr
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timezone, timedelta
import httpx
import json
import asyncio
from concurrent.futures import ThreadPoolExecutor
import io
import secrets
from fpdf import FPDF
from authlib.integrations.starlette_client import OAuth
from app.services.llm_abstraction import LlmChat, UserMessage
from app.services.stripe_abstraction import StripeCheckout, CheckoutSessionResponse, CheckoutStatusResponse, CheckoutSessionRequest
import resend

# Import new modular routers
from app.routers import (
    organizations, 
    article_optimizer, 
    admin, 
    onboarding,
    auth as auth_router,
    projects as projects_router,
    dashboard as dashboard_router,
    notifications as notifications_router,
    schedules as schedules_router,
    subscriptions as subscriptions_router,
    analysis as analysis_router,
    analyses as analyses_router,
)
from app.engines.query import query_engine, variation_engine
from app.engines.semantic import semantic_engine
from app.engines.influence import influence_engine
from app.engines.gap import gap_engine
from app.services.email_service import email_service

# Import PostgreSQL database module
from app.db import initialize_database, shutdown_database, USE_POSTGRES

# Thread pool for LLM calls to avoid blocking the event loop
llm_executor = ThreadPoolExecutor(max_workers=4)

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection (legacy - only initialized if not using PostgreSQL exclusively)
mongo_url = os.environ.get('MONGO_URL', '')
db = None
client = None
if mongo_url and not USE_POSTGRES:
    client = AsyncIOMotorClient(mongo_url)
    db = client[os.environ.get('DB_NAME', 'iaskan_db')]

# Get API keys
EMERGENT_LLM_KEY = os.environ.get('EMERGENT_LLM_KEY')
STRIPE_API_KEY = os.environ.get('STRIPE_API_KEY')

# OAuth Configuration
MICROSOFT_CLIENT_ID = os.environ.get('MICROSOFT_CLIENT_ID', '')
MICROSOFT_CLIENT_SECRET = os.environ.get('MICROSOFT_CLIENT_SECRET', '')
LINKEDIN_CLIENT_ID = os.environ.get('LINKEDIN_CLIENT_ID', '')
LINKEDIN_CLIENT_SECRET = os.environ.get('LINKEDIN_CLIENT_SECRET', '')

# Email Configuration
RESEND_API_KEY = os.environ.get('RESEND_API_KEY', '')
SENDER_EMAIL = os.environ.get('SENDER_EMAIL', 'noreply@iaskan.com')
if RESEND_API_KEY:
    resend.api_key = RESEND_API_KEY

# Create the main app
app = FastAPI(title="IAskan API", version="1.0.0")

# Add session middleware for OAuth state management
app.add_middleware(SessionMiddleware, secret_key=secrets.token_hex(32))

# Create router with /api prefix
api_router = APIRouter(prefix="/api")

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ================== MODELS ==================

class UserBase(BaseModel):
    model_config = ConfigDict(extra="ignore")
    user_id: str
    email: str
    name: str
    picture: Optional[str] = None
    company: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class UserSession(BaseModel):
    model_config = ConfigDict(extra="ignore")
    session_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    session_token: str
    expires_at: datetime
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class Project(BaseModel):
    model_config = ConfigDict(extra="ignore")
    project_id: str = Field(default_factory=lambda: f"proj_{uuid.uuid4().hex[:12]}")
    user_id: str
    name: str
    website_url: str
    brand_name: str
    logo_url: Optional[str] = None  # Brand logo URL (auto-fetched from favicon or user-provided)
    competitors: List[str] = []  # User-defined competitors
    discovered_competitors: List[Dict[str, Any]] = []  # Competitors discovered from AI analysis
    keywords: List[str] = []
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class Analysis(BaseModel):
    model_config = ConfigDict(extra="ignore")
    analysis_id: str = Field(default_factory=lambda: f"ana_{uuid.uuid4().hex[:12]}")
    project_id: str
    user_id: str
    status: str = "pending"  # pending, running, completed, failed
    global_score: float = 0.0
    grade: str = "N/A"  # A, B, C, D, F
    rate_score: Dict[str, Any] = {}  # R.A.T.E scores with weights
    ai_scores: Dict[str, float] = {}  # Score per AI
    query_scores: List[Dict[str, Any]] = []
    recommendations: List[Dict[str, Any]] = []
    competitor_comparison: List[Dict[str, Any]] = []
    # IAskan Verified GEO Protocol™ fields
    indices: Dict[str, float] = {}  # Stability Index™, Dominance Index™, Trust Gap™, Opportunity Score™
    stability_data: Dict[str, Any] = {}  # Detailed stability metrics
    query_type_breakdown: Dict[str, Any] = {}  # Breakdown by query type
    analysis_summary: Dict[str, Any] = {}  # Protocol metadata
    current_phase: str = "pending"  # query_generation, ai_querying, calculating_indices, completed
    protocol_version: str = "IAskan Verified GEO Protocol™ v2.0"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: Optional[datetime] = None

class Query(BaseModel):
    model_config = ConfigDict(extra="ignore")
    query_id: str = Field(default_factory=lambda: f"qry_{uuid.uuid4().hex[:12]}")
    analysis_id: str
    text: str
    intent_type: str  # commercial, informational, local, transactional, conversational
    ai_responses: Dict[str, Dict[str, Any]] = {}  # AI name -> response data
    scores: Dict[str, float] = {}
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class Subscription(BaseModel):
    model_config = ConfigDict(extra="ignore")
    subscription_id: str = Field(default_factory=lambda: f"sub_{uuid.uuid4().hex[:12]}")
    user_id: str
    plan: str  # starter, pro, business
    status: str = "active"  # active, cancelled, expired, trial
    queries_limit: int = 300
    queries_used: int = 0
    trial_ends_at: Optional[datetime] = None
    current_period_start: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

# ================== EMAIL VERIFICATION SYSTEM ==================

class EmailVerificationToken(BaseModel):
    """Token for email verification"""
    model_config = ConfigDict(extra="ignore")
    token_id: str = Field(default_factory=lambda: f"evt_{uuid.uuid4().hex[:12]}")
    user_id: str
    email: str
    token: str = Field(default_factory=lambda: secrets.token_urlsafe(32))
    expires_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc) + timedelta(hours=24))
    used: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

# ================== NOTIFICATION SYSTEM ==================

class Notification(BaseModel):
    """User notifications for completed scans, etc."""
    model_config = ConfigDict(extra="ignore")
    notification_id: str = Field(default_factory=lambda: f"notif_{uuid.uuid4().hex[:12]}")
    user_id: str
    type: str  # scan_complete, scan_failed, subscription_expiring, etc.
    title: str
    message: str
    data: Dict[str, Any] = {}  # Additional data (analysis_id, project_id, etc.)
    read: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

# ================== SCHEDULED SCANS SYSTEM ==================

class ScanSchedule(BaseModel):
    """Schedule configuration for automated scans"""
    model_config = ConfigDict(extra="ignore")
    schedule_id: str = Field(default_factory=lambda: f"sched_{uuid.uuid4().hex[:12]}")
    project_id: str
    user_id: str
    enabled: bool = True
    frequency: str = "weekly"  # daily, weekly, monthly
    day_of_week: int = 0  # 0=Monday, 6=Sunday (for weekly)
    day_of_month: int = 1  # 1-28 (for monthly)
    hour: int = 9  # 0-23, hour to run scan
    minute: int = 0  # 0-59
    timezone: str = "Europe/Paris"
    send_report_email: bool = True
    report_recipients: List[str] = []  # Additional email recipients
    last_run: Optional[str] = None
    next_run: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

# ================== ANTI-ABUSE SYSTEM ==================

class FreeTrialUsage(BaseModel):
    """Track free trial usage to prevent abuse"""
    model_config = ConfigDict(extra="ignore")
    usage_id: str = Field(default_factory=lambda: f"ftu_{uuid.uuid4().hex[:12]}")
    email: str
    email_domain: str
    ip_address: str
    fingerprint: str
    analyzed_domain: str  # The domain that was analyzed for free
    user_id: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

# List of known temporary/disposable email domains
BLOCKED_EMAIL_DOMAINS = {
    # Common disposable email services
    "tempmail.com", "temp-mail.org", "guerrillamail.com", "guerrillamail.org",
    "10minutemail.com", "10minutemail.net", "mailinator.com", "mailinator.net",
    "throwaway.email", "throwawaymail.com", "fakeinbox.com", "sharklasers.com",
    "trashmail.com", "trashmail.net", "trashmail.org", "mailnesia.com",
    "tempail.com", "dispostable.com", "mintemail.com", "tempr.email",
    "discard.email", "discardmail.com", "spamgourmet.com", "mytrashmail.com",
    "mailexpire.com", "maildrop.cc", "getairmail.com", "getnada.com",
    "yopmail.com", "yopmail.fr", "yopmail.net", "cool.fr.nf", "jetable.fr.nf",
    "nospam.ze.tc", "nomail.xl.cx", "mega.zik.dj", "speed.1s.fr", "courriel.fr.nf",
    "moncourrier.fr.nf", "monemail.fr.nf", "monmail.fr.nf", "hide.biz.st",
    "myspaceppl.com", "soodonims.com", "uggsrock.com", "hochsitze.com",
    "hulapla.de", "teleworm.us", "superrito.com", "binkmail.com", "safetymail.info",
    "spamobox.com", "spambox.us", "spam4.me", "grr.la", "spamfree24.org",
    "spamfree24.de", "spamfree24.eu", "spamfree24.info", "spamfree24.net",
    "emailondeck.com", "tempsky.com", "tempmailaddress.com", "burnermail.io",
    "mohmal.com", "emailfake.com", "emaillime.com", "emailsensei.com",
    "fakemail.net", "fakemailgenerator.com", "generator.email", "inboxalias.com",
    "mailcatch.com", "mailsac.com", "mailslurp.com", "moakt.com", "mt2015.com",
    "mytemp.email", "one-time.email", "onetimeusemail.com", "privy-mail.com",
    "spamherelots.com", "tempinbox.com", "tempmails.net", "tmpmail.net",
    "tmpmail.org", "wegwerfmail.de", "wegwerfmail.net", "wegwerfmail.org",
    "zoemail.com", "ezehe.com", "xcodes.net", "nwytg.net", "edumail.icu",
}

class PaymentTransaction(BaseModel):
    model_config = ConfigDict(extra="ignore")
    transaction_id: str = Field(default_factory=lambda: f"txn_{uuid.uuid4().hex[:12]}")
    user_id: str
    session_id: str
    amount: float
    currency: str = "eur"
    plan: str
    status: str = "pending"  # pending, paid, failed, expired
    payment_status: str = "initiated"
    metadata: Dict[str, str] = {}
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

# ================== SUBSCRIPTION PLANS ==================

SUBSCRIPTION_PLANS = {
    "free": {
        "name": "Essai Gratuit",
        "price": 0,
        "queries_limit": 90,
        "scans_limit": 1,
        "projects_limit": 1,
        "num_prompts": 30,
        "runs_per_query": 3,
        "ai_engines": ["chatgpt"],
        "features": ["1 scan offert", "30 prompts", "ChatGPT uniquement", "Rapport standard", "1 projet"],
        "article_optimizer": False,
        "article_optimizer_limit": 0,
        "organizations": False
    },
    "starter": {
        "name": "Starter",
        "price": 79.00,
        "queries_limit": 1500,
        "scans_limit": 10,
        "projects_limit": 1,
        "num_prompts": 50,
        "runs_per_query": 3,
        "ai_engines": ["chatgpt"],
        "features": ["10 scans/mois", "50 prompts/scan", "150 requêtes/scan", "1 500 requêtes/mois", "ChatGPT uniquement", "Rapport standard", "Support email", "5 optimisations d'articles/mois"],
        "article_optimizer": True,
        "article_optimizer_limit": 5,
        "organizations": False
    },
    "pro": {
        "name": "Pro",
        "price": 149.00,
        "queries_limit": 80000,
        "scans_limit": 50,
        "projects_limit": 5,
        "num_prompts": 100,
        "runs_per_query": 4,
        "ai_engines": ["chatgpt", "claude", "gemini", "perplexity"],
        "features": ["50 scans/mois", "100 prompts/scan", "4 runs/requête", "1 600 requêtes/scan", "80 000 requêtes/mois", "4 IA (ChatGPT, Claude, Gemini, Perplexity)", "Benchmark concurrents", "Analyse de stabilité", "Scans programmés + rapport par email", "5 projets", "30 optimisations d'articles/mois", "Support prioritaire"],
        "article_optimizer": True,
        "article_optimizer_limit": 30,
        "organizations": True
    },
    "business": {
        "name": "Business",
        "price": 349.00,
        "queries_limit": 600000,
        "scans_limit": 150,
        "projects_limit": -1,
        "num_prompts": 200,
        "runs_per_query": 5,
        "ai_engines": ["chatgpt", "claude", "gemini", "perplexity"],
        "features": ["150 scans/mois", "200 prompts/scan", "5 runs/requête", "4 000 requêtes/scan", "600 000 requêtes/mois", "4 IA", "Génération d'articles GEO", "Intelligence stratégique", "Scans programmés + rapport par email", "Projets illimités", "Optimisations illimitées", "Organisations/Équipes", "Support dédié"],
        "article_optimizer": True,
        "article_optimizer_limit": -1,
        "organizations": True
    }
}

# ================== AUTH HELPERS ==================

async def get_favicon_url(website_url: str) -> Optional[str]:
    """Extract favicon/logo URL from a website using multiple methods"""
    try:
        if not website_url:
            return None
            
        # Clean the URL
        if not website_url.startswith(('http://', 'https://')):
            website_url = f"https://{website_url}"
        
        from urllib.parse import urlparse
        parsed = urlparse(website_url)
        domain = parsed.netloc.replace("www.", "")
        
        # Try Clearbit for higher quality logos first
        clearbit_logo = f"https://logo.clearbit.com/{domain}"
        
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.head(clearbit_logo)
                if response.status_code == 200:
                    return clearbit_logo
        except:
            pass
        
        # Fallback to Google's favicon service (most reliable)
        return f"https://www.google.com/s2/favicons?domain={domain}&sz=128"
        
    except Exception as e:
        logger.error(f"Error fetching favicon: {e}")
        return None

def extract_competitors_from_response(response_text: str, brand_name: str) -> List[Dict[str, Any]]:
    """Extract competitor brand names mentioned in AI responses"""
    competitors_found = []
    brand_lower = brand_name.lower()
    
    import re
    
    # Find all potential brand names (capitalized words, possibly with .com/.fr etc)
    potential_brands = re.findall(r'\b([A-Z][a-zA-Z0-9]*(?:\.[a-z]{2,4})?)\b', response_text)
    
    # Filter and count mentions
    brand_counts = {}
    for brand in potential_brands:
        brand_clean = brand.lower().replace('.com', '').replace('.fr', '').replace('.io', '')
        # Skip if it's the user's brand or common words
        skip_words = {'le', 'la', 'les', 'un', 'une', 'des', 'de', 'du', 'en', 'pour', 'avec', 
                      'sur', 'par', 'dans', 'qui', 'que', 'est', 'sont', 'cette', 'ces',
                      'ai', 'ia', 'seo', 'geo', 'url', 'api', 'http', 'https', 'www',
                      'france', 'paris', 'europe', 'monde', 'web', 'site', 'page'}
        
        if (brand_clean not in skip_words and 
            brand_clean != brand_lower and 
            len(brand_clean) > 2):
            brand_counts[brand] = brand_counts.get(brand, 0) + 1
    
    # Convert to list sorted by frequency
    for brand, count in sorted(brand_counts.items(), key=lambda x: -x[1]):
        if count >= 1:  # Mentioned at least once
            competitors_found.append({
                "name": brand,
                "mentions": count,
                "source": "ai_analysis"
            })
    
    return competitors_found[:10]  # Return top 10

async def identify_competitors_from_analysis(all_responses: List[Dict[str, Any]], brand_name: str, user_competitors: List[str] = None) -> List[Dict[str, Any]]:
    """
    Analyze all AI responses to identify competitors mentioned.
    Uses multiple strategies:
    1. Known brands database
    2. User-defined competitors tracking
    3. NLP-based entity extraction (proper nouns pattern)
    """
    import re
    
    all_competitors = {}
    brand_lower = brand_name.lower()
    brand_words = set(brand_lower.split())
    user_competitors = user_competitors or []
    
    # Extended list of known brands across industries
    known_brands = [
        # Tech Giants
        "Apple", "Google", "Microsoft", "Amazon", "Meta", "Facebook", "IBM", "Oracle", "Salesforce",
        "Adobe", "SAP", "Cisco", "Intel", "AMD", "Nvidia", "Qualcomm",
        # Consumer Electronics
        "Samsung", "Sony", "LG", "Huawei", "Xiaomi", "OnePlus", "Oppo", "Vivo", "Realme",
        "Nokia", "Motorola", "Asus", "Acer", "Dell", "HP", "Lenovo", "MSI",
        # E-commerce & Marketplaces
        "Alibaba", "eBay", "Shopify", "Etsy", "Rakuten", "Cdiscount", "Fnac", "Darty",
        # Fashion & Retail
        "Nike", "Adidas", "Puma", "Zara", "H&M", "Uniqlo", "Gap", "Levis", "Primark",
        # Entertainment & Media
        "Netflix", "Disney", "HBO", "Spotify", "Apple Music", "YouTube", "TikTok", "Twitch",
        # Travel & Hospitality
        "Uber", "Airbnb", "Booking", "Expedia", "Tripadvisor", "Kayak", "Hotels.com",
        # Automotive
        "Tesla", "BMW", "Mercedes", "Audi", "Toyota", "Honda", "Ford", "Volkswagen", "Porsche", "Renault", "Peugeot", "Citroën",
        # Food & Beverage
        "Coca-Cola", "Pepsi", "McDonald's", "Starbucks", "KFC", "Burger King", "Subway",
        # Beauty & Personal Care
        "L'Oréal", "Sephora", "Estée Lauder", "Nivea", "Dove", "Garnier",
        # Home & Appliances
        "Dyson", "Philips", "Bosch", "Siemens", "IKEA", "Electrolux", "Whirlpool",
        # Sports & Outdoor
        "Decathlon", "Intersport", "Go Sport",
        # Telecom (French)
        "Orange", "SFR", "Bouygues", "Free", "Sosh", "RED", "B&You",
        # Finance & Insurance
        "PayPal", "Stripe", "Square", "Revolut", "N26", "Boursorama", "Fortuneo",
        # Software & SaaS
        "Slack", "Zoom", "Trello", "Asana", "Monday", "Notion", "Airtable", "HubSpot", "Mailchimp",
        "Zendesk", "Intercom", "Freshdesk", "Semrush", "Ahrefs", "Moz", "Majestic",
        # Cloud & Hosting
        "AWS", "Azure", "GCP", "OVH", "DigitalOcean", "Heroku", "Vercel", "Netlify",
        # Product Names
        "iPhone", "iPad", "MacBook", "iMac", "Galaxy", "Pixel", "Surface", "ThinkPad",
        "PlayStation", "Xbox", "Nintendo", "Switch", "Steam",
        # Marketing & Analytics
        "Google Analytics", "Hotjar", "Mixpanel", "Amplitude", "Segment",
        # AI & LLM Tools
        "ChatGPT", "OpenAI", "Claude", "Anthropic", "Gemini", "Perplexity", "Jasper", "Copy.ai"
    ]
    
    def normalize_brand(name: str) -> str:
        """Normalize brand name for consistent tracking"""
        return name.strip().title()
    
    def is_own_brand(candidate: str) -> bool:
        """Check if the candidate is the user's own brand"""
        candidate_lower = candidate.lower()
        candidate_words = set(candidate_lower.split())
        
        # Direct match
        if candidate_lower == brand_lower:
            return True
        # Substring match
        if candidate_lower in brand_lower or brand_lower in candidate_lower:
            return True
        # Word overlap (more than 50% overlap)
        if brand_words and candidate_words:
            overlap = len(brand_words & candidate_words) / max(len(brand_words), len(candidate_words))
            if overlap > 0.5:
                return True
        return False
    
    def extract_potential_brands(text: str) -> List[str]:
        """
        Extract potential brand names using pattern matching.
        Looks for capitalized words/phrases that could be brand names.
        """
        potential = []
        
        # Extended list of common words to exclude (FR/EN)
        common_words = {
            # French common words
            'le', 'la', 'les', 'un', 'une', 'des', 'du', 'de', 'et', 'ou', 'mais', 'donc',
            'il', 'elle', 'ils', 'elles', 'nous', 'vous', 'je', 'tu', 'ce', 'cette', 'ces',
            'qui', 'que', 'quoi', 'dont', 'où', 'est', 'sont', 'être', 'avoir', 'fait',
            'plus', 'moins', 'très', 'bien', 'peut', 'peuvent', 'doit', 'doivent',
            'meilleur', 'meilleure', 'meilleurs', 'meilleures', 'premier', 'première',
            'voici', 'voilà', 'car', 'comme', 'alors', 'ainsi', 'cependant', 'toutefois',
            'pour', 'dans', 'par', 'sur', 'sous', 'avec', 'sans', 'chez', 'entre', 'vers',
            'après', 'avant', 'depuis', 'pendant', 'selon', 'contre', 'malgré',
            'tout', 'tous', 'toute', 'toutes', 'autre', 'autres', 'même', 'mêmes',
            'quel', 'quelle', 'quels', 'quelles', 'chaque', 'plusieurs', 'certain', 'certains',
            # English common words
            'the', 'a', 'an', 'and', 'or', 'but', 'for', 'with', 'from', 'to', 'in', 'on',
            'also', 'just', 'like', 'such', 'some', 'many', 'most', 'other', 'another',
            'will', 'would', 'could', 'should', 'may', 'might', 'must', 'can',
            'however', 'therefore', 'thus', 'hence', 'although', 'though', 'while',
            'this', 'that', 'these', 'those', 'here', 'there', 'where', 'when', 'what',
            'which', 'who', 'whom', 'whose', 'how', 'why', 'not', 'yes', 'all',
            'each', 'every', 'both', 'few', 'more', 'any', 'none', 'only', 'own',
            # Generic terms
            'best', 'top', 'new', 'old', 'first', 'last', 'next', 'good', 'great',
            'free', 'online', 'digital', 'tool', 'tools', 'service', 'services',
            'solution', 'solutions', 'platform', 'software', 'app', 'application',
            'website', 'site', 'page', 'data', 'system', 'feature', 'features'
        }
        
        # Find capitalized words that might be brands
        cap_pattern = r'\b([A-Z][a-zA-Z]{2,}(?:\s+[A-Z][a-zA-Z]+)?)\b'
        matches = re.findall(cap_pattern, text)
        
        for match in matches:
            match_lower = match.lower()
            # Skip common words and short matches
            if match_lower not in common_words and len(match) >= 3:
                potential.append(match)
        
        return potential
    
    # Process each AI response
    total_responses = len(all_responses)
    
    for response in all_responses:
        response_text = response.get("response_excerpt", "") or ""
        ai_type = response.get("ai_type", "unknown")
        
        # Skip empty or very short responses
        if not response_text or len(response_text) < 50:
            continue
        
        response_lower = response_text.lower()
        
        # Strategy 1: Check known brands
        for brand in known_brands:
            brand_check = brand.lower()
            
            # Skip our own brand
            if is_own_brand(brand):
                continue
            
            if brand_check in response_lower:
                count = response_lower.count(brand_check)
                normalized = normalize_brand(brand)
                
                if normalized in all_competitors:
                    all_competitors[normalized]["mentions"] += count
                    all_competitors[normalized]["ai_sources"].add(ai_type)
                    all_competitors[normalized]["responses_containing"] += 1
                else:
                    all_competitors[normalized] = {
                        "name": normalized,
                        "mentions": count,
                        "ai_sources": {ai_type},
                        "discovered": True,
                        "user_defined": False,
                        "responses_containing": 1
                    }
        
        # Strategy 2: Check user-defined competitors
        competitor_analysis = response.get("competitor_analysis", {})
        for comp_name, comp_data in competitor_analysis.items():
            if comp_data.get("mentioned", False):
                normalized = normalize_brand(comp_name)
                
                if normalized in all_competitors:
                    all_competitors[normalized]["mentions"] += 1
                    all_competitors[normalized]["ai_sources"].add(ai_type)
                    all_competitors[normalized]["responses_containing"] += 1
                    all_competitors[normalized]["user_defined"] = True
                else:
                    all_competitors[normalized] = {
                        "name": normalized,
                        "mentions": 1,
                        "ai_sources": {ai_type},
                        "discovered": False,
                        "user_defined": True,
                        "responses_containing": 1
                    }
        
        # Strategy 3: Extract potential brands using NLP patterns
        potential_brands = extract_potential_brands(response_text)
        for potential in potential_brands:
            potential_lower = potential.lower()
            
            # Skip if it's our brand or already tracked
            if is_own_brand(potential):
                continue
            
            # Skip if already in known brands (case insensitive)
            if any(potential_lower == kb.lower() for kb in known_brands):
                continue
            
            # Skip single common words that got through
            if len(potential.split()) == 1 and len(potential) < 4:
                continue
            
            normalized = normalize_brand(potential)
            
            # Only add if mentioned at least twice in this response (to reduce noise)
            if response_lower.count(potential_lower) >= 2:
                if normalized in all_competitors:
                    all_competitors[normalized]["mentions"] += 1
                    all_competitors[normalized]["ai_sources"].add(ai_type)
                    all_competitors[normalized]["responses_containing"] += 1
                else:
                    all_competitors[normalized] = {
                        "name": normalized,
                        "mentions": 1,
                        "ai_sources": {ai_type},
                        "discovered": True,
                        "user_defined": False,
                        "responses_containing": 1
                    }
    
    # Calculate visibility scores and convert to list
    result = []
    for name, data in all_competitors.items():
        mentions = data["mentions"]
        responses_containing = data.get("responses_containing", 1)
        ai_sources_count = len(data["ai_sources"])
        
        # Visibility score based on:
        # - Number of mentions (weighted)
        # - Number of responses containing the competitor
        # - Number of different AI engines mentioning it
        visibility_score = min(100, (
            (mentions * 3) +  # Each mention counts
            (responses_containing * 5) +  # Presence in multiple responses
            (ai_sources_count * 10)  # Cross-AI validation bonus
        ))
        
        # Presence rate: % of responses mentioning this competitor
        presence_rate = round((responses_containing / max(total_responses, 1)) * 100, 1)
        
        result.append({
            "name": data["name"],
            "mentions": mentions,
            "ai_sources": list(data["ai_sources"]),
            "discovered": data["discovered"],
            "user_defined": data.get("user_defined", False),
            "visibility_score": visibility_score,
            "presence_rate": presence_rate,
            "responses_containing": responses_containing
        })
    
    # Sort by visibility score (descending), then by mentions
    result.sort(key=lambda x: (-x["visibility_score"], -x["mentions"]))
    
    return result[:15]  # Return top 15 discovered competitors

# ================== ANTI-ABUSE VALIDATION FUNCTIONS ==================

def extract_domain_from_url(url: str) -> str:
    """Extract the root domain from a URL"""
    from urllib.parse import urlparse
    if not url:
        return ""
    if not url.startswith(('http://', 'https://')):
        url = f"https://{url}"
    parsed = urlparse(url)
    domain = parsed.netloc.lower()
    # Remove www. prefix
    if domain.startswith('www.'):
        domain = domain[4:]
    return domain

def extract_email_domain(email: str) -> str:
    """Extract domain from email address"""
    if not email or '@' not in email:
        return ""
    return email.split('@')[1].lower()

def is_temporary_email(email: str) -> bool:
    """Check if email is from a known temporary/disposable email service"""
    domain = extract_email_domain(email)
    return domain in BLOCKED_EMAIL_DOMAINS

async def check_free_trial_eligibility(
    email: str,
    ip_address: str,
    fingerprint: str,
    domain_to_analyze: str
) -> Dict[str, Any]:
    """
    Check if user is eligible for free trial
    Returns: {"eligible": bool, "reason": str, "blocked_by": str}
    """
    # Extract domains
    email_domain = extract_email_domain(email)
    analyzed_domain = extract_domain_from_url(domain_to_analyze)
    
    # Check 1: Temporary email
    if is_temporary_email(email):
        return {
            "eligible": False,
            "reason": "Les adresses email temporaires ne sont pas autorisées. Veuillez utiliser une adresse email permanente.",
            "blocked_by": "temporary_email"
        }
    
    # Check 2: Email already used for free trial
    existing_email = await db.free_trial_usage.find_one({"email": email.lower()})
    if existing_email:
        return {
            "eligible": False,
            "reason": "Cette adresse email a déjà utilisé l'essai gratuit.",
            "blocked_by": "email"
        }
    
    # Check 3: IP address already used for free trial
    existing_ip = await db.free_trial_usage.find_one({"ip_address": ip_address})
    if existing_ip:
        return {
            "eligible": False,
            "reason": "Un essai gratuit a déjà été utilisé depuis cette connexion.",
            "blocked_by": "ip_address"
        }
    
    # Check 4: Fingerprint already used for free trial
    if fingerprint and fingerprint != "unknown":
        existing_fp = await db.free_trial_usage.find_one({"fingerprint": fingerprint})
        if existing_fp:
            return {
                "eligible": False,
                "reason": "Un essai gratuit a déjà été utilisé depuis ce navigateur.",
                "blocked_by": "fingerprint"
            }
    
    # Check 5: Domain already analyzed for free
    if analyzed_domain:
        existing_domain = await db.free_trial_usage.find_one({"analyzed_domain": analyzed_domain})
        if existing_domain:
            return {
                "eligible": False,
                "reason": f"Le domaine '{analyzed_domain}' a déjà bénéficié d'une analyse gratuite.",
                "blocked_by": "domain"
            }
    
    return {"eligible": True, "reason": "Éligible à l'essai gratuit", "blocked_by": None}

async def record_free_trial_usage(
    email: str,
    ip_address: str,
    fingerprint: str,
    domain_analyzed: str,
    user_id: str
):
    """Record free trial usage to prevent future abuse"""
    usage = FreeTrialUsage(
        email=email.lower(),
        email_domain=extract_email_domain(email),
        ip_address=ip_address,
        fingerprint=fingerprint or "unknown",
        analyzed_domain=extract_domain_from_url(domain_analyzed),
        user_id=user_id
    )
    
    doc = usage.model_dump()
    doc["created_at"] = doc["created_at"].isoformat()
    await db.free_trial_usage.insert_one(doc)
    
    logger.info(f"Free trial usage recorded: email={email}, ip={ip_address}, domain={domain_analyzed}")

def get_client_ip(request: Request) -> str:
    """Get real client IP address considering proxies"""
    # Check common proxy headers
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        # X-Forwarded-For can contain multiple IPs, first one is the client
        return forwarded.split(",")[0].strip()
    
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip.strip()
    
    # Fallback to direct client
    if request.client:
        return request.client.host
    
    return "unknown"

# ================== EMAIL VERIFICATION FUNCTIONS ==================

async def create_verification_token(user_id: str, email: str) -> str:
    """Create a new email verification token"""
    # Invalidate any existing tokens for this user
    await db.email_verification_tokens.update_many(
        {"user_id": user_id, "used": False},
        {"$set": {"used": True}}
    )
    
    # Create new token
    token = EmailVerificationToken(user_id=user_id, email=email)
    doc = token.model_dump()
    doc["expires_at"] = doc["expires_at"].isoformat()
    doc["created_at"] = doc["created_at"].isoformat()
    await db.email_verification_tokens.insert_one(doc)
    
    return token.token

async def send_verification_email(email: str, user_name: str, token: str) -> bool:
    """Send verification email using Resend"""
    if not RESEND_API_KEY:
        logger.warning("RESEND_API_KEY not configured, skipping verification email")
        return False
    
    # Build verification URL
    frontend_url = os.environ.get('FRONTEND_URL', 'https://optimize-visibility.preview.emergentagent.com')
    verification_url = f"{frontend_url}/verify-email?token={token}"
    
    try:
        params = {
            "from": "IAskan <noreply@resend.dev>",
            "to": [email],
            "subject": "Vérifiez votre adresse email - IAskan",
            "html": f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="utf-8">
                <style>
                    body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; color: #1e293b; }}
                    .container {{ max-width: 600px; margin: 0 auto; padding: 40px 20px; }}
                    .header {{ text-align: center; margin-bottom: 30px; }}
                    .logo {{ font-size: 28px; font-weight: bold; background: linear-gradient(135deg, #7c3aed, #06b6d4); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }}
                    .content {{ background: #f8fafc; border-radius: 12px; padding: 30px; margin-bottom: 30px; }}
                    .button {{ display: inline-block; background: linear-gradient(135deg, #7c3aed, #06b6d4); color: white !important; text-decoration: none; padding: 14px 32px; border-radius: 8px; font-weight: 600; margin: 20px 0; }}
                    .footer {{ text-align: center; color: #64748b; font-size: 14px; }}
                    .warning {{ background: #fef3c7; border: 1px solid #f59e0b; border-radius: 8px; padding: 12px; margin-top: 20px; font-size: 13px; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <div class="logo">IAskan</div>
                        <p style="color: #64748b; margin-top: 5px;">Generative Engine Optimization</p>
                    </div>
                    <div class="content">
                        <h2 style="margin-top: 0;">Bienvenue {user_name or 'chez IAskan'} ! 👋</h2>
                        <p>Merci de vous être inscrit sur IAskan. Pour activer votre compte et accéder à votre essai gratuit, veuillez confirmer votre adresse email en cliquant sur le bouton ci-dessous :</p>
                        <div style="text-align: center;">
                            <a href="{verification_url}" class="button">Vérifier mon email</a>
                        </div>
                        <p style="font-size: 14px; color: #64748b;">Ou copiez ce lien dans votre navigateur :</p>
                        <p style="font-size: 12px; word-break: break-all; color: #7c3aed;">{verification_url}</p>
                        <div class="warning">
                            ⚠️ Ce lien expire dans <strong>24 heures</strong>. Si vous n'avez pas créé de compte, ignorez cet email.
                        </div>
                    </div>
                    <div class="footer">
                        <p>© 2026 IAskan - Optimisation pour les Moteurs de Réponse IA</p>
                        <p>Cet email a été envoyé à {email}</p>
                    </div>
                </div>
            </body>
            </html>
            """
        }
        
        await asyncio.to_thread(resend.Emails.send, params)
        logger.info(f"Verification email sent to {email}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send verification email: {e}")
        return False

async def verify_email_token(token: str) -> Dict[str, Any]:
    """Verify an email verification token"""
    # Find the token
    token_doc = await db.email_verification_tokens.find_one({"token": token}, {"_id": 0})
    
    if not token_doc:
        return {"success": False, "error": "Token invalide ou expiré"}
    
    if token_doc.get("used"):
        return {"success": False, "error": "Ce lien a déjà été utilisé"}
    
    # Check expiration
    expires_at = token_doc.get("expires_at")
    if isinstance(expires_at, str):
        expires_at = datetime.fromisoformat(expires_at)
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    
    if expires_at < datetime.now(timezone.utc):
        return {"success": False, "error": "Ce lien a expiré. Veuillez demander un nouveau lien de vérification."}
    
    # Mark token as used
    await db.email_verification_tokens.update_one(
        {"token": token},
        {"$set": {"used": True}}
    )
    
    # Update user's email_verified status
    await db.users.update_one(
        {"user_id": token_doc["user_id"]},
        {"$set": {"email_verified": True, "email_verified_at": datetime.now(timezone.utc).isoformat()}}
    )
    
    logger.info(f"Email verified for user {token_doc['user_id']}")
    
    return {
        "success": True,
        "user_id": token_doc["user_id"],
        "email": token_doc["email"]
    }

# ================== NOTIFICATION FUNCTIONS ==================

async def create_notification(
    user_id: str,
    notification_type: str,
    title: str,
    message: str,
    data: Dict[str, Any] = None
) -> str:
    """Create a notification for a user"""
    notification = Notification(
        user_id=user_id,
        type=notification_type,
        title=title,
        message=message,
        data=data or {}
    )
    
    doc = notification.model_dump()
    doc["created_at"] = doc["created_at"].isoformat()
    await db.notifications.insert_one(doc)
    
    logger.info(f"Notification created for user {user_id}: {notification_type}")
    return notification.notification_id

async def send_scan_complete_email(user_email: str, user_name: str, project_name: str, analysis_id: str, global_score: float) -> bool:
    """Send email notification when scan is complete"""
    if not RESEND_API_KEY:
        logger.warning("RESEND_API_KEY not configured, skipping scan complete email")
        return False
    
    frontend_url = os.environ.get('FRONTEND_URL', 'https://optimize-visibility.preview.emergentagent.com')
    analysis_url = f"{frontend_url}/analysis/{analysis_id}"
    
    # Score color
    score_color = "#10b981" if global_score >= 60 else "#f59e0b" if global_score >= 40 else "#ef4444"
    grade = "A" if global_score >= 80 else "B" if global_score >= 60 else "C" if global_score >= 40 else "D"
    
    try:
        params = {
            "from": "IAskan <noreply@resend.dev>",
            "to": [user_email],
            "subject": f"✅ Scan terminé - {project_name} ({int(global_score)}/100)",
            "html": f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="utf-8">
                <style>
                    body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; color: #1e293b; }}
                    .container {{ max-width: 600px; margin: 0 auto; padding: 40px 20px; }}
                    .header {{ text-align: center; margin-bottom: 30px; }}
                    .logo {{ font-size: 28px; font-weight: bold; background: linear-gradient(135deg, #7c3aed, #06b6d4); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }}
                    .score-box {{ background: linear-gradient(135deg, #f8fafc, #f1f5f9); border-radius: 16px; padding: 30px; text-align: center; margin: 20px 0; }}
                    .score {{ font-size: 48px; font-weight: bold; color: {score_color}; }}
                    .grade {{ display: inline-block; background: {score_color}; color: white; padding: 4px 12px; border-radius: 20px; font-size: 14px; font-weight: 600; margin-left: 10px; }}
                    .button {{ display: inline-block; background: linear-gradient(135deg, #7c3aed, #06b6d4); color: white !important; text-decoration: none; padding: 14px 32px; border-radius: 8px; font-weight: 600; margin: 20px 0; }}
                    .footer {{ text-align: center; color: #64748b; font-size: 14px; margin-top: 30px; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <div class="logo">IAskan</div>
                        <p style="color: #64748b; margin-top: 5px;">Generative Engine Optimization</p>
                    </div>
                    
                    <h2 style="text-align: center; margin-bottom: 10px;">Votre scan est terminé ! 🎉</h2>
                    <p style="text-align: center; color: #64748b;">Projet : <strong>{project_name}</strong></p>
                    
                    <div class="score-box">
                        <p style="margin: 0 0 10px 0; color: #64748b;">Score de Visibilité IA</p>
                        <span class="score">{int(global_score)}</span>
                        <span class="grade">Grade {grade}</span>
                        <p style="margin: 15px 0 0 0; font-size: 14px; color: #64748b;">/100</p>
                    </div>
                    
                    <div style="text-align: center;">
                        <a href="{analysis_url}" class="button">Voir le rapport complet</a>
                    </div>
                    
                    <p style="text-align: center; font-size: 14px; color: #64748b;">
                        Consultez les recommandations pour améliorer votre visibilité dans les réponses IA.
                    </p>
                    
                    <div class="footer">
                        <p>© 2026 IAskan - Optimisation pour les Moteurs de Réponse IA</p>
                        <p style="font-size: 12px;">Vous recevez cet email car vous avez lancé un scan sur IAskan.</p>
                    </div>
                </div>
            </body>
            </html>
            """
        }
        
        await asyncio.to_thread(resend.Emails.send, params)
        logger.info(f"Scan complete email sent to {user_email}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send scan complete email: {e}")
        return False


# ================== SCHEDULED SCANS FUNCTIONS ==================

def calculate_next_run(schedule: dict) -> str:
    """Calculate the next run time based on schedule configuration"""
    from datetime import datetime, timedelta
    import pytz
    
    try:
        tz = pytz.timezone(schedule.get("timezone", "Europe/Paris"))
    except:
        tz = pytz.timezone("Europe/Paris")
    
    now = datetime.now(tz)
    frequency = schedule.get("frequency", "weekly")
    hour = schedule.get("hour", 9)
    minute = schedule.get("minute", 0)
    
    if frequency == "daily":
        # Next occurrence at the specified time
        next_run = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        if next_run <= now:
            next_run += timedelta(days=1)
    
    elif frequency == "weekly":
        day_of_week = schedule.get("day_of_week", 0)  # 0=Monday
        days_ahead = day_of_week - now.weekday()
        if days_ahead < 0:
            days_ahead += 7
        next_run = now + timedelta(days=days_ahead)
        next_run = next_run.replace(hour=hour, minute=minute, second=0, microsecond=0)
        if next_run <= now:
            next_run += timedelta(weeks=1)
    
    elif frequency == "monthly":
        day_of_month = min(schedule.get("day_of_month", 1), 28)
        next_run = now.replace(day=day_of_month, hour=hour, minute=minute, second=0, microsecond=0)
        if next_run <= now:
            # Move to next month
            if now.month == 12:
                next_run = next_run.replace(year=now.year + 1, month=1)
            else:
                next_run = next_run.replace(month=now.month + 1)
    else:
        next_run = now + timedelta(days=7)
    
    return next_run.isoformat()


async def send_scheduled_report_email(
    user_email: str,
    user_name: str,
    project_name: str,
    analysis_id: str,
    global_score: float,
    grade: str,
    recipients: List[str] = None
):
    """Send scheduled scan report email with PDF attachment link"""
    if not RESEND_API_KEY:
        logger.warning("Resend API key not configured")
        return False
    
    try:
        score_color = "#10b981" if global_score >= 70 else "#f59e0b" if global_score >= 40 else "#ef4444"
        frontend_url = os.environ.get("FRONTEND_URL", "https://optimize-visibility.preview.emergentagent.com")
        analysis_url = f"{frontend_url}/analysis/{analysis_id}"
        
        # Build recipient list
        all_recipients = [user_email]
        if recipients:
            all_recipients.extend([r for r in recipients if r and r != user_email])
        
        params = {
            "from": "IAskan <noreply@resend.dev>",
            "to": all_recipients,
            "subject": f"📊 Rapport GEO programmé - {project_name} - Score: {int(global_score)}/100",
            "html": f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="utf-8">
                <style>
                    body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f8fafc; margin: 0; padding: 20px; }}
                    .container {{ max-width: 600px; margin: 0 auto; padding: 40px 20px; }}
                    .header {{ text-align: center; margin-bottom: 30px; }}
                    .logo {{ font-size: 28px; font-weight: bold; background: linear-gradient(135deg, #7c3aed, #06b6d4); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }}
                    .badge {{ display: inline-block; background: #7c3aed; color: white; padding: 4px 12px; border-radius: 20px; font-size: 12px; font-weight: 600; margin-bottom: 20px; }}
                    .score-box {{ background: linear-gradient(135deg, #f8fafc, #f1f5f9); border-radius: 16px; padding: 30px; text-align: center; margin: 20px 0; border: 1px solid #e2e8f0; }}
                    .score {{ font-size: 48px; font-weight: bold; color: {score_color}; }}
                    .grade {{ display: inline-block; background: {score_color}; color: white; padding: 4px 12px; border-radius: 20px; font-size: 14px; font-weight: 600; margin-left: 10px; }}
                    .button {{ display: inline-block; background: linear-gradient(135deg, #7c3aed, #06b6d4); color: white !important; text-decoration: none; padding: 14px 32px; border-radius: 8px; font-weight: 600; margin: 20px 0; }}
                    .button-secondary {{ display: inline-block; background: #f1f5f9; color: #475569 !important; text-decoration: none; padding: 12px 24px; border-radius: 8px; font-weight: 600; margin: 10px; border: 1px solid #e2e8f0; }}
                    .footer {{ text-align: center; color: #64748b; font-size: 14px; margin-top: 30px; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <div class="logo">IAskan</div>
                        <p style="color: #64748b; margin-top: 5px;">Generative Engine Optimization</p>
                    </div>
                    
                    <div style="text-align: center;">
                        <span class="badge">🗓️ Rapport Programmé</span>
                    </div>
                    
                    <h2 style="text-align: center; margin-bottom: 10px;">Votre audit GEO est prêt</h2>
                    <p style="text-align: center; color: #64748b;">Projet : <strong>{project_name}</strong></p>
                    
                    <div class="score-box">
                        <p style="margin: 0 0 10px 0; color: #64748b;">Score de Visibilité IA</p>
                        <span class="score">{int(global_score)}</span>
                        <span class="grade">Grade {grade}</span>
                        <p style="margin: 15px 0 0 0; font-size: 14px; color: #64748b;">/100</p>
                    </div>
                    
                    <div style="text-align: center;">
                        <a href="{analysis_url}" class="button">Voir le rapport complet</a>
                    </div>
                    
                    <div style="text-align: center;">
                        <a href="{analysis_url}?download=pdf" class="button-secondary">📥 Télécharger le PDF</a>
                    </div>
                    
                    <p style="text-align: center; font-size: 14px; color: #64748b; margin-top: 20px;">
                        Ce rapport a été généré automatiquement selon votre programmation.
                    </p>
                    
                    <div class="footer">
                        <p>© 2026 IAskan - Optimisation pour les Moteurs de Réponse IA</p>
                        <p style="font-size: 12px;">Vous recevez cet email car vous avez configuré un scan programmé sur IAskan.</p>
                    </div>
                </div>
            </body>
            </html>
            """
        }
        
        await asyncio.to_thread(resend.Emails.send, params)
        logger.info(f"Scheduled report email sent to {all_recipients}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send scheduled report email: {e}")
        return False


async def run_scheduled_scan(schedule: dict):
    """Execute a scheduled scan for a project"""
    try:
        project_id = schedule.get("project_id")
        user_id = schedule.get("user_id")
        
        # Get project
        project = await db.projects.find_one({"project_id": project_id, "user_id": user_id}, {"_id": 0})
        if not project:
            logger.error(f"Scheduled scan: Project {project_id} not found")
            return False
        
        # Get user subscription
        subscription = await db.subscriptions.find_one({"user_id": user_id}, {"_id": 0})
        if not subscription:
            logger.error(f"Scheduled scan: No subscription for user {user_id}")
            return False
        
        plan = subscription.get("plan", "free")
        
        # Only Pro and Business can use scheduled scans
        if plan not in ["pro", "business"]:
            logger.warning(f"Scheduled scan: User {user_id} has {plan} plan, scheduled scans require Pro or Business")
            return False
        
        # Check quota
        scans_used = subscription.get("scans_used", 0)
        plan_config = SUBSCRIPTION_PLANS.get(plan, SUBSCRIPTION_PLANS["pro"])
        scans_limit = plan_config.get("scans_limit", 50)
        
        if scans_used >= scans_limit:
            logger.warning(f"Scheduled scan: User {user_id} has reached scan limit")
            return False
        
        # Create analysis
        analysis_id = f"ana_{uuid.uuid4().hex[:12]}"
        analysis_doc = {
            "analysis_id": analysis_id,
            "project_id": project_id,
            "user_id": user_id,
            "status": "pending",
            "scheduled": True,
            "schedule_id": schedule.get("schedule_id"),
            "created_at": datetime.now(timezone.utc).isoformat(),
            "current_phase": "initializing"
        }
        await db.analyses.insert_one(analysis_doc)
        
        # Run analysis in background
        asyncio.create_task(run_analysis_v2(analysis_id, project, plan_config))
        
        # Update schedule
        await db.scan_schedules.update_one(
            {"schedule_id": schedule.get("schedule_id")},
            {"$set": {
                "last_run": datetime.now(timezone.utc).isoformat(),
                "next_run": calculate_next_run(schedule),
                "updated_at": datetime.now(timezone.utc).isoformat()
            }}
        )
        
        logger.info(f"Scheduled scan started: {analysis_id} for project {project_id}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to run scheduled scan: {e}")
        return False


async def check_scheduled_scans():
    """Background task to check and run due scheduled scans"""
    while True:
        try:
            now = datetime.now(timezone.utc)
            
            if USE_POSTGRES:
                # Use PostgreSQL for scheduled scans
                from app.db import get_db_session, ScheduleService
                from sqlalchemy import select
                from app.db.models import ScanSchedule
                
                async with get_db_session() as session:
                    if session:
                        result = await session.execute(
                            select(ScanSchedule).where(
                                ScanSchedule.enabled == True,
                                ScanSchedule.next_run <= now
                            )
                        )
                        due_schedules = [ScheduleService.to_dict(s) for s in result.scalars().all()]
                        for schedule in due_schedules:
                            await run_scheduled_scan(schedule)
            elif db is not None:
                # Legacy MongoDB fallback
                due_schedules = await db.scan_schedules.find({
                    "enabled": True,
                    "next_run": {"$lte": now.isoformat()}
                }, {"_id": 0}).to_list(100)
                
                for schedule in due_schedules:
                    await run_scheduled_scan(schedule)
            
        except Exception as e:
            logger.error(f"Error checking scheduled scans: {e}")
        
        # Check every 5 minutes
        await asyncio.sleep(300)


async def get_session_from_token(token: str) -> Optional[dict]:
    """Validate session token and return session data"""
    session = await db.user_sessions.find_one({"session_token": token}, {"_id": 0})
    if not session:
        return None
    
    expires_at = session.get("expires_at")
    if isinstance(expires_at, str):
        expires_at = datetime.fromisoformat(expires_at)
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    
    if expires_at < datetime.now(timezone.utc):
        return None
    
    return session

async def get_current_user(request: Request) -> dict:
    """Get current user from session token in cookies or header"""
    # Try cookie first
    token = request.cookies.get("session_token")
    
    # Fallback to Authorization header
    if not token:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
    
    if not token:
        raise HTTPException(status_code=401, detail="Non authentifié")
    
    session = await get_session_from_token(token)
    if not session:
        raise HTTPException(status_code=401, detail="Session expirée")
    
    user = await db.users.find_one({"user_id": session["user_id"]}, {"_id": 0})
    if not user:
        raise HTTPException(status_code=401, detail="Utilisateur non trouvé")
    
    return user

# ================== IAskan Verified GEO Protocol™ ENGINE ==================
# Méthodologie certifiée multi-IA, multi-requêtes, multi-analyses

# Query type distribution for realistic simulation
QUERY_TYPE_DISTRIBUTION = {
    "transactional": 0.30,    # 30% - "acheter", "prix", "commander"
    "comparative": 0.25,       # 25% - "vs", "comparaison", "meilleur"
    "informational": 0.20,     # 20% - "qu'est-ce que", "comment"
    "local": 0.15,             # 15% - "près de moi", "en France"
    "exploratory": 0.10        # 10% - "recommandations", "suggestions"
}

# Query templates by type (French market focused)
QUERY_TEMPLATES = {
    "transactional": [
        "Acheter {keyword} - meilleur prix",
        "Commander {keyword} en ligne",
        "Où acheter {keyword} pas cher ?",
        "Prix {keyword} - comparatif",
        "Devis {keyword} professionnel"
    ],
    "comparative": [
        "Quel est le meilleur {keyword} ?",
        "{keyword} : comparaison des solutions",
        "Top 10 {keyword} en {year}",
        "Alternative à {competitor} pour {keyword}",
        "{brand} vs {competitor} : avis"
    ],
    "informational": [
        "Qu'est-ce que {keyword} ?",
        "Comment choisir un bon {keyword} ?",
        "Guide complet {keyword}",
        "Avis sur {keyword} - que vaut-il ?",
        "Avantages et inconvénients {keyword}"
    ],
    "local": [
        "Meilleur {keyword} en France",
        "{keyword} entreprise française",
        "Solution {keyword} européenne",
        "{keyword} près de chez moi",
        "Fournisseur {keyword} local"
    ],
    "exploratory": [
        "Je cherche un {keyword}, que recommandez-vous ?",
        "Suggestions pour {keyword}",
        "Quelle solution {keyword} pour mon entreprise ?",
        "Besoin de conseils sur {keyword}",
        "Recommandations {keyword} B2B"
    ]
}

# Query variations for multi-run stability
QUERY_VARIATIONS = {
    "short": lambda q: q.split(" - ")[0] if " - " in q else q[:50],
    "long": lambda q: f"{q} - avis détaillé et recommandations professionnelles",
    "conversational": lambda q: f"Salut ! {q} J'aimerais avoir ton avis.",
    "question": lambda q: f"{q}" if q.endswith("?") else f"{q} ?",
    "recommendation": lambda q: f"Peux-tu me recommander : {q}"
}

# ================== BRAND VARIANTS DETECTION ==================

def generate_brand_variants(brand_name: str, products: List[str] = None) -> List[str]:
    """
    Generate brand name variants including common typos, abbreviations, and products
    """
    variants = [brand_name.lower()]
    brand_lower = brand_name.lower()
    
    # Common typo patterns
    typo_variants = []
    
    # Missing letters
    for i in range(len(brand_lower)):
        typo_variants.append(brand_lower[:i] + brand_lower[i+1:])
    
    # Double letters
    for i in range(len(brand_lower)):
        typo_variants.append(brand_lower[:i] + brand_lower[i] + brand_lower[i:])
    
    # Adjacent key swaps (common typos)
    for i in range(len(brand_lower) - 1):
        swapped = brand_lower[:i] + brand_lower[i+1] + brand_lower[i] + brand_lower[i+2:]
        typo_variants.append(swapped)
    
    # Add only valid variants (length > 2, not same as original)
    for v in typo_variants:
        if len(v) > 2 and v != brand_lower and v not in variants:
            variants.append(v)
    
    # Abbreviations (first letters of each word if multi-word brand)
    words = brand_name.split()
    if len(words) > 1:
        abbreviation = "".join(w[0].lower() for w in words)
        if len(abbreviation) > 1:
            variants.append(abbreviation)
    
    # Without spaces/dashes
    variants.append(brand_lower.replace(" ", ""))
    variants.append(brand_lower.replace("-", ""))
    variants.append(brand_lower.replace("_", ""))
    
    # With common domain extensions
    variants.append(f"{brand_lower}.com")
    variants.append(f"{brand_lower}.fr")
    variants.append(f"www.{brand_lower}")
    
    # Product names as variants
    if products:
        for product in products[:10]:  # Limit to 10 products
            variants.append(product.lower())
    
    # Remove duplicates and empty strings
    variants = list(set(v for v in variants if v and len(v) > 1))
    
    return variants[:50]  # Limit total variants


def detect_brand_mentions_advanced(response_text: str, brand_name: str, variants: List[str]) -> Dict[str, Any]:
    """
    Advanced brand mention detection including variants, products, and typos
    """
    response_lower = response_text.lower()
    brand_lower = brand_name.lower()
    
    # Primary brand detection
    primary_mentioned = brand_lower in response_lower
    primary_count = response_lower.count(brand_lower)
    primary_positions = []
    
    if primary_mentioned:
        start = 0
        while True:
            pos = response_lower.find(brand_lower, start)
            if pos == -1:
                break
            primary_positions.append(pos)
            start = pos + 1
    
    # Variant detection
    variant_mentions = {}
    total_variant_mentions = 0
    
    for variant in variants:
        if variant != brand_lower and variant in response_lower:
            count = response_lower.count(variant)
            variant_mentions[variant] = count
            total_variant_mentions += count
    
    # Calculate overall mention metrics
    total_mentions = primary_count + total_variant_mentions
    first_position = min(primary_positions) if primary_positions else -1
    
    # Determine mention quality
    mention_quality = "absent"
    if total_mentions > 0:
        if primary_mentioned:
            if total_mentions >= 3:
                mention_quality = "strong"
            elif total_mentions >= 2:
                mention_quality = "moderate"
            else:
                mention_quality = "weak"
        else:
            mention_quality = "variant_only"
    
    return {
        "primary_mentioned": primary_mentioned,
        "primary_count": primary_count,
        "primary_positions": primary_positions[:5],  # First 5 positions
        "variant_mentions": variant_mentions,
        "total_variant_mentions": total_variant_mentions,
        "total_mentions": total_mentions,
        "first_position": first_position,
        "mention_quality": mention_quality,
        "variants_found": list(variant_mentions.keys())
    }


# ================== SITE ENRICHMENT ANALYSIS ==================

async def analyze_site_enrichment(website_url: str) -> Dict[str, Any]:
    """
    Analyze website for GEO-relevant enrichment signals:
    - Schema.org structured data
    - FAQ presence
    - About/Team pages
    - Trust signals (contact, legal, certifications)
    """
    enrichment = {
        "schema_org": {"detected": False, "types": []},
        "faq_presence": False,
        "about_page": False,
        "contact_info": False,
        "trust_signals": [],
        "key_pages": [],
        "score": 0,
        "recommendations": []
    }
    
    try:
        # Clean URL
        if not website_url.startswith(('http://', 'https://')):
            website_url = f"https://{website_url}"
        
        from urllib.parse import urlparse
        parsed = urlparse(website_url)
        base_url = f"{parsed.scheme}://{parsed.netloc}"
        
        async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
            # Fetch main page
            response = await client.get(website_url)
            html_content = response.text.lower()
            
            # 1. Schema.org detection
            schema_types = []
            if "application/ld+json" in html_content:
                enrichment["schema_org"]["detected"] = True
                # Detect common schema types
                schema_patterns = [
                    ("Organization", "organization"),
                    ("LocalBusiness", "localbusiness"),
                    ("Product", "product"),
                    ("FAQPage", "faqpage"),
                    ("Article", "article"),
                    ("WebSite", "website"),
                    ("BreadcrumbList", "breadcrumblist"),
                    ("Review", "review"),
                    ("AggregateRating", "aggregaterating")
                ]
                for name, pattern in schema_patterns:
                    if pattern in html_content:
                        schema_types.append(name)
                enrichment["schema_org"]["types"] = schema_types
            
            # 2. FAQ detection
            faq_indicators = ["faq", "questions fréquentes", "frequently asked", "f.a.q", "questions-réponses"]
            enrichment["faq_presence"] = any(ind in html_content for ind in faq_indicators)
            
            # 3. About page detection
            about_indicators = ["à propos", "about us", "qui sommes-nous", "notre histoire", "notre équipe", "about-us"]
            enrichment["about_page"] = any(ind in html_content for ind in about_indicators)
            
            # 4. Contact info detection
            contact_indicators = ["contact", "email", "@", "téléphone", "phone", "adresse", "address"]
            enrichment["contact_info"] = any(ind in html_content for ind in contact_indicators)
            
            # 5. Trust signals
            trust_patterns = [
                ("ssl_secure", "https://" in website_url),
                ("privacy_policy", any(p in html_content for p in ["politique de confidentialité", "privacy policy", "rgpd", "gdpr"])),
                ("legal_mentions", any(p in html_content for p in ["mentions légales", "legal notice", "terms"])),
                ("certifications", any(p in html_content for p in ["certifié", "certified", "iso", "label", "agrément"])),
                ("reviews", any(p in html_content for p in ["avis", "review", "témoignage", "testimonial"])),
                ("social_proof", any(p in html_content for p in ["client", "partenaire", "partner", "they trust us"]))
            ]
            
            for signal_name, detected in trust_patterns:
                if detected:
                    enrichment["trust_signals"].append(signal_name)
            
            # 6. Key pages detection
            key_page_patterns = [
                ("pricing", ["tarif", "pricing", "prix", "plans"]),
                ("features", ["fonctionnalités", "features", "solutions"]),
                ("blog", ["blog", "actualités", "news", "articles"]),
                ("case_studies", ["cas client", "case study", "études de cas", "success story"]),
                ("documentation", ["documentation", "docs", "guide", "support"])
            ]
            
            for page_type, patterns in key_page_patterns:
                if any(p in html_content for p in patterns):
                    enrichment["key_pages"].append(page_type)
            
            # Calculate enrichment score
            score = 0
            if enrichment["schema_org"]["detected"]:
                score += 25 + len(enrichment["schema_org"]["types"]) * 3
            if enrichment["faq_presence"]:
                score += 15
            if enrichment["about_page"]:
                score += 10
            if enrichment["contact_info"]:
                score += 10
            score += len(enrichment["trust_signals"]) * 5
            score += len(enrichment["key_pages"]) * 3
            
            enrichment["score"] = min(100, score)
            
            # Generate recommendations
            if not enrichment["schema_org"]["detected"]:
                enrichment["recommendations"].append({
                    "priority": "high",
                    "action": "Ajouter des données structurées Schema.org",
                    "impact": "Les IAs utilisent les données structurées pour mieux comprendre votre contenu"
                })
            elif "FAQPage" not in enrichment["schema_org"]["types"]:
                enrichment["recommendations"].append({
                    "priority": "medium",
                    "action": "Ajouter un Schema FAQPage",
                    "impact": "Améliore la citabilité dans les réponses de type Q&A"
                })
            
            if not enrichment["faq_presence"]:
                enrichment["recommendations"].append({
                    "priority": "high",
                    "action": "Créer une page FAQ complète",
                    "impact": "Les FAQs sont fréquemment citées par les IAs"
                })
            
            if not enrichment["about_page"]:
                enrichment["recommendations"].append({
                    "priority": "medium",
                    "action": "Enrichir la page 'À propos'",
                    "impact": "Renforce l'E-E-A-T et la crédibilité"
                })
            
            if "case_studies" not in enrichment["key_pages"]:
                enrichment["recommendations"].append({
                    "priority": "medium",
                    "action": "Ajouter des études de cas",
                    "impact": "Preuves concrètes citées par les IAs"
                })
                
    except Exception as e:
        logger.error(f"Error analyzing site enrichment: {e}")
        enrichment["error"] = str(e)
    
    return enrichment


# ================== HISTORICAL DIFF ANALYSIS ==================

async def calculate_scan_diff(current_analysis: dict, previous_analysis: dict) -> Dict[str, Any]:
    """
    Calculate differences between current and previous scan for trend analysis
    """
    diff = {
        "has_previous": previous_analysis is not None,
        "days_between_scans": 0,
        "score_evolution": {},
        "rate_evolution": {},
        "ai_evolution": {},
        "stability_evolution": {},
        "trends": [],
        "improvements": [],
        "regressions": []
    }
    
    if not previous_analysis:
        return diff
    
    # Calculate days between scans
    try:
        current_date = datetime.fromisoformat(current_analysis.get("created_at", "").replace("Z", "+00:00"))
        prev_date = datetime.fromisoformat(previous_analysis.get("created_at", "").replace("Z", "+00:00"))
        diff["days_between_scans"] = (current_date - prev_date).days
    except:
        diff["days_between_scans"] = 0
    
    # Score evolution
    current_score = current_analysis.get("global_score", 0)
    prev_score = previous_analysis.get("global_score", 0)
    score_change = current_score - prev_score
    
    diff["score_evolution"] = {
        "current": round(current_score, 1),
        "previous": round(prev_score, 1),
        "change": round(score_change, 1),
        "change_percent": round((score_change / prev_score * 100) if prev_score > 0 else 0, 1),
        "direction": "up" if score_change > 0 else "down" if score_change < 0 else "stable"
    }
    
    # R.A.T.E. evolution
    current_rate = current_analysis.get("rate_score", {})
    prev_rate = previous_analysis.get("rate_score", {})
    
    for metric in ["relevance", "authority", "truthfulness", "endorsement"]:
        curr_val = current_rate.get(metric, 0)
        prev_val = prev_rate.get(metric, 0)
        change = curr_val - prev_val
        
        diff["rate_evolution"][metric] = {
            "current": round(curr_val, 1),
            "previous": round(prev_val, 1),
            "change": round(change, 1),
            "direction": "up" if change > 0 else "down" if change < 0 else "stable"
        }
        
        # Track significant changes
        if change >= 5:
            diff["improvements"].append(f"{metric.capitalize()} +{round(change, 1)}%")
        elif change <= -5:
            diff["regressions"].append(f"{metric.capitalize()} {round(change, 1)}%")
    
    # AI-specific evolution
    current_ai = current_analysis.get("ai_scores", {})
    prev_ai = previous_analysis.get("ai_scores", {})
    
    for ai in ["chatgpt", "claude", "gemini", "perplexity"]:
        curr_val = current_ai.get(ai, 0)
        prev_val = prev_ai.get(ai, 0)
        change = curr_val - prev_val
        
        diff["ai_evolution"][ai] = {
            "current": round(curr_val, 1),
            "previous": round(prev_val, 1),
            "change": round(change, 1),
            "direction": "up" if change > 0 else "down" if change < 0 else "stable"
        }
        
        if change >= 10:
            diff["improvements"].append(f"{ai.capitalize()} +{round(change, 1)} pts")
        elif change <= -10:
            diff["regressions"].append(f"{ai.capitalize()} {round(change, 1)} pts")
    
    # Stability evolution
    current_indices = current_analysis.get("indices", {})
    prev_indices = previous_analysis.get("indices", {})
    
    stability_curr = current_indices.get("stability_index", 0)
    stability_prev = prev_indices.get("stability_index", 0)
    stability_change = stability_curr - stability_prev
    
    diff["stability_evolution"] = {
        "current": round(stability_curr, 1),
        "previous": round(stability_prev, 1),
        "change": round(stability_change, 1),
        "direction": "up" if stability_change > 0 else "down" if stability_change < 0 else "stable"
    }
    
    # Generate trend insights
    if diff["score_evolution"]["direction"] == "up":
        if diff["score_evolution"]["change"] >= 10:
            diff["trends"].append({"type": "positive", "message": f"Forte progression du score (+{diff['score_evolution']['change']})"})
        else:
            diff["trends"].append({"type": "positive", "message": "Score en légère amélioration"})
    elif diff["score_evolution"]["direction"] == "down":
        if abs(diff["score_evolution"]["change"]) >= 10:
            diff["trends"].append({"type": "negative", "message": f"Baisse significative du score ({diff['score_evolution']['change']})"})
        else:
            diff["trends"].append({"type": "warning", "message": "Score en légère baisse"})
    else:
        diff["trends"].append({"type": "neutral", "message": "Score stable depuis le dernier scan"})
    
    # Identify best/worst performing area
    rate_changes = {k: v["change"] for k, v in diff["rate_evolution"].items()}
    if rate_changes:
        best = max(rate_changes, key=rate_changes.get)
        worst = min(rate_changes, key=rate_changes.get)
        
        if rate_changes[best] > 0:
            diff["trends"].append({"type": "positive", "message": f"Meilleure progression: {best.capitalize()}"})
        if rate_changes[worst] < 0:
            diff["trends"].append({"type": "negative", "message": f"À surveiller: {worst.capitalize()}"})
    
    return diff

async def query_ai_engine_v2(query_text: str, brand_name: str, competitors: List[str], ai_type: str, run_id: int = 1) -> Dict[str, Any]:
    """
    IAskan Verified GEO Protocol™ - Advanced AI Query Engine
    Performs semantic analysis across 4 layers: Presence, Role, Credibility, Conversion
    """
    try:
        session_id = f"geo_v2_{uuid.uuid4().hex[:8]}_{run_id}"
        
        system_message = """Tu es un assistant intelligent qui répond aux questions des utilisateurs de manière naturelle, 
objective et informative. Réponds en mentionnant les marques, entreprises ou solutions pertinentes si applicable. 
Sois précis et factuel dans tes recommandations."""
        
        chat = LlmChat(
            api_key=EMERGENT_LLM_KEY,
            session_id=session_id,
            system_message=system_message
        )
        
        # Configure model based on AI type
        if ai_type == "chatgpt":
            chat.with_model("openai", "gpt-5.2")
        elif ai_type == "claude":
            chat.with_model("anthropic", "claude-sonnet-4-5-20250929")
        elif ai_type == "gemini":
            chat.with_model("gemini", "gemini-3-flash-preview")
        elif ai_type == "perplexity":
            chat.with_model("openai", "gpt-4o")
        else:
            chat.with_model("openai", "gpt-5.2")
        
        user_message = UserMessage(text=query_text)
        
        # Run LLM call in thread pool to avoid blocking the event loop
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            llm_executor, 
            lambda: asyncio.run(chat.send_message(user_message))
        )
        
        response_text = response if isinstance(response, str) else str(response)
        response_lower = response_text.lower()
        brand_lower = brand_name.lower()
        
        # ===== LAYER 1: PRESENCE ANALYSIS =====
        brand_mentioned = brand_lower in response_lower
        mention_count = response_lower.count(brand_lower)
        first_position = response_lower.find(brand_lower) if brand_mentioned else -1
        response_length = len(response_lower)
        position_ratio = (first_position / response_length) if brand_mentioned and response_length > 0 else 1.0
        
        # ===== LAYER 2: ROLE ANALYSIS =====
        role = "absent"
        role_score = 0.0
        
        if brand_mentioned:
            # Analyze surrounding context for role determination
            context_start = max(0, first_position - 100)
            context_end = min(response_length, first_position + 200)
            context = response_lower[context_start:context_end]
            
            # Top recommendation indicators
            top_indicators = ["meilleur", "leader", "recommande", "premier", "numéro 1", "#1", "top", "incontournable", "référence"]
            shortlist_indicators = ["également", "aussi", "autre option", "alternative", "parmi les", "fait partie"]
            comparison_indicators = ["comparé", "versus", "vs", "face à", "contrairement", "différent"]
            negative_indicators = ["éviter", "déconseille", "problème", "inconvénient", "moins bon", "attention"]
            
            has_top = any(ind in context for ind in top_indicators)
            has_shortlist = any(ind in context for ind in shortlist_indicators)
            has_comparison = any(ind in context for ind in comparison_indicators)
            has_negative = any(ind in context for ind in negative_indicators)
            
            if has_negative:
                role = "discouraged"
                role_score = 0.1
            elif position_ratio < 0.15 and has_top:
                role = "top_recommendation"
                role_score = 1.0
            elif position_ratio < 0.30 and (has_top or has_shortlist):
                role = "shortlist"
                role_score = 0.85
            elif position_ratio < 0.50 or has_shortlist:
                role = "comparison"
                role_score = 0.60
            elif has_comparison:
                role = "mentioned"
                role_score = 0.40
            else:
                role = "cited"
                role_score = 0.25
        
        # ===== LAYER 3: CREDIBILITY ANALYSIS =====
        credibility_score = 50.0  # Base score
        credibility_factors = []
        
        # Check for credibility signals around brand mention
        if brand_mentioned:
            credibility_signals = {
                "numbers": any(char.isdigit() for char in response_text),
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
            
            credibility_score = min(100, credibility_score)
        
        # ===== LAYER 4: CONVERSION ANALYSIS =====
        conversion_score = 0.0
        conversion_signals = []
        
        if brand_mentioned:
            # Check for conversion-oriented language
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
            
            conversion_score = min(100, conversion_score)
        
        # ===== ANTI-HALLUCINATION CHECK =====
        hallucination_flags = []
        hallucination_penalty = 0
        
        # Check for inconsistencies
        if brand_mentioned:
            # Check if brand is mentioned but with conflicting info
            if "n'existe pas" in response_lower or "ne connais pas" in response_lower:
                hallucination_flags.append("existence_doubt")
                hallucination_penalty += 30
            
            # Check for contradictions
            if ("meilleur" in response_lower and "éviter" in response_lower):
                hallucination_flags.append("contradiction")
                hallucination_penalty += 20
        
        # ===== COMPETITOR ANALYSIS =====
        competitor_positions = {}
        for comp in competitors[:5]:  # Limit to top 5 competitors
            comp_lower = comp.lower()
            if comp_lower in response_lower:
                comp_pos = response_lower.find(comp_lower)
                comp_ratio = comp_pos / response_length if response_length > 0 else 1
                competitor_positions[comp] = {
                    "mentioned": True,
                    "position_ratio": round(comp_ratio, 3),
                    "before_brand": comp_pos < first_position if brand_mentioned else True
                }
            else:
                competitor_positions[comp] = {"mentioned": False, "position_ratio": 1.0, "before_brand": False}
        
        return {
            "ai_type": ai_type,
            "run_id": run_id,
            "query_text": query_text[:200],
            "response_excerpt": response_text[:500],
            "response_length": response_length,
            # Layer 1: Presence
            "brand_mentioned": brand_mentioned,
            "mention_count": mention_count,
            "first_position": first_position,
            "position_ratio": round(position_ratio, 3),
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
            "competitor_analysis": competitor_positions,
            # Metadata
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


def generate_queries_multi_dimension(brand_name: str, keywords: List[str], competitors: List[str], num_queries: int = 15) -> List[Dict[str, Any]]:
    """
    IAskan Verified GEO Protocol™ - Multi-dimension Query Generator
    Distributes queries across: 30% transactional, 25% comparative, 20% informational, 15% local, 10% exploratory
    """
    import random
    from datetime import datetime
    
    queries = []
    current_year = datetime.now().year
    
    # Calculate queries per type based on distribution
    type_counts = {
        qtype: max(1, int(num_queries * ratio))
        for qtype, ratio in QUERY_TYPE_DISTRIBUTION.items()
    }
    
    # Ensure we hit the target number
    total = sum(type_counts.values())
    if total < num_queries:
        type_counts["comparative"] += num_queries - total
    
    for query_type, count in type_counts.items():
        templates = QUERY_TEMPLATES.get(query_type, QUERY_TEMPLATES["informational"])
        
        for i in range(count):
            # Select template
            template = random.choice(templates)
            
            # Fill in template variables
            keyword = random.choice(keywords) if keywords else "solution"
            competitor = random.choice(competitors) if competitors else "concurrent"
            
            query_text = template.format(
                keyword=keyword,
                brand=brand_name,
                competitor=competitor,
                year=current_year
            )
            
            queries.append({
                "text": query_text,
                "type": query_type,
                "keyword": keyword,
                "intent": query_type,
                "variations": []
            })
    
    # Generate variations for each query (for multi-run stability)
    for query in queries:
        base_text = query["text"]
        query["variations"] = [
            QUERY_VARIATIONS["short"](base_text),
            QUERY_VARIATIONS["conversational"](base_text),
            QUERY_VARIATIONS["question"](base_text)
        ]
    
    return queries[:num_queries]


def calculate_stability_index(multi_run_results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    IAskan Verified GEO Protocol™ - Stability Index™
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
        role_variance = len(set(roles)) / len(roles)  # 1.0 = all different, lower = more consistent
        
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


def calculate_advanced_indices(all_responses: List[Dict[str, Any]], brand_name: str, competitors: List[str]) -> Dict[str, Any]:
    """
    IAskan Verified GEO Protocol™ - Advanced Indices Calculator
    Calculates: Stability Index™, Dominance Index™, Trust Gap™, Opportunity Score™
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
    
    # ===== DOMINANCE INDEX™ =====
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
    
    # ===== TRUST GAP™ =====
    # Measures credibility gap vs competitors
    brand_credibility = [r.get("credibility_score", 0) for r in valid_responses if r.get("brand_mentioned")]
    avg_brand_credibility = sum(brand_credibility) / len(brand_credibility) if brand_credibility else 0
    
    # Estimate competitor credibility (simplified - based on mention frequency)
    competitor_mentions = 0
    for resp in valid_responses:
        comp_analysis = resp.get("competitor_analysis", {})
        competitor_mentions += sum(1 for c, data in comp_analysis.items() if data.get("mentioned", False))
    
    avg_competitor_presence = (competitor_mentions / (len(valid_responses) * len(competitors))) * 100 if competitors else 0
    indices["trust_gap"] = round(avg_brand_credibility - avg_competitor_presence, 1)
    
    # ===== OPPORTUNITY SCORE™ =====
    # Measures potential for improvement
    low_score_queries = sum(1 for r in valid_responses if r.get("role_score", 0) < 0.5)
    absent_queries = sum(1 for r in valid_responses if r.get("role") == "absent")
    
    # High opportunity = many queries where brand is absent or low-ranked
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


def calculate_rate_score_v2(all_responses: List[Dict[str, Any]], stability_data: Dict[str, Any]) -> Dict[str, float]:
    """
    IAskan Verified GEO Protocol™ - R.A.T.E.™ Score Calculator (Enhanced)
    Weights: Relevance 30%, Authority 25%, Truthfulness 20%, Endorsement 25%
    """
    if not all_responses:
        return {"relevance": 0, "authority": 0, "truthfulness": 0, "endorsement": 0, "total": 0, "grade": "F"}
    
    valid_responses = [r for r in all_responses if r.get("role") != "error"]
    if not valid_responses:
        return {"relevance": 0, "authority": 0, "truthfulness": 0, "endorsement": 0, "total": 0, "grade": "F"}
    
    # ===== RELEVANCE (30%) =====
    # Based on mention rate and position quality
    mentioned = sum(1 for r in valid_responses if r.get("brand_mentioned", False))
    mention_rate = (mentioned / len(valid_responses)) * 100
    
    # Position quality bonus
    position_scores = [1 - r.get("position_ratio", 1) for r in valid_responses if r.get("brand_mentioned")]
    avg_position_score = (sum(position_scores) / len(position_scores)) * 100 if position_scores else 0
    
    relevance = (mention_rate * 0.6) + (avg_position_score * 0.4)
    
    # ===== AUTHORITY (25%) =====
    # Based on role weight and credibility factors
    role_scores = [r.get("role_score", 0) for r in valid_responses]
    avg_role = (sum(role_scores) / len(role_scores)) * 100
    
    credibility_scores = [r.get("credibility_score", 50) for r in valid_responses if r.get("brand_mentioned")]
    avg_credibility = sum(credibility_scores) / len(credibility_scores) if credibility_scores else 50
    
    authority = (avg_role * 0.5) + (avg_credibility * 0.5)
    
    # ===== TRUTHFULNESS (20%) =====
    # Based on credibility analysis and anti-hallucination checks
    base_truthfulness = 85.0
    
    # Penalty for hallucinations
    hallucination_penalties = sum(r.get("hallucination_penalty", 0) for r in valid_responses)
    truthfulness = max(0, base_truthfulness - (hallucination_penalties / len(valid_responses)))
    
    # Bonus for credibility factors
    all_credibility_factors = []
    for r in valid_responses:
        all_credibility_factors.extend(r.get("credibility_factors", []))
    
    unique_factors = len(set(all_credibility_factors))
    truthfulness = min(100, truthfulness + (unique_factors * 2))
    
    # ===== ENDORSEMENT (25%) =====
    # Based on top recommendations and conversion potential
    top_recs = sum(1 for r in valid_responses if r.get("role") == "top_recommendation")
    shortlists = sum(1 for r in valid_responses if r.get("role") == "shortlist")
    
    endorsement_base = ((top_recs * 2 + shortlists) / len(valid_responses)) * 100
    
    # Conversion score bonus
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


def generate_recommendations_v2(
    rate_score: Dict[str, float],
    ai_scores: Dict[str, float],
    indices: Dict[str, Any],
    stability_data: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """
    IAskan Verified GEO Protocol™ - Advanced Recommendations Generator
    Generates actionable, prioritized recommendations based on comprehensive analysis
    """
    recommendations = []
    
    # Priority 1: Stability issues
    if stability_data.get("stability_score", 100) < 60:
        recommendations.append({
            "priority": "critical",
            "category": "stability",
            "title": "Améliorer la cohérence des réponses IA",
            "description": f"Votre Stability Index™ est de {stability_data.get('stability_score', 0)}%. Les IAs donnent des réponses incohérentes sur votre marque. Standardisez votre présence en ligne avec des informations uniformes.",
            "impact": "critique",
            "effort": "moyen",
            "metrics_impacted": ["stability_index", "trustworthiness"]
        })
    
    # Priority 2: Low visibility
    if rate_score.get("relevance", 0) < 40:
        recommendations.append({
            "priority": "high",
            "category": "visibility",
            "title": "Augmenter la visibilité de marque",
            "description": f"Score de pertinence: {rate_score.get('relevance', 0)}%. Votre marque n'apparaît pas suffisamment dans les réponses IA. Créez du contenu optimisé GEO avec des cas d'usage concrets et des témoignages clients.",
            "impact": "élevé",
            "effort": "moyen",
            "metrics_impacted": ["relevance", "mention_rate"]
        })
    
    # Priority 3: Low authority
    if rate_score.get("authority", 0) < 50:
        recommendations.append({
            "priority": "high",
            "category": "authority",
            "title": "Renforcer l'autorité de marque",
            "description": f"Score d'autorité: {rate_score.get('authority', 0)}%. Ajoutez des signaux de crédibilité: études de cas chiffrées, certifications, mentions presse, témoignages vérifiables.",
            "impact": "élevé",
            "effort": "faible",
            "metrics_impacted": ["authority", "credibility"]
        })
    
    # Priority 4: Low endorsement
    if rate_score.get("endorsement", 0) < 35:
        recommendations.append({
            "priority": "high",
            "category": "endorsement",
            "title": "Optimiser pour les recommandations",
            "description": f"Score d'endorsement: {rate_score.get('endorsement', 0)}%. Positionnez votre marque comme référence en créant du contenu comparatif objectif et des guides de décision.",
            "impact": "élevé",
            "effort": "moyen",
            "metrics_impacted": ["endorsement", "conversion"]
        })
    
    # Priority 5: Dominance issues
    if indices.get("dominance_index", 0) < 50:
        recommendations.append({
            "priority": "medium",
            "category": "competitive",
            "title": "Améliorer le positionnement concurrentiel",
            "description": f"Dominance Index™: {indices.get('dominance_index', 0)}%. Vos concurrents apparaissent souvent avant vous. Renforcez votre présence sur les requêtes clés avec du contenu ciblé.",
            "impact": "moyen",
            "effort": "moyen",
            "metrics_impacted": ["dominance_index", "ranking"]
        })
    
    # Priority 6: Trust gap
    trust_gap = indices.get("trust_gap", 0)
    if trust_gap < 0:
        recommendations.append({
            "priority": "medium",
            "category": "trust",
            "title": "Combler l'écart de confiance",
            "description": f"Trust Gap™: {trust_gap}. Vos concurrents sont perçus comme plus fiables. Ajoutez des preuves sociales et des garanties pour renforcer la confiance.",
            "impact": "moyen",
            "effort": "faible",
            "metrics_impacted": ["trust_gap", "credibility"]
        })
    
    # AI-specific recommendations
    for ai, score in ai_scores.items():
        if score < 30:
            ai_names = {"chatgpt": "ChatGPT", "claude": "Claude", "gemini": "Gemini", "perplexity": "Perplexity"}
            recommendations.append({
                "priority": "medium",
                "category": "ai_specific",
                "title": f"Améliorer la visibilité sur {ai_names.get(ai, ai)}",
                "description": f"Score sur {ai_names.get(ai, ai)}: {score}%. Adaptez votre contenu aux préférences de ce moteur IA spécifique. Analysez comment vos concurrents y sont positionnés.",
                "impact": "moyen",
                "effort": "moyen",
                "metrics_impacted": [f"ai_{ai}", "relevance"]
            })
    
    # Opportunity-based recommendations
    if indices.get("opportunity_score", 0) > 60:
        recommendations.append({
            "priority": "medium",
            "category": "opportunity",
            "title": "Exploiter les opportunités de marché",
            "description": f"Opportunity Score™: {indices.get('opportunity_score', 0)}%. Il existe de nombreuses requêtes où ni vous ni vos concurrents n'êtes bien positionnés. C'est une opportunité à saisir!",
            "impact": "élevé",
            "effort": "moyen",
            "metrics_impacted": ["opportunity_score", "market_share"]
        })
    
    # General recommendations
    recommendations.append({
        "priority": "low",
        "category": "content",
        "title": "Créer du contenu FAQ structuré",
        "description": "Les IAs privilégient le contenu structuré en questions-réponses. Ajoutez une section FAQ complète avec des réponses détaillées sur votre site.",
        "impact": "moyen",
        "effort": "faible",
        "metrics_impacted": ["relevance", "authority"]
    })
    
    recommendations.append({
        "priority": "low",
        "category": "schema",
        "title": "Implémenter les Schema.org",
        "description": "Ajoutez les balises Schema.org (Organization, Product, FAQ) pour aider les IAs à mieux comprendre votre contenu.",
        "impact": "moyen",
        "effort": "faible",
        "metrics_impacted": ["authority", "crawlability"]
    })
    
    # Sort by priority
    priority_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    recommendations.sort(key=lambda x: priority_order.get(x["priority"], 3))
    
    return recommendations[:12]

@api_router.post("/analysis/check-eligibility")
async def check_analysis_eligibility(request: Request, user: dict = Depends(get_current_user)):
    """Check if user is eligible to start an analysis (anti-abuse check)"""
    body = await request.json()
    project_id = body.get("project_id")
    fingerprint = body.get("fingerprint", "unknown")
    
    # Check project exists
    project = await db.projects.find_one({"project_id": project_id, "user_id": user["user_id"]}, {"_id": 0})
    if not project:
        raise HTTPException(status_code=404, detail="Projet non trouvé")
    
    # Check subscription
    subscription = await db.subscriptions.find_one({"user_id": user["user_id"]}, {"_id": 0})
    if not subscription:
        return {"eligible": False, "reason": "Abonnement requis", "is_free_trial": False}
    
    plan = subscription.get("plan", "free")
    is_free_trial = plan == "free" and subscription.get("queries_used", 0) == 0
    
    if not is_free_trial:
        # Paid users are always eligible (within their limits)
        queries_used = subscription.get("queries_used", 0)
        queries_limit = subscription.get("queries_limit", 0)
        return {
            "eligible": queries_used < queries_limit,
            "reason": "Limite d'analyses atteinte" if queries_used >= queries_limit else "Éligible",
            "is_free_trial": False,
            "queries_remaining": max(0, queries_limit - queries_used)
        }
    
    # Free trial - check anti-abuse
    client_ip = get_client_ip(request)
    eligibility = await check_free_trial_eligibility(
        email=user.get("email", ""),
        ip_address=client_ip,
        fingerprint=fingerprint,
        domain_to_analyze=project.get("website_url", "")
    )
    
    return {
        "eligible": eligibility["eligible"],
        "reason": eligibility["reason"],
        "blocked_by": eligibility.get("blocked_by"),
        "is_free_trial": True
    }

@api_router.post("/analysis/start")
async def start_analysis(request: Request, user: dict = Depends(get_current_user)):
    """Start a new IAskan Verified GEO Protocol™ analysis"""
    body = await request.json()
    project_id = body.get("project_id")
    fingerprint = body.get("fingerprint", "unknown")  # Browser fingerprint from frontend
    
    # Check project exists
    project = await db.projects.find_one({"project_id": project_id, "user_id": user["user_id"]}, {"_id": 0})
    if not project:
        raise HTTPException(status_code=404, detail="Projet non trouvé")
    
    # Check subscription limits
    subscription = await db.subscriptions.find_one({"user_id": user["user_id"]}, {"_id": 0})
    if not subscription:
        raise HTTPException(status_code=403, detail="Abonnement requis")
    
    plan = subscription.get("plan", "free")
    plan_config = SUBSCRIPTION_PLANS.get(plan, SUBSCRIPTION_PLANS["starter"])
    
    # ===== ANTI-ABUSE CHECK FOR FREE TRIAL =====
    is_free_trial = plan == "free" and subscription.get("queries_used", 0) == 0
    
    if is_free_trial:
        client_ip = get_client_ip(request)
        domain_to_analyze = project.get("website_url", "")
        user_email = user.get("email", "")
        
        # Check eligibility
        eligibility = await check_free_trial_eligibility(
            email=user_email,
            ip_address=client_ip,
            fingerprint=fingerprint,
            domain_to_analyze=domain_to_analyze
        )
        
        if not eligibility["eligible"]:
            logger.warning(f"Free trial blocked: user={user_email}, reason={eligibility['blocked_by']}, ip={client_ip}")
            raise HTTPException(
                status_code=403,
                detail={
                    "error": "free_trial_blocked",
                    "reason": eligibility["reason"],
                    "blocked_by": eligibility["blocked_by"]
                }
            )
        
        # Record free trial usage BEFORE starting analysis
        await record_free_trial_usage(
            email=user_email,
            ip_address=client_ip,
            fingerprint=fingerprint,
            domain_analyzed=domain_to_analyze,
            user_id=user["user_id"]
        )
    
    # Create analysis
    analysis = Analysis(
        project_id=project_id,
        user_id=user["user_id"],
        status="running"
    )
    
    doc = analysis.model_dump()
    doc["created_at"] = doc["created_at"].isoformat()
    doc["protocol_version"] = "IAskan Verified GEO Protocol™ v2.0"
    doc["is_free_trial"] = is_free_trial
    await db.analyses.insert_one(doc)
    
    # Start analysis in background with full plan config
    asyncio.create_task(run_analysis_v2(doc["analysis_id"], project, plan_config))
    
    return {"analysis_id": doc["analysis_id"], "status": "running", "protocol": "IAskan Verified GEO Protocol™"}


async def run_analysis_v2(analysis_id: str, project: dict, plan_config: dict):
    """
    IAskan Verified GEO Protocol™ - Main Analysis Engine
    
    Features:
    - Multi-runs per query for stability measurement
    - Multi-dimension query generation (30% transactional, 25% comparative, etc.)
    - Variations per prompt for deeper analysis
    - 4-layer semantic analysis (Presence, Role, Credibility, Conversion)
    - Advanced indices: Stability Index™, Dominance Index™, Trust Gap™, Opportunity Score™
    - R.A.T.E.™ score with adjusted weights
    - Anti-hallucination checks
    - Brand variants detection (typos, products, abbreviations)
    - Site enrichment analysis (schema.org, FAQ, trust signals)
    - Historical diff (comparison with previous scan)
    """
    try:
        # Extract plan parameters
        ai_engines = plan_config.get("ai_engines", ["chatgpt"])
        num_prompts = plan_config.get("num_prompts", 10)
        runs_per_query = plan_config.get("runs_per_query", 3)
        
        # Calculate total queries: prompts × runs × engines
        total_api_calls = num_prompts * runs_per_query * len(ai_engines)
        
        brand_name = project.get("brand_name", "")
        keywords = project.get("keywords", [])
        competitors = project.get("competitors", [])
        website_url = project.get("website_url", "")
        products = project.get("products", [])  # Product names for variant detection
        
        if not brand_name:
            raise ValueError("Nom de marque requis")
        
        # ===== PRE-PHASE: Generate Brand Variants =====
        brand_variants = generate_brand_variants(brand_name, products)
        
        # Update status with phase info
        await db.analyses.update_one(
            {"analysis_id": analysis_id},
            {"$set": {
                "current_phase": "initializing",
                "plan_config": {
                    "num_prompts": num_prompts,
                    "runs_per_query": runs_per_query,
                    "ai_engines": ai_engines,
                    "total_api_calls": total_api_calls
                },
                "brand_variants": brand_variants[:20]  # Store top 20 variants
            }}
        )
        
        # ===== PRE-PHASE: Site Enrichment Analysis =====
        site_enrichment = {}
        if website_url:
            await db.analyses.update_one(
                {"analysis_id": analysis_id},
                {"$set": {"current_phase": "site_analysis"}}
            )
            site_enrichment = await analyze_site_enrichment(website_url)
        
        # ===== PRE-PHASE: Get Previous Analysis for Diff =====
        previous_analysis = await db.analyses.find_one(
            {
                "project_id": project.get("project_id"),
                "user_id": project.get("user_id"),
                "status": "completed",
                "analysis_id": {"$ne": analysis_id}
            },
            {"_id": 0},
            sort=[("created_at", -1)]
        )
        
        # ===== PHASE 1: Generate Multi-Dimension Queries =====
        await db.analyses.update_one(
            {"analysis_id": analysis_id},
            {"$set": {"current_phase": "query_generation"}}
        )
        queries = generate_queries_multi_dimension(brand_name, keywords, competitors, num_prompts)
        
        await db.analyses.update_one(
            {"analysis_id": analysis_id},
            {"$set": {"current_phase": "ai_querying", "total_queries": len(queries), "total_api_calls": total_api_calls}}
        )
        
        # ===== PHASE 2: Multi-Run AI Querying =====
        all_responses = []
        ai_scores = {ai: [] for ai in ai_engines}
        query_results = []
        brand_mention_details = []  # Track detailed mention data
        
        for query_idx, query in enumerate(queries):
            query_text = query["text"]
            query_type = query["type"]
            
            query_all_responses = []
            
            for ai in ai_engines:
                ai_run_responses = []
                
                # Execute multi-runs for each prompt
                for run_id in range(1, runs_per_query + 1):
                    response = await query_ai_engine_v2(
                        query_text,
                        brand_name,
                        competitors,
                        ai,
                        run_id
                    )
                    
                    # Enhanced: Detect brand variants in response
                    response_text = response.get("response_excerpt", "")
                    advanced_mentions = detect_brand_mentions_advanced(response_text, brand_name, brand_variants)
                    response["advanced_mentions"] = advanced_mentions
                    
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
            
            # Aggregate query results with enhanced mention data
            mention_count = sum(1 for r in query_all_responses if r.get("brand_mentioned", False) or r.get("advanced_mentions", {}).get("total_mentions", 0) > 0)
            
            query_result = {
                "query_text": query_text,
                "query_type": query_type,
                "keyword": query.get("keyword", ""),
                "responses": query_all_responses,
                "runs_per_ai": runs_per_query,
                "avg_score": sum(r.get("role_score", 0) for r in query_all_responses) / len(query_all_responses) * 100 if query_all_responses else 0,
                "mention_rate": (mention_count / len(query_all_responses) * 100) if query_all_responses else 0,
                "stability": {
                    "roles": list(set(r.get("role", "absent") for r in query_all_responses)),
                    "consistent": len(set(r.get("role", "absent") for r in query_all_responses)) <= 2
                }
            }
            query_results.append(query_result)
            
            # Update progress
            await db.analyses.update_one(
                {"analysis_id": analysis_id},
                {"$set": {"queries_processed": query_idx + 1}}
            )
        
        await db.analyses.update_one(
            {"analysis_id": analysis_id},
            {"$set": {"current_phase": "calculating_indices"}}
        )
        
        # ===== PHASE 3: Calculate Stability Index™ =====
        stability_data = calculate_stability_index(all_responses)
        
        # ===== PHASE 4: Calculate Advanced Indices =====
        indices = calculate_advanced_indices(all_responses, brand_name, competitors)
        indices["stability_index"] = stability_data.get("stability_score", 0)
        
        # ===== PHASE 5: Calculate R.A.T.E.™ Score (Enhanced) =====
        rate_score = calculate_rate_score_v2(all_responses, stability_data)
        
        # ===== PHASE 6: Calculate Per-AI Scores =====
        final_ai_scores = {}
        for ai, scores in ai_scores.items():
            final_ai_scores[ai] = round(sum(scores) / len(scores), 1) if scores else 0
        
        # ===== PHASE 7: Generate Recommendations =====
        recommendations = generate_recommendations_v2(rate_score, final_ai_scores, indices, stability_data)
        
        # ===== PHASE 8: Query Type Analysis =====
        query_type_breakdown = {}
        for qt in QUERY_TYPE_DISTRIBUTION.keys():
            qt_queries = [q for q in query_results if q.get("query_type") == qt]
            if qt_queries:
                query_type_breakdown[qt] = {
                    "count": len(qt_queries),
                    "avg_score": round(sum(q.get("avg_score", 0) for q in qt_queries) / len(qt_queries), 1),
                    "mention_rate": round(sum(q.get("mention_rate", 0) for q in qt_queries) / len(qt_queries), 1)
                }
        
        # ===== PHASE 9: Identify Discovered Competitors =====
        discovered_competitors = await identify_competitors_from_analysis(all_responses, brand_name, competitors)
        
        # Update project with discovered competitors
        await db.projects.update_one(
            {"project_id": project.get("project_id")},
            {"$set": {"discovered_competitors": discovered_competitors}}
        )
        
        # Merge user-defined and discovered competitors for analysis summary
        all_competitors_analyzed = list(set(competitors[:5] + [c["name"] for c in discovered_competitors[:10]]))
        
        # ===== PHASE 10: Finalize Analysis =====
        analysis_summary = {
            "total_prompts": num_prompts,
            "runs_per_query": runs_per_query,
            "total_api_calls": total_api_calls,
            "total_responses": len(all_responses),
            "ai_engines_used": ai_engines,
            "competitors_analyzed": all_competitors_analyzed[:10],
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
                "site_enrichment_analysis": bool(site_enrichment),
                "historical_diff": previous_analysis is not None
            }
        }
        
        # Build comprehensive competitor comparison
        competitor_comparison = []
        already_added = set()
        
        for comp in discovered_competitors[:10]:
            comp_name = comp["name"]
            already_added.add(comp_name.lower())
            competitor_comparison.append({
                "competitor": comp_name,
                "mentions": comp.get("mentions", 0),
                "visibility_rate": comp.get("visibility_score", 0),
                "presence_rate": comp.get("presence_rate", 0),
                "ai_sources": comp.get("ai_sources", []),
                "discovered": comp.get("discovered", True),
                "user_defined": comp.get("user_defined", False),
                "responses_containing": comp.get("responses_containing", 0)
            })
        
        # Add user-defined competitors that weren't discovered
        for comp in competitors[:5]:
            if comp.lower() not in already_added:
                competitor_comparison.append({
                    "competitor": comp,
                    "mentions": 0,
                    "visibility_rate": 0,
                    "presence_rate": 0,
                    "ai_sources": [],
                    "discovered": False,
                    "user_defined": True,
                    "responses_containing": 0
                })
        
        # ===== PHASE 11: Calculate Historical Diff =====
        scan_diff = await calculate_scan_diff(
            {
                "global_score": rate_score["total"],
                "rate_score": rate_score,
                "ai_scores": final_ai_scores,
                "indices": indices,
                "created_at": datetime.now(timezone.utc).isoformat()
            },
            previous_analysis
        )
        
        # ===== PHASE 12: Aggregate Brand Mention Analysis =====
        brand_analysis = {
            "variants_used": brand_variants[:20],
            "mention_details": brand_mention_details[:50],  # Top 50 mention instances
            "mention_quality_distribution": {},
            "variants_found_summary": {}
        }
        
        # Summarize mention quality distribution
        quality_counts = {}
        variants_found_counts = {}
        for detail in brand_mention_details:
            quality = detail.get("mention_quality", "unknown")
            quality_counts[quality] = quality_counts.get(quality, 0) + 1
            for variant in detail.get("variants_found", []):
                variants_found_counts[variant] = variants_found_counts.get(variant, 0) + 1
        
        brand_analysis["mention_quality_distribution"] = quality_counts
        brand_analysis["variants_found_summary"] = dict(sorted(variants_found_counts.items(), key=lambda x: -x[1])[:10])
        
        # ===== Add site enrichment recommendations to main recommendations =====
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
        
        # Update analysis with complete results
        await db.analyses.update_one(
            {"analysis_id": analysis_id},
            {"$set": {
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
                "current_phase": "completed",
                "completed_at": datetime.now(timezone.utc).isoformat(),
                # NEW: Enhanced scan data
                "site_enrichment": site_enrichment,
                "scan_diff": scan_diff,
                "brand_analysis": brand_analysis
            }}
        )
        
        # Update subscription usage - use total_api_calls calculated at the start
        await db.subscriptions.update_one(
            {"user_id": project["user_id"]},
            {"$inc": {"queries_used": total_api_calls, "scans_used": 1}}
        )
        
        logger.info(f"Analysis {analysis_id} completed: {num_prompts} prompts × {runs_per_query} runs × {len(ai_engines)} AI = {total_api_calls} total queries")
        
        # ===== SEND NOTIFICATIONS =====
        user_id = project.get("user_id")
        project_name = project.get("name", "Projet")
        global_score = rate_score["total"]
        
        # Create in-app notification
        await create_notification(
            user_id=user_id,
            notification_type="scan_complete",
            title="Scan terminé",
            message=f"L'analyse de {project_name} est terminée. Score: {int(global_score)}/100",
            data={
                "analysis_id": analysis_id,
                "project_id": project.get("project_id"),
                "project_name": project_name,
                "global_score": global_score,
                "grade": rate_score.get("grade", "N/A")
            }
        )
        
        # Send email notification
        user = await db.users.find_one({"user_id": user_id}, {"_id": 0})
        if user:
            # Get analysis to check if it's a scheduled scan
            analysis_data = await db.analyses.find_one({"analysis_id": analysis_id}, {"_id": 0})
            is_scheduled = analysis_data.get("scheduled", False) if analysis_data else False
            
            if is_scheduled:
                # For scheduled scans, use the special report email
                schedule = await db.scan_schedules.find_one(
                    {"schedule_id": analysis_data.get("schedule_id")},
                    {"_id": 0}
                )
                recipients = schedule.get("report_recipients", []) if schedule else []
                
                await send_scheduled_report_email(
                    user_email=user.get("email", ""),
                    user_name=user.get("name", ""),
                    project_name=project_name,
                    analysis_id=analysis_id,
                    global_score=global_score,
                    grade=rate_score.get("grade", "N/A"),
                    recipients=recipients
                )
            else:
                # For manual scans, use the standard notification email
                await send_scan_complete_email(
                    user_email=user.get("email", ""),
                    user_name=user.get("name", ""),
                    project_name=project_name,
                    analysis_id=analysis_id,
                    global_score=global_score
                )
        
    except Exception as e:
        logger.error(f"Analysis error: {e}")
        await db.analyses.update_one(
            {"analysis_id": analysis_id},
            {"$set": {
                "status": "failed",
                "error": str(e),
                "current_phase": "failed"
            }}
        )
        
        # Create failure notification
        user_id = project.get("user_id")
        project_name = project.get("name", "Projet")
        await create_notification(
            user_id=user_id,
            notification_type="scan_failed",
            title="Échec du scan",
            message=f"L'analyse de {project_name} a échoué. Veuillez réessayer.",
            data={
                "analysis_id": analysis_id,
                "project_id": project.get("project_id"),
                "project_name": project_name,
                "error": str(e)
            }
        )

@api_router.get("/analysis/{analysis_id}")
async def get_analysis(analysis_id: str, user: dict = Depends(get_current_user)):
    """Get analysis results"""
    analysis = await db.analyses.find_one(
        {"analysis_id": analysis_id, "user_id": user["user_id"]},
        {"_id": 0}
    )
    if not analysis:
        raise HTTPException(status_code=404, detail="Analyse non trouvée")
    return {"analysis": analysis}

@api_router.get("/analyses")
async def get_analyses(project_id: Optional[str] = None, user: dict = Depends(get_current_user)):
    """Get all analyses for user or project"""
    query = {"user_id": user["user_id"]}
    if project_id:
        query["project_id"] = project_id
    
    analyses = await db.analyses.find(query, {"_id": 0}).sort("created_at", -1).to_list(50)
    return {"analyses": analyses}

@api_router.get("/analyses/history/{project_id}")
async def get_analysis_history(project_id: str, user: dict = Depends(get_current_user)):
    """Get analysis history with trends for charts"""
    # Verify project belongs to user
    project = await db.projects.find_one(
        {"project_id": project_id, "user_id": user["user_id"]},
        {"_id": 0}
    )
    if not project:
        raise HTTPException(status_code=404, detail="Projet non trouvé")
    
    # Get completed analyses
    analyses = await db.analyses.find(
        {"project_id": project_id, "user_id": user["user_id"], "status": "completed"},
        {"_id": 0}
    ).sort("created_at", 1).to_list(100)
    
    # Format data for charts
    history = {
        "score_evolution": [],
        "rate_evolution": [],
        "ai_evolution": {
            "chatgpt": [],
            "claude": [],
            "gemini": [],
            "perplexity": []
        },
        "summary": {
            "total_analyses": len(analyses),
            "first_analysis": analyses[0]["created_at"] if analyses else None,
            "last_analysis": analyses[-1]["created_at"] if analyses else None,
            "score_change": 0,
            "trend": "stable"
        }
    }
    
    for analysis in analyses:
        created_at = analysis.get("created_at", "")
        
        # Score evolution
        history["score_evolution"].append({
            "date": created_at,
            "score": round(analysis.get("global_score", 0), 1),
            "analysis_id": analysis.get("analysis_id")
        })
        
        # R.A.T.E. evolution
        rate_score = analysis.get("rate_score", {})
        history["rate_evolution"].append({
            "date": created_at,
            "relevance": round(rate_score.get("relevance", 0), 1),
            "authority": round(rate_score.get("authority", 0), 1),
            "truthfulness": round(rate_score.get("truthfulness", 0), 1),
            "endorsement": round(rate_score.get("endorsement", 0), 1)
        })
        
        # AI evolution
        ai_scores = analysis.get("ai_scores", {})
        for ai in ["chatgpt", "claude", "gemini", "perplexity"]:
            history["ai_evolution"][ai].append({
                "date": created_at,
                "score": round(ai_scores.get(ai, 0), 1)
            })
    
    # Calculate trend
    if len(analyses) >= 2:
        first_score = analyses[0].get("global_score", 0)
        last_score = analyses[-1].get("global_score", 0)
        history["summary"]["score_change"] = round(last_score - first_score, 1)
        
        if history["summary"]["score_change"] > 5:
            history["summary"]["trend"] = "up"
        elif history["summary"]["score_change"] < -5:
            history["summary"]["trend"] = "down"
        else:
            history["summary"]["trend"] = "stable"
    
    return {"history": history, "project": project}

@api_router.get("/comparisons/history/{project_id}")
async def get_comparison_history(project_id: str, user: dict = Depends(get_current_user)):
    """Get competitor comparison history for charts"""
    # Get completed comparisons
    comparisons = await db.competitor_comparisons.find(
        {"project_id": project_id, "user_id": user["user_id"], "status": "completed"},
        {"_id": 0}
    ).sort("created_at", 1).to_list(50)
    
    history = {
        "ranking_evolution": [],
        "dominance_evolution": [],
        "brand_evolution": {}
    }
    
    for comp in comparisons:
        created_at = comp.get("created_at", "")
        results = comp.get("results", {})
        summary = results.get("summary", {})
        rankings = results.get("rankings", {})
        
        # Ranking evolution
        history["ranking_evolution"].append({
            "date": created_at,
            "rank": summary.get("user_rank", 0),
            "score": summary.get("user_score", 0)
        })
        
        # Dominance evolution
        history["dominance_evolution"].append({
            "date": created_at,
            "dominance": summary.get("dominance_index", 0)
        })
        
        # Brand evolution
        for brand, data in rankings.items():
            if brand not in history["brand_evolution"]:
                history["brand_evolution"][brand] = []
            history["brand_evolution"][brand].append({
                "date": created_at,
                "score": data.get("score", 0),
                "rank": data.get("rank", 0),
                "is_user": data.get("is_user_brand", False)
            })
    
    return {"history": history}

# ================== PDF REPORT GENERATION ==================

class IAskanPDF(FPDF):
    """Custom PDF class for IAskan reports"""
    
    def __init__(self):
        super().__init__()
        self.set_auto_page_break(auto=True, margin=20)
        # Add Unicode font
        self.add_font('DejaVu', '', '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', uni=True)
        self.add_font('DejaVu', 'B', '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', uni=True)
    
    def header(self):
        # Logo/Brand
        self.set_font('DejaVu', 'B', 20)
        self.set_text_color(124, 58, 237)  # Violet
        self.cell(0, 10, 'IAskan', align='L')
        self.set_font('DejaVu', '', 10)
        self.set_text_color(100, 116, 139)  # Slate
        self.cell(0, 10, 'Rapport GEO', align='R', new_x='LMARGIN', new_y='NEXT')
        self.ln(5)
        # Line separator
        self.set_draw_color(226, 232, 240)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(10)
    
    def footer(self):
        self.set_y(-15)
        self.set_font('DejaVu', '', 8)
        self.set_text_color(148, 163, 184)
        self.cell(0, 10, f'IAskan - Rapport genere le {datetime.now().strftime("%d/%m/%Y a %H:%M")} - Page {self.page_no()}', align='C')
    
    def section_title(self, title):
        self.set_font('DejaVu', 'B', 14)
        self.set_text_color(15, 23, 42)  # Slate 900
        self.cell(0, 10, title, new_x='LMARGIN', new_y='NEXT')
        self.ln(2)
    
    def add_score_box(self, label, score, x, y, width=45, height=25):
        # Background
        if score >= 70:
            self.set_fill_color(220, 252, 231)  # Green 100
            text_color = (22, 163, 74)  # Green 600
        elif score >= 40:
            self.set_fill_color(254, 249, 195)  # Yellow 100
            text_color = (202, 138, 4)  # Yellow 600
        else:
            self.set_fill_color(254, 226, 226)  # Red 100
            text_color = (220, 38, 38)  # Red 600
        
        self.set_xy(x, y)
        self.rect(x, y, width, height, style='F')
        
        # Score
        self.set_xy(x, y + 2)
        self.set_font('DejaVu', 'B', 16)
        self.set_text_color(*text_color)
        self.cell(width, 10, str(round(score)), align='C')
        
        # Label
        self.set_xy(x, y + 12)
        self.set_font('DejaVu', '', 9)
        self.set_text_color(100, 116, 139)
        self.cell(width, 8, label, align='C')


def generate_analysis_pdf(analysis: dict, project: dict) -> bytes:
    """Generate a PDF report for an analysis"""
    pdf = IAskanPDF()
    pdf.add_page()
    
    # Project Info
    pdf.set_font('DejaVu', 'B', 18)
    pdf.set_text_color(15, 23, 42)
    pdf.cell(0, 10, f"Rapport d'Analyse GEO", new_x='LMARGIN', new_y='NEXT')
    
    pdf.set_font('DejaVu', '', 11)
    pdf.set_text_color(100, 116, 139)
    pdf.cell(0, 8, f"Projet: {project.get('name', 'N/A')}", new_x='LMARGIN', new_y='NEXT')
    pdf.cell(0, 8, f"Marque: {project.get('brand_name', 'N/A')}", new_x='LMARGIN', new_y='NEXT')
    
    created_at = analysis.get('created_at', '')
    if isinstance(created_at, str):
        try:
            created_at = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
            created_at = created_at.strftime('%d/%m/%Y à %H:%M')
        except:
            pass
    pdf.cell(0, 8, f"Date d'analyse: {created_at}", new_x='LMARGIN', new_y='NEXT')
    pdf.ln(10)
    
    # Global Score Section
    pdf.section_title("Score GEO Global")
    
    global_score = analysis.get('global_score', 0)
    
    # Main score display
    pdf.set_font('DejaVu', 'B', 48)
    if global_score >= 70:
        pdf.set_text_color(22, 163, 74)
    elif global_score >= 40:
        pdf.set_text_color(202, 138, 4)
    else:
        pdf.set_text_color(220, 38, 38)
    pdf.cell(50, 25, str(round(global_score)), align='C')
    
    pdf.set_font('DejaVu', '', 14)
    pdf.set_text_color(148, 163, 184)
    pdf.cell(20, 25, '/ 100')
    pdf.ln(30)
    
    # R.A.T.E. Scores
    pdf.section_title("Score R.A.T.E.™")
    pdf.set_font('DejaVu', '', 10)
    pdf.set_text_color(100, 116, 139)
    pdf.cell(0, 6, "Relevance • Authority • Truthfulness • Endorsement", new_x='LMARGIN', new_y='NEXT')
    pdf.ln(5)
    
    rate_score = analysis.get('rate_score', {})
    rate_items = [
        ('Relevance', rate_score.get('relevance', 0)),
        ('Authority', rate_score.get('authority', 0)),
        ('Truthfulness', rate_score.get('truthfulness', 0)),
        ('Endorsement', rate_score.get('endorsement', 0))
    ]
    
    start_x = 15
    for i, (label, score) in enumerate(rate_items):
        pdf.add_score_box(label, score, start_x + (i * 48), pdf.get_y())
    pdf.ln(35)
    
    # AI Scores
    ai_scores = analysis.get('ai_scores', {})
    if ai_scores:
        pdf.section_title("Score par Moteur IA")
        pdf.ln(5)
        
        ai_names = {'chatgpt': 'ChatGPT', 'claude': 'Claude', 'gemini': 'Gemini', 'perplexity': 'Perplexity'}
        start_x = 15
        for i, (ai, score) in enumerate(ai_scores.items()):
            pdf.add_score_box(ai_names.get(ai, ai), score, start_x + (i * 48), pdf.get_y())
        pdf.ln(35)
    
    # Query Results
    query_scores = analysis.get('query_scores', [])
    if query_scores:
        pdf.add_page()
        pdf.section_title("Détail des Requêtes Analysées")
        pdf.ln(3)
        
        for i, query in enumerate(query_scores[:10], 1):
            query_text = query.get('query_text', '')[:80]
            avg_score = query.get('avg_score', 0)
            
            # Query box
            pdf.set_fill_color(248, 250, 252)
            pdf.rect(10, pdf.get_y(), 190, 18, style='F')
            
            pdf.set_xy(12, pdf.get_y() + 2)
            pdf.set_font('DejaVu', 'B', 10)
            pdf.set_text_color(15, 23, 42)
            pdf.cell(150, 6, f"{i}. {query_text}")
            
            # Score badge
            if avg_score >= 70:
                pdf.set_fill_color(220, 252, 231)
                pdf.set_text_color(22, 163, 74)
            elif avg_score >= 40:
                pdf.set_fill_color(254, 249, 195)
                pdf.set_text_color(202, 138, 4)
            else:
                pdf.set_fill_color(254, 226, 226)
                pdf.set_text_color(220, 38, 38)
            
            pdf.set_xy(170, pdf.get_y())
            pdf.set_font('DejaVu', 'B', 11)
            pdf.cell(25, 6, str(round(avg_score)), align='C', fill=True)
            
            # AI responses
            pdf.set_xy(12, pdf.get_y() + 8)
            pdf.set_font('DejaVu', '', 8)
            pdf.set_text_color(100, 116, 139)
            
            responses = query.get('responses', [])
            response_text = ' | '.join([f"{r.get('ai_type', '?')}: {r.get('role', 'absent')}" for r in responses[:4]])
            pdf.cell(180, 5, response_text)
            
            pdf.ln(20)
            
            # Add page break if needed
            if pdf.get_y() > 250:
                pdf.add_page()
    
    # Recommendations
    recommendations = analysis.get('recommendations', [])
    if recommendations:
        pdf.add_page()
        pdf.section_title("Recommandations Prioritaires")
        pdf.ln(5)
        
        priority_colors = {
            'high': (220, 38, 38),
            'medium': (202, 138, 4),
            'low': (100, 116, 139)
        }
        priority_labels = {
            'high': 'HAUTE',
            'medium': 'MOYENNE', 
            'low': 'FAIBLE'
        }
        
        for rec in recommendations[:8]:
            priority = rec.get('priority', 'low')
            
            # Priority badge
            pdf.set_font('DejaVu', 'B', 8)
            pdf.set_text_color(*priority_colors.get(priority, (100, 116, 139)))
            pdf.cell(25, 6, priority_labels.get(priority, 'N/A'))
            
            # Title
            pdf.set_font('DejaVu', 'B', 11)
            pdf.set_text_color(15, 23, 42)
            pdf.cell(0, 6, rec.get('title', ''), new_x='LMARGIN', new_y='NEXT')
            
            # Description
            pdf.set_font('DejaVu', '', 10)
            pdf.set_text_color(100, 116, 139)
            description = rec.get('description', '')[:200]
            pdf.multi_cell(0, 5, description)
            
            # Impact/Effort
            pdf.set_font('DejaVu', '', 9)
            pdf.set_text_color(148, 163, 184)
            pdf.cell(0, 5, f"Impact: {rec.get('impact', 'N/A')} | Effort: {rec.get('effort', 'N/A')}", new_x='LMARGIN', new_y='NEXT')
            pdf.ln(8)
            
            if pdf.get_y() > 260:
                pdf.add_page()
    
    # Final page - Summary
    pdf.add_page()
    pdf.section_title("Synthèse et Prochaines Étapes")
    pdf.ln(5)
    
    pdf.set_font('DejaVu', '', 11)
    pdf.set_text_color(51, 65, 85)
    
    # Generate summary based on scores
    if global_score >= 70:
        summary = f"Votre marque '{project.get('brand_name', '')}' bénéficie d'une excellente visibilité dans les réponses IA avec un score de {round(global_score)}/100. Continuez à maintenir votre présence et explorez les opportunités d'amélioration identifiées."
    elif global_score >= 40:
        summary = f"Votre marque '{project.get('brand_name', '')}' a une visibilité modérée dans les réponses IA ({round(global_score)}/100). Les recommandations ci-dessus vous aideront à améliorer significativement votre positionnement."
    else:
        summary = f"Votre marque '{project.get('brand_name', '')}' a une visibilité limitée dans les réponses IA ({round(global_score)}/100). Une action prioritaire sur les recommandations est nécessaire pour améliorer votre présence."
    
    pdf.multi_cell(0, 6, summary)
    pdf.ln(10)
    
    # Key metrics summary
    pdf.set_font('DejaVu', 'B', 11)
    pdf.set_text_color(15, 23, 42)
    pdf.cell(0, 8, "Métriques Clés:", new_x='LMARGIN', new_y='NEXT')
    
    pdf.set_font('DejaVu', '', 10)
    pdf.set_text_color(51, 65, 85)
    
    metrics = [
        f"• Score GEO Global: {round(global_score)}/100",
        f"• Relevance: {round(rate_score.get('relevance', 0))}%",
        f"• Authority: {round(rate_score.get('authority', 0))}%",
        f"• Truthfulness: {round(rate_score.get('truthfulness', 0))}%",
        f"• Endorsement: {round(rate_score.get('endorsement', 0))}%",
        f"• Requêtes analysées: {len(query_scores)}",
        f"• Moteurs IA testés: {len(ai_scores)}"
    ]
    
    for metric in metrics:
        pdf.cell(0, 6, metric, new_x='LMARGIN', new_y='NEXT')
    
    pdf.ln(15)
    
    # CTA
    pdf.set_fill_color(238, 242, 255)  # Violet 50
    pdf.rect(10, pdf.get_y(), 190, 25, style='F')
    pdf.set_xy(15, pdf.get_y() + 5)
    pdf.set_font('DejaVu', 'B', 11)
    pdf.set_text_color(124, 58, 237)
    pdf.cell(0, 6, "Besoin d'aide pour améliorer votre score GEO?", new_x='LMARGIN', new_y='NEXT')
    pdf.set_xy(15, pdf.get_y())
    pdf.set_font('DejaVu', '', 10)
    pdf.set_text_color(100, 116, 139)
    pdf.cell(0, 6, "Contactez notre équipe pour un accompagnement personnalisé.")
    
    # Output PDF
    return bytes(pdf.output())


@api_router.get("/analysis/{analysis_id}/pdf")
async def download_analysis_pdf(analysis_id: str, user: dict = Depends(get_current_user)):
    """Generate and download PDF report for an analysis"""
    # Get analysis
    analysis = await db.analyses.find_one(
        {"analysis_id": analysis_id, "user_id": user["user_id"]},
        {"_id": 0}
    )
    if not analysis:
        raise HTTPException(status_code=404, detail="Analyse non trouvée")
    
    if analysis.get("status") != "completed":
        raise HTTPException(status_code=400, detail="L'analyse n'est pas encore terminée")
    
    # Get project
    project = await db.projects.find_one(
        {"project_id": analysis.get("project_id")},
        {"_id": 0}
    )
    if not project:
        project = {"name": "Projet", "brand_name": "Marque"}
    
    # Generate PDF
    pdf_bytes = generate_analysis_pdf(analysis, project)
    
    # Create filename
    project_name = project.get('name', 'analyse').replace(' ', '_')
    filename = f"IAskan_Rapport_{project_name}_{analysis_id}.pdf"
    
    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

# ================== COMPETITOR COMPARISON ==================

class CompetitorAnalysisRequest(BaseModel):
    project_id: str
    competitors: List[str] = []

async def analyze_competitor_visibility(brand_name: str, query: str, ai_type: str) -> Dict[str, Any]:
    """Analyze a competitor's visibility for a specific query"""
    try:
        session_id = f"comp_{uuid.uuid4().hex[:8]}"
        
        chat = LlmChat(
            api_key=EMERGENT_LLM_KEY,
            session_id=session_id,
            system_message="Tu es un assistant qui répond naturellement aux questions."
        )
        
        if ai_type == "chatgpt":
            chat.with_model("openai", "gpt-5.2")
        elif ai_type == "claude":
            chat.with_model("anthropic", "claude-sonnet-4-5-20250929")
        elif ai_type == "gemini":
            chat.with_model("gemini", "gemini-3-flash-preview")
        else:
            chat.with_model("openai", "gpt-4o")
        
        user_message = UserMessage(text=query)
        response = await chat.send_message(user_message)
        # Response can be a string or an object with .text attribute
        response_text = response if isinstance(response, str) else str(response)
        response_text = response_text.lower() if response_text else ""
        
        # Check if brand is mentioned
        brand_lower = brand_name.lower()
        is_mentioned = brand_lower in response_text
        
        # Determine position/role
        position = 0
        role = "absent"
        
        if is_mentioned:
            # Find position in response
            pos = response_text.find(brand_lower)
            total_length = len(response_text)
            
            if pos < total_length * 0.2:
                position = 1
                role = "leader"
            elif pos < total_length * 0.4:
                position = 2
                role = "challenger"
            elif pos < total_length * 0.6:
                position = 3
                role = "mentioned"
            else:
                position = 4
                role = "cited"
        
        # Calculate visibility score
        visibility_score = 0
        if role == "leader":
            visibility_score = 90 + (hash(brand_name) % 10)
        elif role == "challenger":
            visibility_score = 70 + (hash(brand_name) % 15)
        elif role == "mentioned":
            visibility_score = 45 + (hash(brand_name) % 20)
        elif role == "cited":
            visibility_score = 20 + (hash(brand_name) % 20)
        
        return {
            "brand": brand_name,
            "ai_type": ai_type,
            "is_mentioned": is_mentioned,
            "position": position,
            "role": role,
            "visibility_score": visibility_score,
            "response_excerpt": response_text[:200] if response_text else ""
        }
        
    except Exception as e:
        logger.error(f"Competitor analysis error for {brand_name}: {str(e)}")
        return {
            "brand": brand_name,
            "ai_type": ai_type,
            "is_mentioned": False,
            "position": 0,
            "role": "error",
            "visibility_score": 0,
            "error": str(e)
        }


@api_router.post("/analysis/compare")
async def start_competitor_comparison(request: Request, user: dict = Depends(get_current_user)):
    """Start a competitor comparison analysis"""
    body = await request.json()
    project_id = body.get("project_id")
    custom_competitors = body.get("competitors", [])
    
    # Get project
    project = await db.projects.find_one(
        {"project_id": project_id, "user_id": user["user_id"]},
        {"_id": 0}
    )
    if not project:
        raise HTTPException(status_code=404, detail="Projet non trouvé")
    
    # Get competitors from project or custom list
    competitors = custom_competitors if custom_competitors else project.get("competitors", [])
    if not competitors:
        raise HTTPException(status_code=400, detail="Aucun concurrent défini pour ce projet")
    
    brand_name = project.get("brand_name", "")
    if not brand_name:
        raise HTTPException(status_code=400, detail="Nom de marque requis")
    
    # Create comparison ID
    comparison_id = f"cmp_{uuid.uuid4().hex[:12]}"
    
    # Store initial comparison document
    comparison_doc = {
        "comparison_id": comparison_id,
        "project_id": project_id,
        "user_id": user["user_id"],
        "brand_name": brand_name,
        "competitors": competitors,
        "status": "running",
        "results": {},
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.competitor_comparisons.insert_one(comparison_doc)
    
    # Run comparison in background
    asyncio.create_task(run_competitor_comparison(comparison_id, brand_name, competitors, project))
    
    return {"comparison_id": comparison_id, "status": "running"}


async def run_competitor_comparison(comparison_id: str, brand_name: str, competitors: List[str], project: dict):
    """Run the competitor comparison analysis"""
    try:
        keywords = project.get("keywords", ["best solution", "top provider"])
        
        # Generate comparison queries
        queries = [
            f"Quelle est la meilleure solution pour {keywords[0] if keywords else 'ce domaine'}?",
            f"Comparez les leaders du marché en {keywords[0] if keywords else 'ce secteur'}",
            f"Qui recommandez-vous pour {keywords[0] if keywords else 'ce besoin'}?",
            f"Quels sont les avantages et inconvénients des principales solutions?"
        ]
        
        ai_engines = ["chatgpt", "claude", "gemini"]
        all_brands = [brand_name] + competitors
        
        results = {
            "brand_scores": {},
            "ai_breakdown": {},
            "query_details": [],
            "rankings": {}
        }
        
        # Initialize scores
        for brand in all_brands:
            results["brand_scores"][brand] = {
                "total_score": 0,
                "mention_count": 0,
                "leader_count": 0,
                "avg_position": 0
            }
        
        for ai in ai_engines:
            results["ai_breakdown"][ai] = {}
            for brand in all_brands:
                results["ai_breakdown"][ai][brand] = 0
        
        total_queries = 0
        
        # Run analysis for each query and AI
        for query in queries:
            query_result = {
                "query": query,
                "responses": []
            }
            
            for ai_type in ai_engines:
                # Analyze all brands for this query/AI combination
                brand_results = []
                
                for brand in all_brands:
                    result = await analyze_competitor_visibility(brand, query, ai_type)
                    brand_results.append(result)
                    
                    # Update scores
                    if result["is_mentioned"]:
                        results["brand_scores"][brand]["mention_count"] += 1
                        results["brand_scores"][brand]["total_score"] += result["visibility_score"]
                        if result["role"] == "leader":
                            results["brand_scores"][brand]["leader_count"] += 1
                        if result["position"] > 0:
                            results["brand_scores"][brand]["avg_position"] += result["position"]
                    
                    results["ai_breakdown"][ai_type][brand] += result["visibility_score"]
                
                query_result["responses"].append({
                    "ai_type": ai_type,
                    "brands": brand_results
                })
                
                total_queries += 1
            
            results["query_details"].append(query_result)
        
        # Calculate averages and rankings
        for brand in all_brands:
            scores = results["brand_scores"][brand]
            mention_count = scores["mention_count"] or 1
            scores["avg_score"] = scores["total_score"] / (len(queries) * len(ai_engines)) if total_queries > 0 else 0
            scores["avg_position"] = scores["avg_position"] / mention_count if scores["avg_position"] > 0 else 0
            
            # Average AI breakdown
            for ai in ai_engines:
                results["ai_breakdown"][ai][brand] = results["ai_breakdown"][ai][brand] / len(queries)
        
        # Create rankings
        ranked_brands = sorted(
            all_brands,
            key=lambda b: results["brand_scores"][b]["avg_score"],
            reverse=True
        )
        
        for i, brand in enumerate(ranked_brands):
            results["rankings"][brand] = {
                "rank": i + 1,
                "score": round(results["brand_scores"][brand]["avg_score"], 1),
                "is_user_brand": brand == brand_name
            }
        
        # Calculate dominance index
        user_score = results["brand_scores"][brand_name]["avg_score"]
        competitor_scores = [results["brand_scores"][c]["avg_score"] for c in competitors]
        avg_competitor_score = sum(competitor_scores) / len(competitor_scores) if competitor_scores else 0
        
        dominance_index = ((user_score - avg_competitor_score) / max(avg_competitor_score, 1)) * 100
        
        results["summary"] = {
            "user_brand": brand_name,
            "user_rank": results["rankings"][brand_name]["rank"],
            "user_score": round(user_score, 1),
            "top_competitor": ranked_brands[1] if len(ranked_brands) > 1 and ranked_brands[0] == brand_name else ranked_brands[0],
            "dominance_index": round(dominance_index, 1),
            "total_brands_analyzed": len(all_brands),
            "queries_analyzed": len(queries),
            "ai_engines_used": len(ai_engines)
        }
        
        # Update comparison in database
        await db.competitor_comparisons.update_one(
            {"comparison_id": comparison_id},
            {
                "$set": {
                    "status": "completed",
                    "results": results,
                    "completed_at": datetime.now(timezone.utc).isoformat()
                }
            }
        )
        
    except Exception as e:
        logger.error(f"Competitor comparison error: {str(e)}")
        await db.competitor_comparisons.update_one(
            {"comparison_id": comparison_id},
            {
                "$set": {
                    "status": "failed",
                    "error": str(e),
                    "completed_at": datetime.now(timezone.utc).isoformat()
                }
            }
        )


@api_router.get("/analysis/compare/{comparison_id}")
async def get_competitor_comparison(comparison_id: str, user: dict = Depends(get_current_user)):
    """Get competitor comparison results"""
    comparison = await db.competitor_comparisons.find_one(
        {"comparison_id": comparison_id, "user_id": user["user_id"]},
        {"_id": 0}
    )
    if not comparison:
        raise HTTPException(status_code=404, detail="Comparaison non trouvée")
    
    return {"comparison": comparison}


@api_router.get("/analysis/comparisons/{project_id}")
async def get_project_comparisons(project_id: str, user: dict = Depends(get_current_user)):
    """Get all competitor comparisons for a project"""
    comparisons = await db.competitor_comparisons.find(
        {"project_id": project_id, "user_id": user["user_id"]},
        {"_id": 0}
    ).sort("created_at", -1).to_list(20)
    
    return {"comparisons": comparisons}

# ================== VISIBILITY TRACKING ==================

@api_router.get("/visibility/{project_id}")
async def get_visibility_data(project_id: str, user: dict = Depends(get_current_user)):
    """Get visibility tracking data for a project"""
    # Verify project belongs to user
    project = await db.projects.find_one(
        {"project_id": project_id, "user_id": user["user_id"]},
        {"_id": 0}
    )
    if not project:
        raise HTTPException(status_code=404, detail="Projet non trouve")
    
    # Get latest completed analysis
    latest_analysis = await db.analyses.find_one(
        {"project_id": project_id, "status": "completed"},
        {"_id": 0},
        sort=[("created_at", -1)]
    )
    
    if not latest_analysis:
        # Return default data if no analysis
        return {
            "global_visibility_score": 0,
            "ai_engines": {},
            "position_distribution": {"first": 0, "second": 0, "third": 0, "other": 0, "absent": 100},
            "thematic_visibility": [],
            "recent_queries": [],
            "has_data": False
        }
    
    # Calculate visibility metrics from analysis
    ai_scores = latest_analysis.get("ai_scores", {})
    query_scores = latest_analysis.get("query_scores", [])
    
    # Build AI engines data
    ai_engines = {}
    for ai_name, score in ai_scores.items():
        # Calculate metrics per AI from query scores
        ai_queries = [q for q in query_scores if any(r.get("ai_type") == ai_name for r in q.get("responses", []))]
        mention_count = sum(1 for q in ai_queries for r in q.get("responses", []) if r.get("ai_type") == ai_name and r.get("brand_mentioned"))
        total_ai_queries = len(ai_queries)
        mention_rate = round((mention_count / total_ai_queries * 100) if total_ai_queries > 0 else 0)
        
        # Get average position
        positions = [r.get("position_ratio", 1) for q in ai_queries for r in q.get("responses", []) if r.get("ai_type") == ai_name and r.get("brand_mentioned")]
        avg_position = round(sum(positions) / len(positions) * 5, 1) if positions else 5.0
        
        ai_engines[ai_name] = {
            "score": round(score),
            "position_avg": avg_position,
            "mention_rate": mention_rate,
            "trend": "stable"  # Would need historical data for real trend
        }
    
    # Position distribution
    positions = {"first": 0, "second": 0, "third": 0, "other": 0, "absent": 0}
    for query in query_scores:
        for resp in query.get("responses", []):
            if not resp.get("brand_mentioned"):
                positions["absent"] += 1
            else:
                pos_ratio = resp.get("position_ratio", 1)
                if pos_ratio < 0.15:
                    positions["first"] += 1
                elif pos_ratio < 0.30:
                    positions["second"] += 1
                elif pos_ratio < 0.50:
                    positions["third"] += 1
                else:
                    positions["other"] += 1
    
    total_responses = sum(positions.values())
    if total_responses > 0:
        for key in positions:
            positions[key] = round(positions[key] / total_responses * 100)
    
    # Thematic visibility (by query type)
    query_type_breakdown = latest_analysis.get("query_type_breakdown", {})
    thematic_visibility = []
    for qtype, data in query_type_breakdown.items():
        thematic_visibility.append({
            "theme": qtype,
            "score": round(data.get("avg_score", 0)),
            "frequency": data.get("count", 0)
        })
    
    # Recent queries
    recent_queries = []
    for query in query_scores[:10]:
        for resp in query.get("responses", [])[:1]:  # First response only
            recent_queries.append({
                "query": query.get("query_text", "")[:100],
                "mentioned": resp.get("brand_mentioned", False),
                "position": 1 if resp.get("position_ratio", 1) < 0.15 else (2 if resp.get("position_ratio", 1) < 0.30 else 3),
                "ai": resp.get("ai_type", "unknown")
            })
    
    return {
        "global_visibility_score": round(latest_analysis.get("global_score", 0)),
        "ai_engines": ai_engines,
        "position_distribution": positions,
        "thematic_visibility": thematic_visibility,
        "recent_queries": recent_queries,
        "has_data": True,
        "last_analysis_date": latest_analysis.get("created_at")
    }


# ================== CONTENT AUDIT ==================

@api_router.get("/content-audit/{project_id}")
async def get_content_audit(project_id: str, user: dict = Depends(get_current_user)):
    """Get content audit data for a project"""
    # Verify project belongs to user
    project = await db.projects.find_one(
        {"project_id": project_id, "user_id": user["user_id"]},
        {"_id": 0}
    )
    if not project:
        raise HTTPException(status_code=404, detail="Projet non trouve")
    
    # Get latest completed analysis
    latest_analysis = await db.analyses.find_one(
        {"project_id": project_id, "status": "completed"},
        {"_id": 0},
        sort=[("created_at", -1)]
    )
    
    if not latest_analysis:
        return {
            "global_citability_score": 0,
            "pages_analyzed": 0,
            "structure_score": 0,
            "content_gaps": 0,
            "schema_coverage": 0,
            "pages": [],
            "gaps": [],
            "structure_recommendations": [],
            "has_data": False
        }
    
    # Calculate citability from analysis data
    rate_score = latest_analysis.get("rate_score", {})
    indices = latest_analysis.get("indices", {})
    recommendations = latest_analysis.get("recommendations", [])
    
    # Global citability = average of relevance and authority
    relevance = rate_score.get("relevance", 0)
    authority = rate_score.get("authority", 0)
    global_citability = round((relevance + authority) / 2)
    
    # Structure score from truthfulness (format/structure matters for LLMs)
    structure_score = round(rate_score.get("truthfulness", 0) * 0.8 + rate_score.get("endorsement", 0) * 0.2)
    
    # Schema coverage (estimated from credibility factors in responses)
    query_scores = latest_analysis.get("query_scores", [])
    schema_signals = 0
    total_checks = 0
    for query in query_scores:
        for resp in query.get("responses", []):
            total_checks += 1
            cred_factors = resp.get("credibility_factors", [])
            if "facts" in cred_factors or "sources" in cred_factors:
                schema_signals += 1
    schema_coverage = round(schema_signals / total_checks * 100) if total_checks > 0 else 0
    
    # Content gaps from recommendations
    gaps = []
    for rec in recommendations[:5]:
        if rec.get("priority") in ["critical", "high", "medium"]:
            gaps.append({
                "topic": rec.get("title", ""),
                "priority": "high" if rec.get("priority") == "critical" else rec.get("priority", "medium"),
                "potential_impact": 20 if rec.get("impact") == "critique" else (15 if rec.get("impact") == "eleve" else 10)
            })
    
    # Simulated page analysis based on project keywords
    pages = []
    keywords = project.get("keywords", [])
    for i, kw in enumerate(keywords[:4]):
        score = max(30, min(90, global_citability + (i * 5) - 10))
        pages.append({
            "url": f"/{kw.lower().replace(' ', '-')}",
            "title": f"Page {kw}",
            "citability_score": score,
            "structure_score": score - 5,
            "has_schema": i < 2,
            "content_length": 1500 + i * 500,
            "headings_count": 8 + i * 2,
            "lists_count": 3 + i,
            "issues": ["Ajouter FAQ", "Optimiser structure"] if score < 60 else [],
            "strengths": ["Bonne structure"] if score >= 60 else []
        })
    
    # Structure recommendations
    structure_recommendations = [
        {"type": "schema", "title": "Ajouter Schema.org Product", "pages": 3},
        {"type": "faq", "title": "Ajouter section FAQ", "pages": 4},
        {"type": "heading", "title": "Ameliorer structure des titres", "pages": 2},
        {"type": "list", "title": "Ajouter listes a puces", "pages": 3}
    ]
    
    return {
        "global_citability_score": global_citability,
        "pages_analyzed": len(pages),
        "structure_score": structure_score,
        "content_gaps": len(gaps),
        "schema_coverage": schema_coverage,
        "pages": pages,
        "gaps": gaps,
        "structure_recommendations": structure_recommendations,
        "has_data": True
    }


# ================== GENERAL ROUTES ==================


# ================== CONTENT GENERATION ==================

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

@api_router.post("/content/generate")
async def generate_geo_content(request: ContentGenerateRequest, user: dict = Depends(get_current_user)):
    """Generate GEO-optimized content using AI"""
    
    content_prompts = {
        "article": f"""Genere un article de blog optimise pour le GEO (Generative Engine Optimization) sur le sujet: "{request.topic}"
        
Marque a mettre en avant: {request.brand_name or 'la marque'}
Mots-cles a integrer: {', '.join(request.keywords) if request.keywords else 'aucun specifie'}

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

        "faq": f"""Genere une FAQ optimisee GEO (Generative Engine Optimization) sur le sujet: "{request.topic}"

Marque concernee: {request.brand_name or 'la marque'}
Mots-cles: {', '.join(request.keywords) if request.keywords else 'aucun specifie'}

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

        "entity": f"""Genere une fiche d'entite optimisee GEO pour: "{request.topic}"

Marque/Entite: {request.brand_name or request.topic}

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

        "guide": f"""Genere un guide definitif et exhaustif optimise GEO sur: "{request.topic}"

Marque a integrer: {request.brand_name or 'la marque'}
Mots-cles: {', '.join(request.keywords) if request.keywords else 'aucun specifie'}

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

        "comparison": f"""Genere un comparatif structure et optimise GEO sur: "{request.topic}"

Marque a mettre en avant: {request.brand_name or 'la marque'}
Mots-cles: {', '.join(request.keywords) if request.keywords else 'aucun specifie'}

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

    prompt = content_prompts.get(request.content_type, content_prompts["article"])
    
    try:
        # Use Emergent LLM Key for generation
        loop = asyncio.get_event_loop()
        generated_text = await loop.run_in_executor(
            llm_executor,
            lambda: call_llm_for_content(prompt)
        )
        
        # Calculate word count
        word_count = len(generated_text.split())
        
        # Generate tips based on content type
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
        
        return {
            "content": generated_text,
            "content_type": request.content_type,
            "topic": request.topic,
            "word_count": word_count,
            "geo_score": min(95, 75 + len(request.keywords) * 2),
            "tips": tips.get(request.content_type, []),
            "generated_at": datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as e:
        print(f"Content generation error: {e}")
        raise HTTPException(status_code=500, detail=f"Erreur de generation: {str(e)}")


@api_router.post("/content/reformulate")
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
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            llm_executor,
            lambda: call_llm_for_content(prompt)
        )
        
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
        print(f"Reformulation error: {e}")
        raise HTTPException(status_code=500, detail=f"Erreur d'optimisation: {str(e)}")


def call_llm_for_content(prompt: str) -> str:
    """Call LLM for content generation using Emergent LLM Key - synchronous wrapper"""
    import asyncio
    
    async def _async_call():
        try:
            from app.services.llm_abstraction import LlmChat, UserMessage
            import uuid
            
            # Initialize chat with system message for GEO content
            chat = LlmChat(
                api_key=EMERGENT_LLM_KEY,
                session_id=f"geo-content-{uuid.uuid4().hex[:8]}",
                system_message="Tu es un expert en content marketing et GEO (Generative Engine Optimization). Tu crees du contenu optimise pour etre cite par les LLMs comme ChatGPT, Claude, Gemini. Reponds toujours en francais avec un contenu riche, structure et factuel. Utilise le format Markdown."
            )
            
            # Use GPT-4o for content generation
            chat = chat.with_model("openai", "gpt-4o")
            
            # Create user message
            user_message = UserMessage(text=prompt)
            
            # Send message and get response
            response = await chat.send_message(user_message)
            return response
            
        except Exception as e:
            print(f"LLM async call error: {e}")
            import traceback
            traceback.print_exc()
            raise e
    
    try:
        # Run the async function in the current event loop or create new one
        try:
            loop = asyncio.get_running_loop()
            # If we're already in an async context, we need to run in thread
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as pool:
                future = pool.submit(asyncio.run, _async_call())
                return future.result(timeout=120)
        except RuntimeError:
            # No running loop, create new one
            return asyncio.run(_async_call())
            
    except Exception as e:
        print(f"LLM call error: {e}")
        # Fallback response
        return f"""# Contenu genere pour: {prompt[:50]}...

## Introduction
Ce contenu a ete genere pour optimiser votre visibilite dans les moteurs IA generatifs.

## Points Cles
- Contenu structure pour les LLMs
- Donnees factuelles et verifiables
- Format optimise E-E-A-T

## Conclusion
Pour un meilleur resultat, assurez-vous que votre budget LLM Emergent est suffisant.

*Note: Generation de secours - verifiez votre cle API Emergent*"""

# ================== CONTACT ENDPOINT ==================

class ContactForm(BaseModel):
    name: str
    email: EmailStr
    company: Optional[str] = None
    subject: str
    message: str

@api_router.post("/contact")
async def send_contact_message(form: ContactForm):
    """Handle contact form submission"""
    try:
        # Store contact message in database
        contact_doc = {
            "contact_id": f"contact_{uuid.uuid4().hex[:12]}",
            "name": form.name,
            "email": form.email,
            "company": form.company,
            "subject": form.subject,
            "message": form.message,
            "status": "new",
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        await db.contact_messages.insert_one(contact_doc)
        
        # Send notification email to admin
        if RESEND_API_KEY:
            subject_labels = {
                "demo": "Demande de démo",
                "pricing": "Question tarifs",
                "support": "Support technique",
                "partnership": "Partenariat",
                "other": "Autre"
            }
            subject_label = subject_labels.get(form.subject, form.subject)
            
            try:
                params = {
                    "from": "IAskan Contact <noreply@resend.dev>",
                    "to": ["contact@iaskan.com"],  # Admin email
                    "reply_to": form.email,
                    "subject": f"[IAskan Contact] {subject_label} - {form.name}",
                    "html": f"""
                    <h2>Nouveau message de contact</h2>
                    <p><strong>Nom:</strong> {form.name}</p>
                    <p><strong>Email:</strong> {form.email}</p>
                    <p><strong>Entreprise:</strong> {form.company or 'Non renseigné'}</p>
                    <p><strong>Sujet:</strong> {subject_label}</p>
                    <hr>
                    <h3>Message:</h3>
                    <p>{form.message}</p>
                    """
                }
                await asyncio.to_thread(resend.Emails.send, params)
                logger.info(f"Contact email sent for {form.email}")
            except Exception as e:
                logger.error(f"Failed to send contact email: {e}")
        
        return {"success": True, "message": "Message reçu"}
        
    except Exception as e:
        logger.error(f"Contact form error: {e}")
        raise HTTPException(status_code=500, detail="Erreur lors de l'envoi du message")

@api_router.get("/")
async def root():
    return {"message": "IAskan API v1.0", "status": "healthy"}

@api_router.get("/health")
async def health():
    return {"status": "healthy", "timestamp": datetime.now(timezone.utc).isoformat()}

# Include router
app.include_router(api_router)

# Include modular routers
# Core routers (migrated from server.py)
app.include_router(auth_router.router)         # Authentication endpoints
app.include_router(projects_router.router)     # Project CRUD endpoints
app.include_router(dashboard_router.router)    # Dashboard stats endpoints
app.include_router(notifications_router.router) # Notifications endpoints
app.include_router(schedules_router.router)    # Scheduled scans endpoints
app.include_router(subscriptions_router.router) # Subscription & payment endpoints

# Feature routers
app.include_router(organizations.router)       # Organizations/workspaces management
app.include_router(article_optimizer.router)   # Article optimization feature
app.include_router(admin.router)               # Admin backoffice
app.include_router(onboarding.router)          # User onboarding flow
app.include_router(analysis_router.router)     # Celery-powered analysis pipeline
app.include_router(analyses_router.router)     # Analyses listing (frontend compatibility)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    """Start background tasks on application startup"""
    # Initialize PostgreSQL database
    if USE_POSTGRES:
        try:
            await initialize_database()
            logger.info("PostgreSQL database initialized successfully")
        except Exception as e:
            logger.error(f"PostgreSQL initialization error: {e}")
    
    # Start scheduled scans checker
    asyncio.create_task(check_scheduled_scans())
    logger.info("Scheduled scans background task started")

@app.on_event("shutdown")
async def shutdown_db_client():
    """Cleanup on application shutdown"""
    # Close MongoDB connection if configured
    if client:
        client.close()
    
    # Close PostgreSQL connections
    if USE_POSTGRES:
        await shutdown_database()
        logger.info("PostgreSQL connections closed")
