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
import io
import secrets
from fpdf import FPDF
from authlib.integrations.starlette_client import OAuth
from emergentintegrations.llm.chat import LlmChat, UserMessage
from emergentintegrations.payments.stripe.checkout import StripeCheckout, CheckoutSessionResponse, CheckoutStatusResponse, CheckoutSessionRequest
import resend

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

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
    competitors: List[str] = []
    keywords: List[str] = []
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class Analysis(BaseModel):
    model_config = ConfigDict(extra="ignore")
    analysis_id: str = Field(default_factory=lambda: f"ana_{uuid.uuid4().hex[:12]}")
    project_id: str
    user_id: str
    status: str = "pending"  # pending, running, completed, failed
    global_score: float = 0.0
    rate_score: Dict[str, float] = {}  # R.A.T.E scores
    ai_scores: Dict[str, float] = {}  # Score per AI
    query_scores: List[Dict[str, Any]] = []
    recommendations: List[Dict[str, Any]] = []
    competitor_comparison: List[Dict[str, Any]] = []
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
    current_period_end: datetime = Field(default_factory=lambda: datetime.now(timezone.utc) + timedelta(days=30))
    stripe_subscription_id: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

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
    "starter": {
        "name": "Starter",
        "price": 79.00,
        "queries_limit": 300,
        "free_scans": 1,
        "projects_limit": 1,
        "ai_engines": ["chatgpt"],
        "features": ["1 scan gratuit", "Score GEO basique", "ChatGPT uniquement", "Rapport standard", "1 projet", "Support email"]
    },
    "pro": {
        "name": "Pro",
        "price": 149.00,
        "queries_limit": 600,
        "free_scans": 0,
        "projects_limit": 5,
        "ai_engines": ["chatgpt", "claude", "gemini", "perplexity"],
        "features": ["Score GEO avancé", "Multi-IA (4 moteurs)", "Benchmark concurrents", "Analyse de stabilité", "5 projets", "Support prioritaire"]
    },
    "business": {
        "name": "Business",
        "price": 349.00,
        "queries_limit": 1500,
        "free_scans": 0,
        "projects_limit": -1,
        "ai_engines": ["chatgpt", "claude", "gemini", "perplexity"],
        "features": ["Score GEO complet", "Toutes les IA", "Génération d'articles GEO", "Intelligence stratégique", "Projets illimités", "API access", "Support dédié"]
    }
}

# ================== AUTH HELPERS ==================

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

# ================== AUTH ROUTES ==================

