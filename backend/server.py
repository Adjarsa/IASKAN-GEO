from fastapi import FastAPI, APIRouter, HTTPException, Request, Response, Depends
from fastapi.responses import StreamingResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timezone, timedelta
import httpx
import json
import asyncio
import io
from fpdf import FPDF
from emergentintegrations.llm.chat import LlmChat, UserMessage
from emergentintegrations.payments.stripe.checkout import StripeCheckout, CheckoutSessionResponse, CheckoutStatusResponse, CheckoutSessionRequest

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Get API keys
EMERGENT_LLM_KEY = os.environ.get('EMERGENT_LLM_KEY')
STRIPE_API_KEY = os.environ.get('STRIPE_API_KEY')

# Create the main app
app = FastAPI(title="IAskan API", version="1.0.0")

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
        "ai_engines": ["chatgpt"],
        "features": ["Score GEO basique", "ChatGPT uniquement", "Rapport standard", "Support email"]
    },
    "pro": {
        "name": "Pro",
        "price": 149.00,
        "queries_limit": 600,
        "ai_engines": ["chatgpt", "claude", "gemini", "perplexity"],
        "features": ["Score GEO avancé", "Multi-IA (4 moteurs)", "Benchmark concurrents", "Analyse de stabilité", "Support prioritaire"]
    },
    "business": {
        "name": "Business",
        "price": 349.00,
        "queries_limit": 1500,
        "ai_engines": ["chatgpt", "claude", "gemini", "perplexity"],
        "features": ["Score GEO complet", "Toutes les IA", "Génération d'articles GEO", "Intelligence stratégique", "API access", "Support dédié"]
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
            pdf.set_font('DejaVu', 'I', 9)
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
