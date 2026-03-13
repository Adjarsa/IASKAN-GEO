"""
IAskan Configuration Module
Central configuration for all environment variables and settings
"""
import os
from pathlib import Path
from dotenv import load_dotenv

ROOT_DIR = Path(__file__).parent.parent.parent
load_dotenv(ROOT_DIR / '.env')

# Database - PostgreSQL (primary) and MongoDB (legacy)
DATABASE_URL = os.environ.get('DATABASE_URL', 'postgresql://iaskan_user:iaskan_secure_password_2024@localhost:5432/iaskan')
USE_POSTGRES = os.environ.get('USE_POSTGRES', 'true').lower() == 'true'
MONGO_URL = os.environ.get('MONGO_URL')
DB_NAME = os.environ.get('DB_NAME', 'iaskan')

# Supabase (for production)
SUPABASE_URL = os.environ.get('SUPABASE_URL', '')
SUPABASE_ANON_KEY = os.environ.get('SUPABASE_ANON_KEY', '')

# API Keys
EMERGENT_LLM_KEY = os.environ.get('EMERGENT_LLM_KEY')
STRIPE_API_KEY = os.environ.get('STRIPE_API_KEY')
RESEND_API_KEY = os.environ.get('RESEND_API_KEY', '')

# OAuth
GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID', '')
GOOGLE_CLIENT_SECRET = os.environ.get('GOOGLE_CLIENT_SECRET', '')
MICROSOFT_CLIENT_ID = os.environ.get('MICROSOFT_CLIENT_ID', '')
MICROSOFT_CLIENT_SECRET = os.environ.get('MICROSOFT_CLIENT_SECRET', '')
LINKEDIN_CLIENT_ID = os.environ.get('LINKEDIN_CLIENT_ID', '')
LINKEDIN_CLIENT_SECRET = os.environ.get('LINKEDIN_CLIENT_SECRET', '')

# Email
SENDER_EMAIL = os.environ.get('SENDER_EMAIL', 'noreply@iaskan.com')
FRONTEND_URL = os.environ.get('FRONTEND_URL', 'https://iaskan-preview-1.preview.emergentagent.com')

# CORS
CORS_ORIGINS = os.environ.get('CORS_ORIGINS', '*').split(',')

# Subscription Plans Configuration
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
        "article_optimizer_limit": 0
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
        "features": ["10 scans/mois", "50 prompts/scan", "150 requêtes/scan", "1 500 requêtes/mois", "ChatGPT uniquement", "Rapport standard", "Support email"],
        "article_optimizer": True,
        "article_optimizer_limit": 5
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
        "features": ["50 scans/mois", "100 prompts/scan", "4 runs/requête", "1 600 requêtes/scan", "80 000 requêtes/mois", "4 IA", "Benchmark concurrents", "Analyse de stabilité", "Scans programmés + rapport par email", "5 projets", "Support prioritaire"],
        "article_optimizer": True,
        "article_optimizer_limit": 30
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
        "features": ["150 scans/mois", "200 prompts/scan", "5 runs/requête", "4 000 requêtes/scan", "600 000 requêtes/mois", "4 IA", "Génération d'articles GEO", "Intelligence stratégique", "Scans programmés + rapport par email", "Projets illimités", "Support dédié"],
        "article_optimizer": True,
        "article_optimizer_limit": -1  # Unlimited
    }
}

# Blocked temporary email domains
BLOCKED_EMAIL_DOMAINS = {
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