@api_router.post("/auth/session")
async def create_session(request: Request, response: Response):
    """Exchange session_id from Emergent Auth for session_token"""
    body = await request.json()
    session_id = body.get("session_id")
    
    if not session_id:
        raise HTTPException(status_code=400, detail="session_id requis")
    
    # Call Emergent Auth to get user data
    # REMINDER: DO NOT HARDCODE THE URL, OR ADD ANY FALLBACKS OR REDIRECT URLS, THIS BREAKS THE AUTH
    async with httpx.AsyncClient() as client:
        auth_response = await client.get(
            "https://demobackend.emergentagent.com/auth/v1/env/oauth/session-data",
            headers={"X-Session-ID": session_id}
        )
        
        if auth_response.status_code != 200:
            raise HTTPException(status_code=401, detail="Session invalide")
        
        auth_data = auth_response.json()
    
    user_id = f"user_{uuid.uuid4().hex[:12]}"
    email = auth_data.get("email")
    name = auth_data.get("name")
    picture = auth_data.get("picture")
    session_token = auth_data.get("session_token")
    
    # Check if user exists
    existing_user = await db.users.find_one({"email": email}, {"_id": 0})
    if existing_user:
        user_id = existing_user["user_id"]
    else:
        # Create new user
        user_doc = {
            "user_id": user_id,
            "email": email,
            "name": name,
            "picture": picture,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        await db.users.insert_one(user_doc)
        
        # Create free subscription with 1 free scan
        free_sub = {
            "subscription_id": f"sub_{uuid.uuid4().hex[:12]}",
            "user_id": user_id,
            "plan": "free",
            "status": "active",
            "queries_limit": 1,
            "queries_used": 0,
            "free_scans_remaining": 1,
            "current_period_start": datetime.now(timezone.utc).isoformat(),
            "current_period_end": None,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        await db.subscriptions.insert_one(free_sub)
    
    # Create session
    expires_at = datetime.now(timezone.utc) + timedelta(days=30)
    session_doc = {
        "session_id": str(uuid.uuid4()),
        "user_id": user_id,
        "session_token": session_token,
        "expires_at": expires_at.isoformat(),
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.user_sessions.insert_one(session_doc)
    
    # Set cookie
    response.set_cookie(
        key="session_token",
        value=session_token,
        httponly=True,
        secure=True,
        samesite="none",
        path="/",
        max_age=7 * 24 * 60 * 60  # 7 days
    )
    
    user = await db.users.find_one({"user_id": user_id}, {"_id": 0})
    return {"user": user, "session_token": session_token}

@api_router.get("/auth/me")
async def get_me(user: dict = Depends(get_current_user)):
    """Get current authenticated user"""
    # Get subscription info
    subscription = await db.subscriptions.find_one({"user_id": user["user_id"]}, {"_id": 0})
    return {"user": user, "subscription": subscription}

@api_router.post("/auth/logout")
async def logout(request: Request, response: Response):
    """Logout user and clear session"""
    token = request.cookies.get("session_token")
    if token:
        await db.user_sessions.delete_many({"session_token": token})
    
    response.delete_cookie("session_token", path="/")
    return {"message": "Déconnexion réussie"}

# ================== MICROSOFT & LINKEDIN OAUTH ==================

async def create_oauth_user_session(email: str, name: str, picture: str, provider: str, response: Response):
    """Helper function to create user session for OAuth providers"""
    user_id = f"user_{uuid.uuid4().hex[:12]}"
    
    # Check if user exists
    existing_user = await db.users.find_one({"email": email}, {"_id": 0})
    is_new_user = False
    if existing_user:
        user_id = existing_user["user_id"]
    else:
        is_new_user = True
        # Create new user
        user_doc = {
            "user_id": user_id,
            "email": email,
            "name": name,
            "picture": picture,
            "auth_provider": provider,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        await db.users.insert_one(user_doc)
        
        # Create trial subscription
        trial_sub = {
            "subscription_id": f"sub_{uuid.uuid4().hex[:12]}",
            "user_id": user_id,
            "plan": "starter",
            "status": "trial",
            "queries_limit": 300,
            "queries_used": 0,
            "trial_ends_at": (datetime.now(timezone.utc) + timedelta(days=7)).isoformat(),
            "current_period_start": datetime.now(timezone.utc).isoformat(),
            "current_period_end": (datetime.now(timezone.utc) + timedelta(days=7)).isoformat(),
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        await db.subscriptions.insert_one(trial_sub)
    
    # Create session
    session_token = f"sess_{uuid.uuid4().hex}"
    expires_at = datetime.now(timezone.utc) + timedelta(days=7)
    session_doc = {
        "session_id": str(uuid.uuid4()),
        "user_id": user_id,
        "session_token": session_token,
        "expires_at": expires_at.isoformat(),
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.user_sessions.insert_one(session_doc)
    
    # Set cookie
    response.set_cookie(
        key="session_token",
        value=session_token,
        httponly=True,
        secure=True,
        samesite="none",
        path="/",
        max_age=7 * 24 * 60 * 60
    )
    
    # Send welcome email for new users (non-blocking)
    if is_new_user and RESEND_API_KEY:
        frontend_url = "https://analyze-visibility.preview.emergentagent.com"
        asyncio.create_task(send_welcome_email(email, name, frontend_url))
    
    return user_id, session_token

@api_router.get("/auth/microsoft/login")
async def microsoft_login(request: Request):
    """Initiate Microsoft OAuth2 login"""
    if not MICROSOFT_CLIENT_ID or not MICROSOFT_CLIENT_SECRET:
        raise HTTPException(status_code=501, detail="Microsoft OAuth non configuré. Veuillez contacter l'administrateur.")
    
    # Get the frontend URL from referer or use default
    referer = request.headers.get("referer", "")
    frontend_url = referer.split("/login")[0] if "/login" in referer else request.headers.get("origin", "")
    
    state = secrets.token_urlsafe(32)
    request.session["oauth_state"] = state
    request.session["frontend_url"] = frontend_url
    
    redirect_uri = str(request.base_url) + "api/auth/microsoft/callback"
    
    auth_url = (
        f"https://login.microsoftonline.com/common/oauth2/v2.0/authorize?"
        f"client_id={MICROSOFT_CLIENT_ID}&"
        f"response_type=code&"
        f"redirect_uri={redirect_uri}&"
        f"scope=openid profile email&"
        f"state={state}&"
        f"response_mode=query"
    )
    
    return RedirectResponse(url=auth_url)

@api_router.get("/auth/microsoft/callback")
async def microsoft_callback(request: Request, code: str = None, state: str = None, error: str = None):
    """Handle Microsoft OAuth2 callback"""
    frontend_url = request.session.get("frontend_url", "")
    
    if error:
        return RedirectResponse(url=f"{frontend_url}/login?error=microsoft_auth_failed")
    
    stored_state = request.session.get("oauth_state")
    if not stored_state or stored_state != state:
        return RedirectResponse(url=f"{frontend_url}/login?error=invalid_state")
    
    redirect_uri = str(request.base_url) + "api/auth/microsoft/callback"
    
    # Exchange code for token
    async with httpx.AsyncClient() as client:
        token_response = await client.post(
            "https://login.microsoftonline.com/common/oauth2/v2.0/token",
            data={
                "client_id": MICROSOFT_CLIENT_ID,
                "client_secret": MICROSOFT_CLIENT_SECRET,
                "code": code,
                "redirect_uri": redirect_uri,
                "grant_type": "authorization_code"
            }
        )
        
        if token_response.status_code != 200:
            logger.error(f"Microsoft token error: {token_response.text}")
            return RedirectResponse(url=f"{frontend_url}/login?error=token_exchange_failed")
        
        token_data = token_response.json()
        access_token = token_data.get("access_token")
        
        # Get user info
        user_response = await client.get(
            "https://graph.microsoft.com/v1.0/me",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        
        if user_response.status_code != 200:
            return RedirectResponse(url=f"{frontend_url}/login?error=user_info_failed")
        
        user_data = user_response.json()
    
    email = user_data.get("mail") or user_data.get("userPrincipalName")
    name = user_data.get("displayName")
    picture = None
    
    response = RedirectResponse(url=f"{frontend_url}/projects")
    await create_oauth_user_session(email, name, picture, "microsoft", response)
    
    return response

@api_router.get("/auth/linkedin/login")
async def linkedin_login(request: Request):
    """Initiate LinkedIn OAuth2 login"""
    if not LINKEDIN_CLIENT_ID or not LINKEDIN_CLIENT_SECRET:
        raise HTTPException(status_code=501, detail="LinkedIn OAuth non configuré. Veuillez contacter l'administrateur.")
    
    referer = request.headers.get("referer", "")
    frontend_url = referer.split("/login")[0] if "/login" in referer else request.headers.get("origin", "")
    
    state = secrets.token_urlsafe(32)
    request.session["oauth_state"] = state
    request.session["frontend_url"] = frontend_url
    
    redirect_uri = str(request.base_url) + "api/auth/linkedin/callback"
    
    auth_url = (
        f"https://www.linkedin.com/oauth/v2/authorization?"
        f"response_type=code&"
        f"client_id={LINKEDIN_CLIENT_ID}&"
        f"redirect_uri={redirect_uri}&"
        f"scope=openid profile email&"
        f"state={state}"
    )
    
    return RedirectResponse(url=auth_url)

@api_router.get("/auth/linkedin/callback")
async def linkedin_callback(request: Request, code: str = None, state: str = None, error: str = None):
    """Handle LinkedIn OAuth2 callback"""
    frontend_url = request.session.get("frontend_url", "")
    
    if error:
        return RedirectResponse(url=f"{frontend_url}/login?error=linkedin_auth_failed")
    
    stored_state = request.session.get("oauth_state")
    if not stored_state or stored_state != state:
        return RedirectResponse(url=f"{frontend_url}/login?error=invalid_state")
    
    redirect_uri = str(request.base_url) + "api/auth/linkedin/callback"
    
    # Exchange code for token
    async with httpx.AsyncClient() as client:
        token_response = await client.post(
            "https://www.linkedin.com/oauth/v2/accessToken",
            data={
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": redirect_uri,
                "client_id": LINKEDIN_CLIENT_ID,
                "client_secret": LINKEDIN_CLIENT_SECRET
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        
        if token_response.status_code != 200:
            logger.error(f"LinkedIn token error: {token_response.text}")
            return RedirectResponse(url=f"{frontend_url}/login?error=token_exchange_failed")
        
        token_data = token_response.json()
        access_token = token_data.get("access_token")
        
        # Get user info using OpenID Connect userinfo endpoint
        user_response = await client.get(
            "https://api.linkedin.com/v2/userinfo",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        
        if user_response.status_code != 200:
            return RedirectResponse(url=f"{frontend_url}/login?error=user_info_failed")
        
        user_data = user_response.json()
    
    email = user_data.get("email")
    name = user_data.get("name") or f"{user_data.get('given_name', '')} {user_data.get('family_name', '')}".strip()
    picture = user_data.get("picture")
    
    response = RedirectResponse(url=f"{frontend_url}/projects")
    await create_oauth_user_session(email, name, picture, "linkedin", response)
    
    return response

@api_router.get("/auth/providers")
async def get_auth_providers():
    """Get available authentication providers"""
    return {
        "providers": {
            "google": True,  # Always available via Emergent Auth
            "microsoft": bool(MICROSOFT_CLIENT_ID and MICROSOFT_CLIENT_SECRET),
            "linkedin": bool(LINKEDIN_CLIENT_ID and LINKEDIN_CLIENT_SECRET)
        }
    }

# ================== EMAIL SERVICE ==================

def get_email_template_welcome(name: str, login_url: str) -> str:
    """Generate welcome email HTML template"""
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
    </head>
    <body style="margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background-color: #f8fafc;">
        <table width="100%" cellpadding="0" cellspacing="0" style="background-color: #f8fafc; padding: 40px 20px;">
            <tr>
                <td align="center">
                    <table width="600" cellpadding="0" cellspacing="0" style="background-color: #ffffff; border-radius: 16px; overflow: hidden; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);">
                        <!-- Header -->
                        <tr>
                            <td style="background: linear-gradient(135deg, #7c3aed 0%, #06b6d4 100%); padding: 40px; text-align: center;">
                                <h1 style="color: #ffffff; font-size: 28px; margin: 0; font-weight: 700;">IAskan</h1>
                                <p style="color: rgba(255,255,255,0.9); margin: 10px 0 0 0; font-size: 14px;">Generative Engine Optimization</p>
                            </td>
                        </tr>
                        <!-- Content -->
                        <tr>
                            <td style="padding: 40px;">
                                <h2 style="color: #1e293b; font-size: 24px; margin: 0 0 20px 0;">Bienvenue {name} !</h2>
                                <p style="color: #64748b; font-size: 16px; line-height: 1.6; margin: 0 0 20px 0;">
                                    Merci de rejoindre IAskan ! Vous êtes maintenant prêt à analyser et optimiser 
                                    votre visibilité dans les réponses des intelligences artificielles.
                                </p>
                                <p style="color: #64748b; font-size: 16px; line-height: 1.6; margin: 0 0 30px 0;">
                                    Avec IAskan, vous pouvez :
                                </p>
                                <ul style="color: #64748b; font-size: 16px; line-height: 1.8; margin: 0 0 30px 20px; padding: 0;">
                                    <li>Analyser votre présence sur ChatGPT, Claude, Gemini et Perplexity</li>
                                    <li>Obtenir votre score R.A.T.E.™ détaillé</li>
                                    <li>Recevoir des recommandations personnalisées</li>
                                    <li>Télécharger des rapports PDF professionnels</li>
                                </ul>
                                <table cellpadding="0" cellspacing="0" style="margin: 0 auto;">
                                    <tr>
                                        <td style="background: linear-gradient(135deg, #7c3aed 0%, #06b6d4 100%); border-radius: 8px;">
                                            <a href="{login_url}" style="display: inline-block; padding: 14px 32px; color: #ffffff; text-decoration: none; font-weight: 600; font-size: 16px;">
                                                Accéder à mon dashboard
                                            </a>
                                        </td>
                                    </tr>
                                </table>
                            </td>
                        </tr>
                        <!-- Footer -->
                        <tr>
                            <td style="background-color: #f8fafc; padding: 30px; text-align: center; border-top: 1px solid #e2e8f0;">
                                <p style="color: #94a3b8; font-size: 14px; margin: 0;">
                                    © 2026 IAskan. Tous droits réservés.
                                </p>
                                <p style="color: #94a3b8; font-size: 12px; margin: 10px 0 0 0;">
                                    Vous recevez cet email car vous avez créé un compte sur IAskan.
                                </p>
                            </td>
                        </tr>
                    </table>
                </td>
            </tr>
        </table>
    </body>
    </html>
    """


def get_email_template_password_reset(name: str, reset_url: str, expires_in: str = "1 heure") -> str:
    """Generate password reset email HTML template"""
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
    </head>
    <body style="margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background-color: #f8fafc;">
        <table width="100%" cellpadding="0" cellspacing="0" style="background-color: #f8fafc; padding: 40px 20px;">
            <tr>
                <td align="center">
                    <table width="600" cellpadding="0" cellspacing="0" style="background-color: #ffffff; border-radius: 16px; overflow: hidden; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);">
                        <!-- Header -->
                        <tr>
                            <td style="background: linear-gradient(135deg, #7c3aed 0%, #06b6d4 100%); padding: 40px; text-align: center;">
                                <h1 style="color: #ffffff; font-size: 28px; margin: 0; font-weight: 700;">IAskan</h1>
                                <p style="color: rgba(255,255,255,0.9); margin: 10px 0 0 0; font-size: 14px;">Réinitialisation de mot de passe</p>
                            </td>
                        </tr>
                        <!-- Content -->
                        <tr>
                            <td style="padding: 40px;">
                                <h2 style="color: #1e293b; font-size: 24px; margin: 0 0 20px 0;">Bonjour {name},</h2>
                                <p style="color: #64748b; font-size: 16px; line-height: 1.6; margin: 0 0 20px 0;">
                                    Vous avez demandé à réinitialiser votre mot de passe. 
                                    Cliquez sur le bouton ci-dessous pour créer un nouveau mot de passe.
                                </p>
                                <table cellpadding="0" cellspacing="0" style="margin: 30px auto;">
                                    <tr>
                                        <td style="background: linear-gradient(135deg, #7c3aed 0%, #06b6d4 100%); border-radius: 8px;">
                                            <a href="{reset_url}" style="display: inline-block; padding: 14px 32px; color: #ffffff; text-decoration: none; font-weight: 600; font-size: 16px;">
                                                Réinitialiser mon mot de passe
                                            </a>
                                        </td>
                                    </tr>
                                </table>
                                <p style="color: #94a3b8; font-size: 14px; line-height: 1.6; margin: 30px 0 0 0; padding: 20px; background-color: #fef3c7; border-radius: 8px; border-left: 4px solid #f59e0b;">
                                    <strong style="color: #92400e;">Important :</strong> Ce lien expire dans {expires_in}. 
                                    Si vous n'avez pas demandé cette réinitialisation, ignorez cet email.
                                </p>
                            </td>
                        </tr>
                        <!-- Footer -->
                        <tr>
                            <td style="background-color: #f8fafc; padding: 30px; text-align: center; border-top: 1px solid #e2e8f0;">
                                <p style="color: #94a3b8; font-size: 14px; margin: 0;">
                                    © 2026 IAskan. Tous droits réservés.
                                </p>
                                <p style="color: #94a3b8; font-size: 12px; margin: 10px 0 0 0;">
                                    Pour des raisons de sécurité, ce lien n'est valide qu'une seule fois.
                                </p>
                            </td>
                        </tr>
                    </table>
                </td>
            </tr>
        </table>
    </body>
    </html>
    """


def get_email_template_magic_link(name: str, magic_link: str, expires_in: str = "15 minutes") -> str:
    """Generate magic link email HTML template"""
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
    </head>
    <body style="margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background-color: #f8fafc;">
        <table width="100%" cellpadding="0" cellspacing="0" style="background-color: #f8fafc; padding: 40px 20px;">
            <tr>
                <td align="center">
                    <table width="600" cellpadding="0" cellspacing="0" style="background-color: #ffffff; border-radius: 16px; overflow: hidden; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);">
                        <!-- Header -->
                        <tr>
                            <td style="background: linear-gradient(135deg, #7c3aed 0%, #06b6d4 100%); padding: 40px; text-align: center;">
                                <h1 style="color: #ffffff; font-size: 28px; margin: 0; font-weight: 700;">IAskan</h1>
                                <p style="color: rgba(255,255,255,0.9); margin: 10px 0 0 0; font-size: 14px;">Connexion sécurisée</p>
                            </td>
                        </tr>
                        <!-- Content -->
                        <tr>
                            <td style="padding: 40px;">
                                <h2 style="color: #1e293b; font-size: 24px; margin: 0 0 20px 0;">Bonjour {name},</h2>
                                <p style="color: #64748b; font-size: 16px; line-height: 1.6; margin: 0 0 20px 0;">
                                    Cliquez sur le bouton ci-dessous pour vous connecter à votre compte IAskan.
                                    Aucun mot de passe requis !
                                </p>
                                <table cellpadding="0" cellspacing="0" style="margin: 30px auto;">
                                    <tr>
                                        <td style="background: linear-gradient(135deg, #7c3aed 0%, #06b6d4 100%); border-radius: 8px;">
                                            <a href="{magic_link}" style="display: inline-block; padding: 14px 32px; color: #ffffff; text-decoration: none; font-weight: 600; font-size: 16px;">
                                                Se connecter à IAskan
                                            </a>
                                        </td>
                                    </tr>
                                </table>
                                <p style="color: #94a3b8; font-size: 14px; line-height: 1.6; margin: 30px 0 0 0; text-align: center;">
                                    Ce lien expire dans {expires_in} et ne peut être utilisé qu'une seule fois.
                                </p>
                            </td>
                        </tr>
                        <!-- Footer -->
                        <tr>
                            <td style="background-color: #f8fafc; padding: 30px; text-align: center; border-top: 1px solid #e2e8f0;">
                                <p style="color: #94a3b8; font-size: 14px; margin: 0;">
                                    © 2026 IAskan. Tous droits réservés.
                                </p>
                                <p style="color: #94a3b8; font-size: 12px; margin: 10px 0 0 0;">
                                    Si vous n'avez pas demandé ce lien, ignorez cet email.
                                </p>
                            </td>
                        </tr>
                    </table>
                </td>
            </tr>
        </table>
    </body>
    </html>
    """


async def send_email_async(to_email: str, subject: str, html_content: str) -> dict:
    """Send email using Resend API (non-blocking)"""
    if not RESEND_API_KEY:
        logger.warning(f"Email not sent (no API key): {subject} to {to_email}")
        return {"status": "skipped", "reason": "No Resend API key configured"}
    
    params = {
        "from": SENDER_EMAIL,
        "to": [to_email],
        "subject": subject,
        "html": html_content
    }
    
    try:
        email = await asyncio.to_thread(resend.Emails.send, params)
        logger.info(f"Email sent: {subject} to {to_email}")
        return {"status": "success", "email_id": email.get("id")}
    except Exception as e:
        logger.error(f"Failed to send email: {str(e)}")
        return {"status": "error", "error": str(e)}


async def send_welcome_email(email: str, name: str, frontend_url: str):
    """Send welcome email to new user"""
    login_url = f"{frontend_url}/login"
    html = get_email_template_welcome(name or "cher utilisateur", login_url)
    return await send_email_async(email, "Bienvenue sur IAskan ! 🚀", html)


async def send_password_reset_email(email: str, name: str, reset_token: str, frontend_url: str):
    """Send password reset email"""
    reset_url = f"{frontend_url}/reset-password?token={reset_token}"
    html = get_email_template_password_reset(name or "cher utilisateur", reset_url)
    return await send_email_async(email, "Réinitialisation de votre mot de passe IAskan", html)


async def send_magic_link_email(email: str, name: str, magic_token: str, frontend_url: str):
    """Send magic link login email"""
    magic_link = f"{frontend_url}/auth/magic?token={magic_token}"
    html = get_email_template_magic_link(name or "cher utilisateur", magic_link)
    return await send_email_async(email, "Votre lien de connexion IAskan", html)


# Pydantic models for email endpoints
class PasswordResetRequest(BaseModel):
    email: EmailStr

class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str

class MagicLinkRequest(BaseModel):
    email: EmailStr


@api_router.post("/auth/forgot-password")
async def forgot_password(request: Request, body: PasswordResetRequest):
    """Request password reset email"""
    # Find user
    user = await db.users.find_one({"email": body.email}, {"_id": 0})
    
    # Always return success to prevent email enumeration
    if not user:
        return {"message": "Si un compte existe avec cet email, vous recevrez un lien de réinitialisation."}
    
    # Generate reset token
    reset_token = secrets.token_urlsafe(32)
    expires_at = datetime.now(timezone.utc) + timedelta(hours=1)
    
    # Store reset token
    await db.password_resets.insert_one({
        "token": reset_token,
        "user_id": user["user_id"],
        "email": body.email,
        "expires_at": expires_at.isoformat(),
        "used": False,
        "created_at": datetime.now(timezone.utc).isoformat()
    })
    
    # Get frontend URL
    referer = request.headers.get("referer", "")
    frontend_url = referer.split("/")[0] + "//" + referer.split("/")[2] if "//" in referer else request.headers.get("origin", "")
    
    # Send email (non-blocking)
    asyncio.create_task(send_password_reset_email(
        body.email, 
        user.get("name", ""), 
        reset_token, 
        frontend_url
    ))
    
    return {"message": "Si un compte existe avec cet email, vous recevrez un lien de réinitialisation."}


@api_router.post("/auth/reset-password")
async def reset_password(body: PasswordResetConfirm):
    """Reset password with token"""
    import hashlib
    
    # Find valid reset token
    reset_doc = await db.password_resets.find_one({
        "token": body.token,
        "used": False
    }, {"_id": 0})
    
    if not reset_doc:
        raise HTTPException(status_code=400, detail="Lien de réinitialisation invalide ou expiré.")
    
    # Check expiration
    expires_at = datetime.fromisoformat(reset_doc["expires_at"].replace('Z', '+00:00'))
    if datetime.now(timezone.utc) > expires_at:
        raise HTTPException(status_code=400, detail="Ce lien a expiré. Veuillez demander un nouveau lien.")
    
    # Hash new password
    password_hash = hashlib.sha256(body.new_password.encode()).hexdigest()
    
    # Update user password
    await db.users.update_one(
        {"user_id": reset_doc["user_id"]},
        {"$set": {"password_hash": password_hash, "updated_at": datetime.now(timezone.utc).isoformat()}}
    )
    
    # Mark token as used
    await db.password_resets.update_one(
        {"token": body.token},
        {"$set": {"used": True}}
    )
    
    # Invalidate all existing sessions
    await db.user_sessions.delete_many({"user_id": reset_doc["user_id"]})
    
    return {"message": "Mot de passe mis à jour avec succès. Vous pouvez maintenant vous connecter."}


@api_router.post("/auth/magic-link")
async def request_magic_link(request: Request, body: MagicLinkRequest):
    """Request magic link login email"""
    # Find or create user
    user = await db.users.find_one({"email": body.email}, {"_id": 0})
    
    if not user:
        # Create new user
        user_id = f"user_{uuid.uuid4().hex[:12]}"
        user = {
            "user_id": user_id,
            "email": body.email,
            "name": body.email.split("@")[0],
            "auth_provider": "magic_link",
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        await db.users.insert_one(user)
        
        # Create trial subscription
        trial_sub = {
            "subscription_id": f"sub_{uuid.uuid4().hex[:12]}",
            "user_id": user_id,
            "plan": "starter",
            "status": "trial",
            "queries_limit": 300,
            "queries_used": 0,
            "trial_ends_at": (datetime.now(timezone.utc) + timedelta(days=7)).isoformat(),
            "current_period_start": datetime.now(timezone.utc).isoformat(),
            "current_period_end": (datetime.now(timezone.utc) + timedelta(days=7)).isoformat(),
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        await db.subscriptions.insert_one(trial_sub)
    
    # Generate magic token
    magic_token = secrets.token_urlsafe(32)
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=15)
    
    # Store magic token
    await db.magic_links.insert_one({
        "token": magic_token,
        "user_id": user["user_id"],
        "email": body.email,
        "expires_at": expires_at.isoformat(),
        "used": False,
        "created_at": datetime.now(timezone.utc).isoformat()
    })
    
    # Get frontend URL
    referer = request.headers.get("referer", "")
    frontend_url = referer.split("/")[0] + "//" + referer.split("/")[2] if "//" in referer else request.headers.get("origin", "")
    
    # Send email
    asyncio.create_task(send_magic_link_email(
        body.email,
        user.get("name", ""),
        magic_token,
        frontend_url
    ))
    
    return {"message": "Un lien de connexion a été envoyé à votre adresse email."}


@api_router.get("/auth/magic-verify")
async def verify_magic_link(token: str, response: Response):
    """Verify magic link and create session"""
    # Find valid magic token
    magic_doc = await db.magic_links.find_one({
        "token": token,
        "used": False
    }, {"_id": 0})
    
    if not magic_doc:
        raise HTTPException(status_code=400, detail="Lien de connexion invalide ou déjà utilisé.")
    
    # Check expiration
    expires_at = datetime.fromisoformat(magic_doc["expires_at"].replace('Z', '+00:00'))
    if datetime.now(timezone.utc) > expires_at:
        raise HTTPException(status_code=400, detail="Ce lien a expiré. Veuillez demander un nouveau lien.")
    
    # Mark token as used
    await db.magic_links.update_one(
        {"token": token},
        {"$set": {"used": True}}
    )
    
    # Get user
    user = await db.users.find_one({"user_id": magic_doc["user_id"]}, {"_id": 0})
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur non trouvé.")
    
    # Create session
    session_token = f"sess_{uuid.uuid4().hex}"
    expires_at = datetime.now(timezone.utc) + timedelta(days=7)
    session_doc = {
        "session_id": str(uuid.uuid4()),
        "user_id": user["user_id"],
        "session_token": session_token,
        "expires_at": expires_at.isoformat(),
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.user_sessions.insert_one(session_doc)
    
    # Set cookie
    response.set_cookie(
        key="session_token",
        value=session_token,
        httponly=True,
        secure=True,
        samesite="none",
        path="/",
        max_age=7 * 24 * 60 * 60
    )
    
    return {"message": "Connexion réussie", "user": user}

# ================== PROJECT ROUTES ==================

@api_router.post("/projects")
async def create_project(request: Request, user: dict = Depends(get_current_user)):
    """Create a new project"""
    body = await request.json()
    
    project = Project(
        user_id=user["user_id"],
        name=body.get("name", "Mon projet"),
        website_url=body.get("website_url", ""),
        brand_name=body.get("brand_name", ""),
        competitors=body.get("competitors", []),
        keywords=body.get("keywords", [])
    )
    
    doc = project.model_dump()
    doc["created_at"] = doc["created_at"].isoformat()
    await db.projects.insert_one(doc)
    
    # Return project without MongoDB _id
    project_data = await db.projects.find_one({"project_id": doc["project_id"]}, {"_id": 0})
    return {"project": project_data}

@api_router.get("/projects")
async def get_projects(user: dict = Depends(get_current_user)):
    """Get all projects for user"""
    projects = await db.projects.find({"user_id": user["user_id"]}, {"_id": 0}).to_list(100)
    return {"projects": projects}

@api_router.get("/projects/{project_id}")
async def get_project(project_id: str, user: dict = Depends(get_current_user)):
    """Get single project"""
    project = await db.projects.find_one(
        {"project_id": project_id, "user_id": user["user_id"]},
        {"_id": 0}
    )
    if not project:
        raise HTTPException(status_code=404, detail="Projet non trouvé")
    return {"project": project}

@api_router.put("/projects/{project_id}")
async def update_project(project_id: str, request: Request, user: dict = Depends(get_current_user)):
    """Update project"""
    body = await request.json()
    
    result = await db.projects.update_one(
        {"project_id": project_id, "user_id": user["user_id"]},
        {"$set": body}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Projet non trouvé")
    
    project = await db.projects.find_one({"project_id": project_id}, {"_id": 0})
    return {"project": project}

@api_router.delete("/projects/{project_id}")
async def delete_project(project_id: str, user: dict = Depends(get_current_user)):
    """Delete project"""
    result = await db.projects.delete_one({"project_id": project_id, "user_id": user["user_id"]})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Projet non trouvé")
    return {"message": "Projet supprimé"}

# ================== GEO ANALYSIS ENGINE ==================

async def query_ai_engine(query_text: str, brand_name: str, ai_type: str) -> Dict[str, Any]:
    """Query a specific AI engine and analyze the response"""
    try:
        session_id = f"geo_{uuid.uuid4().hex[:8]}"
        
        system_message = f"""Tu es un assistant qui répond aux questions des utilisateurs de manière naturelle et informative.
Réponds à la question suivante de manière complète et objective, en mentionnant les marques ou entreprises pertinentes si applicable."""
        
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
            # Use OpenAI as fallback for perplexity simulation
            chat.with_model("openai", "gpt-4o")
        else:
            chat.with_model("openai", "gpt-5.2")
        
        user_message = UserMessage(text=query_text)
        response = await chat.send_message(user_message)
        
        # Analyze response for brand visibility
        response_lower = response.lower()
        brand_lower = brand_name.lower()
        
        # Check if brand is mentioned
        brand_mentioned = brand_lower in response_lower
        
        # Determine role
        role = "absent"
        role_weight = 0.0
        
        if brand_mentioned:
            # Check position
            first_mention = response_lower.find(brand_lower)
            total_len = len(response_lower)
            position_ratio = first_mention / total_len if total_len > 0 else 1
            
            if position_ratio < 0.2:
                role = "top_recommendation"
                role_weight = 1.0
            elif position_ratio < 0.5:
                role = "shortlist"
                role_weight = 0.85
            elif "recommend" in response_lower or "conseille" in response_lower:
                role = "comparison"
                role_weight = 0.65
            else:
                role = "mention"
                role_weight = 0.4
        
        # Count mentions
        mention_count = response_lower.count(brand_lower)
        
        return {
            "ai_type": ai_type,
            "response_text": response[:500],  # Truncate for storage
            "brand_mentioned": brand_mentioned,
            "role": role,
            "role_weight": role_weight,
            "mention_count": mention_count,
            "response_length": len(response),
            "analyzed_at": datetime.now(timezone.utc).isoformat()
        }
    except Exception as e:
        logger.error(f"Error querying {ai_type}: {e}")
        return {
            "ai_type": ai_type,
            "error": str(e),
            "brand_mentioned": False,
            "role": "error",
            "role_weight": 0.0,
            "mention_count": 0
        }

def calculate_rate_score(ai_responses: List[Dict[str, Any]]) -> Dict[str, float]:
    """Calculate R.A.T.E score from AI responses"""
    if not ai_responses:
        return {"relevance": 0, "authority": 0, "truthfulness": 0, "endorsement": 0, "total": 0}
    
    valid_responses = [r for r in ai_responses if r.get("role") != "error"]
    if not valid_responses:
        return {"relevance": 0, "authority": 0, "truthfulness": 0, "endorsement": 0, "total": 0}
    
    # Relevance: based on mention rate
    mentioned = sum(1 for r in valid_responses if r.get("brand_mentioned", False))
    relevance = (mentioned / len(valid_responses)) * 100
    
    # Authority: based on role weight
    authority = sum(r.get("role_weight", 0) for r in valid_responses) / len(valid_responses) * 100
    
    # Truthfulness: assume high if no errors
    truthfulness = 85.0  # Base score
    
    # Endorsement: based on top recommendations
    top_recs = sum(1 for r in valid_responses if r.get("role") == "top_recommendation")
    endorsement = (top_recs / len(valid_responses)) * 100
    
    total = (relevance * 0.35 + authority * 0.20 + truthfulness * 0.15 + endorsement * 0.30)
    
    return {
        "relevance": round(relevance, 1),
        "authority": round(authority, 1),
        "truthfulness": round(truthfulness, 1),
        "endorsement": round(endorsement, 1),
        "total": round(total, 1)
    }

def generate_recommendations(rate_score: Dict[str, float], ai_scores: Dict[str, float]) -> List[Dict[str, Any]]:
    """Generate actionable recommendations based on scores"""
    recommendations = []
    
    if rate_score.get("relevance", 0) < 50:
        recommendations.append({
            "priority": "high",
            "category": "visibility",
            "title": "Améliorer la visibilité de marque",
            "description": "Votre marque n'apparaît pas suffisamment dans les réponses IA. Créez plus de contenu mentionnant votre marque avec des cas d'usage concrets.",
            "impact": "élevé",
            "effort": "moyen"
        })
    
    if rate_score.get("authority", 0) < 60:
        recommendations.append({
            "priority": "high",
            "category": "authority",
            "title": "Renforcer l'autorité",
            "description": "Ajoutez des preuves de crédibilité : études de cas, témoignages, certifications, mentions presse.",
            "impact": "élevé",
            "effort": "faible"
        })
    
    if rate_score.get("endorsement", 0) < 40:
        recommendations.append({
            "priority": "medium",
            "category": "endorsement",
            "title": "Optimiser pour les recommandations",
            "description": "Créez du contenu comparatif où votre marque est positionnée comme solution de référence.",
            "impact": "élevé",
            "effort": "moyen"
        })
    
    # AI-specific recommendations
    for ai, score in ai_scores.items():
        if score < 30:
            recommendations.append({
                "priority": "medium",
                "category": "ai_specific",
                "title": f"Améliorer la visibilité sur {ai.capitalize()}",
                "description": f"Votre score sur {ai.capitalize()} est faible. Adaptez votre contenu aux préférences de ce moteur IA.",
                "impact": "moyen",
                "effort": "moyen"
            })
    
    # Add general recommendations
    recommendations.append({
        "priority": "low",
        "category": "content",
        "title": "Créer du contenu FAQ structuré",
        "description": "Les IAs privilégient le contenu structuré en questions-réponses. Ajoutez une section FAQ complète.",
        "impact": "moyen",
        "effort": "faible"
    })
    
    return recommendations[:10]  # Limit to 10 recommendations

@api_router.post("/analysis/start")
async def start_analysis(request: Request, user: dict = Depends(get_current_user)):
    """Start a new GEO analysis"""
    body = await request.json()
    project_id = body.get("project_id")
    
    # Check project exists
    project = await db.projects.find_one({"project_id": project_id, "user_id": user["user_id"]}, {"_id": 0})
    if not project:
        raise HTTPException(status_code=404, detail="Projet non trouvé")
    
    # Check subscription limits
    subscription = await db.subscriptions.find_one({"user_id": user["user_id"]}, {"_id": 0})
    if not subscription:
        raise HTTPException(status_code=403, detail="Abonnement requis")
    
    plan = subscription.get("plan", "starter")
    plan_config = SUBSCRIPTION_PLANS.get(plan, SUBSCRIPTION_PLANS["starter"])
    
    # Create analysis
    analysis = Analysis(
        project_id=project_id,
        user_id=user["user_id"],
        status="running"
    )
    
    doc = analysis.model_dump()
    doc["created_at"] = doc["created_at"].isoformat()
    await db.analyses.insert_one(doc)
    
    # Start analysis in background
    asyncio.create_task(run_analysis(doc["analysis_id"], project, plan_config["ai_engines"]))
    
    return {"analysis_id": doc["analysis_id"], "status": "running"}

async def run_analysis(analysis_id: str, project: dict, ai_engines: List[str]):
    """Run the actual GEO analysis"""
    try:
        brand_name = project.get("brand_name", "")
        keywords = project.get("keywords", [])
        
        # Generate queries
        queries = []
        base_queries = [
            f"Quel est le meilleur {keywords[0] if keywords else 'service'} ?",
            f"Je cherche un {keywords[0] if keywords else 'service'}, que recommandez-vous ?",
            f"Comparaison des meilleurs {keywords[0] if keywords else 'services'}",
            f"Avis sur {brand_name}",
            f"{brand_name} vs concurrents"
        ]
        
        if keywords:
            for kw in keywords[:3]:
                base_queries.extend([
                    f"Meilleur {kw} en 2025",
                    f"Comment choisir un {kw} ?",
                    f"Top {kw} recommandés"
                ])
        
        all_ai_responses = []
        ai_scores = {ai: [] for ai in ai_engines}
        query_results = []
        
        for query_text in base_queries[:10]:  # Limit queries
            query_responses = []
            
            for ai in ai_engines:
                response = await query_ai_engine(query_text, brand_name, ai)
                query_responses.append(response)
                all_ai_responses.append(response)
                
                if response.get("role") != "error":
                    score = response.get("role_weight", 0) * 100
                    ai_scores[ai].append(score)
            
            query_result = {
                "query_text": query_text,
                "responses": query_responses,
                "avg_score": sum(r.get("role_weight", 0) for r in query_responses) / len(query_responses) * 100 if query_responses else 0
            }
            query_results.append(query_result)
        
        # Calculate scores
        rate_score = calculate_rate_score(all_ai_responses)
        
        # Calculate per-AI scores
        final_ai_scores = {}
        for ai, scores in ai_scores.items():
            final_ai_scores[ai] = round(sum(scores) / len(scores), 1) if scores else 0
        
        # Generate recommendations
        recommendations = generate_recommendations(rate_score, final_ai_scores)
        
        # Update analysis
        await db.analyses.update_one(
            {"analysis_id": analysis_id},
            {"$set": {
                "status": "completed",
                "global_score": rate_score["total"],
                "rate_score": rate_score,
                "ai_scores": final_ai_scores,
                "query_scores": query_results,
                "recommendations": recommendations,
                "completed_at": datetime.now(timezone.utc).isoformat()
            }}
        )
        
        # Update subscription usage
        await db.subscriptions.update_one(
            {"user_id": project["user_id"]},
            {"$inc": {"queries_used": len(base_queries[:10]) * len(ai_engines)}}
        )
        
    except Exception as e:
        logger.error(f"Analysis error: {e}")
        await db.analyses.update_one(
            {"analysis_id": analysis_id},
            {"$set": {"status": "failed", "error": str(e)}}
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
        response_text = response.text.lower() if response and response.text else ""
        
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

# ================== SUBSCRIPTION & PAYMENT ROUTES ==================

@api_router.get("/subscription/plans")
async def get_plans():
    """Get available subscription plans"""
    return {"plans": SUBSCRIPTION_PLANS}

@api_router.get("/subscription")
async def get_subscription(user: dict = Depends(get_current_user)):
    """Get user's current subscription"""
    subscription = await db.subscriptions.find_one({"user_id": user["user_id"]}, {"_id": 0})
    if not subscription:
        raise HTTPException(status_code=404, detail="Abonnement non trouvé")
    return {"subscription": subscription}

@api_router.post("/checkout/create")
async def create_checkout(request: Request, user: dict = Depends(get_current_user)):
    """Create Stripe checkout session"""
    body = await request.json()
    plan = body.get("plan", "starter")
    origin_url = body.get("origin_url")
    
    if plan not in SUBSCRIPTION_PLANS:
        raise HTTPException(status_code=400, detail="Plan invalide")
    
    if not origin_url:
        raise HTTPException(status_code=400, detail="origin_url requis")
    
    plan_config = SUBSCRIPTION_PLANS[plan]
    amount = plan_config["price"]
    
    # Initialize Stripe
    host_url = str(request.base_url)
    webhook_url = f"{host_url}api/webhook/stripe"
    stripe_checkout = StripeCheckout(api_key=STRIPE_API_KEY, webhook_url=webhook_url)
    
    success_url = f"{origin_url}/dashboard?payment=success&session_id={{CHECKOUT_SESSION_ID}}"
    cancel_url = f"{origin_url}/pricing?payment=cancelled"
    
    checkout_request = CheckoutSessionRequest(
        amount=amount,
        currency="eur",
        success_url=success_url,
        cancel_url=cancel_url,
        metadata={
            "user_id": user["user_id"],
            "plan": plan,
            "email": user.get("email", "")
        }
    )
    
    session = await stripe_checkout.create_checkout_session(checkout_request)
    
    # Create payment transaction record
    transaction = {
        "transaction_id": f"txn_{uuid.uuid4().hex[:12]}",
        "user_id": user["user_id"],
        "session_id": session.session_id,
        "amount": amount,
        "currency": "eur",
        "plan": plan,
        "status": "pending",
        "payment_status": "initiated",
        "metadata": {"plan": plan, "email": user.get("email", "")},
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.payment_transactions.insert_one(transaction)
    
    return {"url": session.url, "session_id": session.session_id}

@api_router.get("/checkout/status/{session_id}")
async def get_checkout_status(session_id: str, user: dict = Depends(get_current_user)):
    """Get checkout session status"""
    # Initialize Stripe
    host_url = "https://example.com/"  # Not needed for status check
    stripe_checkout = StripeCheckout(api_key=STRIPE_API_KEY, webhook_url=f"{host_url}api/webhook/stripe")
    
    status = await stripe_checkout.get_checkout_status(session_id)
    
    # Update transaction if payment completed
    if status.payment_status == "paid":
        transaction = await db.payment_transactions.find_one({"session_id": session_id}, {"_id": 0})
        
        if transaction and transaction.get("payment_status") != "paid":
            # Update transaction
            await db.payment_transactions.update_one(
                {"session_id": session_id},
                {"$set": {"status": "completed", "payment_status": "paid"}}
            )
            
            # Update subscription
            plan = status.metadata.get("plan", "starter")
            plan_config = SUBSCRIPTION_PLANS.get(plan, SUBSCRIPTION_PLANS["starter"])
            
            await db.subscriptions.update_one(
                {"user_id": user["user_id"]},
                {"$set": {
                    "plan": plan,
                    "status": "active",
                    "queries_limit": plan_config["queries_limit"],
                    "trial_ends_at": None,
                    "current_period_start": datetime.now(timezone.utc).isoformat(),
                    "current_period_end": (datetime.now(timezone.utc) + timedelta(days=30)).isoformat()
                }}
            )
    
    return {
        "status": status.status,
        "payment_status": status.payment_status,
        "amount_total": status.amount_total,
        "currency": status.currency
    }

@api_router.post("/webhook/stripe")
async def stripe_webhook(request: Request):
    """Handle Stripe webhooks"""
    body = await request.body()
    sig = request.headers.get("Stripe-Signature")
    
    try:
        host_url = str(request.base_url)
        stripe_checkout = StripeCheckout(api_key=STRIPE_API_KEY, webhook_url=f"{host_url}api/webhook/stripe")
        webhook_response = await stripe_checkout.handle_webhook(body, sig)
        
        if webhook_response.payment_status == "paid":
            session_id = webhook_response.session_id
            metadata = webhook_response.metadata
            
            # Update transaction
            await db.payment_transactions.update_one(
                {"session_id": session_id},
                {"$set": {"status": "completed", "payment_status": "paid"}}
            )
            
            # Update subscription
            user_id = metadata.get("user_id")
            plan = metadata.get("plan", "starter")
            plan_config = SUBSCRIPTION_PLANS.get(plan, SUBSCRIPTION_PLANS["starter"])
            
            await db.subscriptions.update_one(
                {"user_id": user_id},
                {"$set": {
                    "plan": plan,
                    "status": "active",
                    "queries_limit": plan_config["queries_limit"],
                    "current_period_start": datetime.now(timezone.utc).isoformat(),
                    "current_period_end": (datetime.now(timezone.utc) + timedelta(days=30)).isoformat()
                }}
            )
        
        return {"received": True}
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        return {"received": True, "error": str(e)}

# ================== DASHBOARD STATS ==================

@api_router.get("/dashboard/stats")
async def get_dashboard_stats(user: dict = Depends(get_current_user)):
    """Get dashboard statistics"""
    # Get projects count
    projects_count = await db.projects.count_documents({"user_id": user["user_id"]})
    
    # Get latest analysis
    latest_analysis = await db.analyses.find_one(
        {"user_id": user["user_id"], "status": "completed"},
        {"_id": 0},
        sort=[("created_at", -1)]
    )
    
    # Get subscription
    subscription = await db.subscriptions.find_one({"user_id": user["user_id"]}, {"_id": 0})
    
    # Get analyses history
    analyses = await db.analyses.find(
        {"user_id": user["user_id"], "status": "completed"},
        {"_id": 0, "analysis_id": 1, "global_score": 1, "created_at": 1}
    ).sort("created_at", -1).to_list(10)
    
    return {
        "projects_count": projects_count,
        "latest_analysis": latest_analysis,
        "subscription": subscription,
        "analyses_history": analyses,
        "global_score": latest_analysis.get("global_score", 0) if latest_analysis else 0
    }

# ================== GENERAL ROUTES ==================

@api_router.get("/")
async def root():
    return {"message": "IAskan API v1.0", "status": "healthy"}

@api_router.get("/health")
async def health():
    return {"status": "healthy", "timestamp": datetime.now(timezone.utc).isoformat()}

# Include router
app.include_router(api_router)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
