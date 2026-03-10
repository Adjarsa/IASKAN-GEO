"""
Authentication Router
Handles all authentication related endpoints
"""
from fastapi import APIRouter, HTTPException, Request, Response, Depends
from typing import Optional, Dict, Any
from datetime import datetime, timezone, timedelta
from pydantic import BaseModel, EmailStr
import uuid
import httpx
import logging

from ..core.database import db
from ..core.config import (
    BLOCKED_EMAIL_DOMAINS, 
    SUBSCRIPTION_PLANS,
    FRONTEND_URL,
    MICROSOFT_CLIENT_ID,
    MICROSOFT_CLIENT_SECRET,
    LINKEDIN_CLIENT_ID,
    LINKEDIN_CLIENT_SECRET
)
from ..services.email_service import email_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


# Request Models
class PasswordResetRequest(BaseModel):
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    token: str
    password: str


class MagicLinkRequest(BaseModel):
    email: EmailStr


# Helper Functions
def get_client_ip(request: Request) -> str:
    """Extract client IP from request"""
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def is_temporary_email(email: str) -> bool:
    """Check if email is from a temporary email provider"""
    domain = email.split("@")[-1].lower() if "@" in email else ""
    return domain in BLOCKED_EMAIL_DOMAINS


async def get_session_from_token(token: str) -> Optional[dict]:
    """Get session from token"""
    if not token:
        return None
    session = await db.user_sessions.find_one({"session_token": token}, {"_id": 0})
    if not session:
        return None
    expires_at = datetime.fromisoformat(session["expires_at"].replace('Z', '+00:00'))
    if datetime.now(timezone.utc) > expires_at:
        return None
    return session


async def get_current_user(request: Request) -> dict:
    """Dependency to get current authenticated user"""
    token = request.cookies.get("session_token")
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


async def create_verification_token(user_id: str, email: str) -> str:
    """Create email verification token"""
    token = uuid.uuid4().hex
    expires_at = datetime.now(timezone.utc) + timedelta(hours=24)
    
    token_doc = {
        "token_id": f"evt_{uuid.uuid4().hex[:12]}",
        "user_id": user_id,
        "email": email,
        "token": token,
        "expires_at": expires_at.isoformat(),
        "used": False,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.email_verification_tokens.insert_one(token_doc)
    return token


async def send_verification_email(email: str, user_name: str, token: str) -> bool:
    """Send verification email"""
    try:
        import resend
        from ..core.config import RESEND_API_KEY, SENDER_EMAIL
        
        if not RESEND_API_KEY:
            logger.warning("RESEND_API_KEY not set, skipping verification email")
            return False
        
        resend.api_key = RESEND_API_KEY
        verification_url = f"{FRONTEND_URL}/verify-email?token={token}"
        
        html_content = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <div style="background: linear-gradient(135deg, #8b5cf6 0%, #06b6d4 100%); padding: 30px; text-align: center;">
                <h1 style="color: white; margin: 0;">IAskan</h1>
            </div>
            <div style="padding: 30px; background: #ffffff;">
                <h2 style="color: #1e293b;">Vérifiez votre email</h2>
                <p style="color: #475569;">Bonjour {user_name},</p>
                <p style="color: #475569;">Cliquez sur le bouton ci-dessous pour vérifier votre adresse email :</p>
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{verification_url}" 
                       style="background: linear-gradient(135deg, #8b5cf6 0%, #06b6d4 100%); 
                              color: white; padding: 15px 30px; text-decoration: none; 
                              border-radius: 8px; font-weight: bold;">
                        Vérifier mon email
                    </a>
                </div>
                <p style="color: #94a3b8; font-size: 12px;">Ce lien expire dans 24 heures.</p>
            </div>
        </div>
        """
        
        resend.Emails.send({
            "from": f"IAskan <{SENDER_EMAIL}>",
            "to": [email],
            "subject": "Vérifiez votre email - IAskan",
            "html": html_content
        })
        return True
    except Exception as e:
        logger.error(f"Error sending verification email: {e}")
        return False


# Routes
@router.post("/session")
async def create_session(request: Request, response: Response):
    """Exchange session_id from Emergent Auth for session_token"""
    body = await request.json()
    session_id = body.get("session_id")
    fingerprint = body.get("fingerprint", "unknown")
    
    if not session_id:
        raise HTTPException(status_code=400, detail="session_id requis")
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            auth_response = await client.get(
                "https://demobackend.emergentagent.com/auth/v1/env/oauth/session-data",
                headers={"X-Session-ID": session_id}
            )
            
            if auth_response.status_code != 200:
                raise HTTPException(status_code=401, detail="Session invalide")
            
            auth_data = auth_response.json()
    except httpx.TimeoutException:
        raise HTTPException(status_code=408, detail="Timeout lors de la vérification de session")
    except Exception as e:
        logger.error(f"Auth session error: {e}")
        raise HTTPException(status_code=401, detail="Session invalide")
    
    user_id = f"user_{uuid.uuid4().hex[:12]}"
    email = auth_data.get("email")
    name = auth_data.get("name")
    picture = auth_data.get("picture")
    session_token = auth_data.get("session_token")
    
    # Check for temporary email
    if is_temporary_email(email):
        raise HTTPException(
            status_code=403,
            detail={
                "error": "temporary_email_blocked",
                "message": "Les adresses email temporaires ne sont pas autorisées."
            }
        )
    
    client_ip = get_client_ip(request)
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
            "email_verified": False,
            "registration_ip": client_ip,
            "registration_fingerprint": fingerprint,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        await db.users.insert_one(user_doc)
        
        # Create free subscription
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
        
        # Send verification email
        verification_token = await create_verification_token(user_id, email)
        await send_verification_email(email, name, verification_token)
        
        # Send welcome email
        await email_service.send_welcome_email(email, name)
        
        logger.info(f"New user registered: email={email}")
    
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
        max_age=7 * 24 * 60 * 60
    )
    
    user = await db.users.find_one({"user_id": user_id}, {"_id": 0})
    return {"user": user, "session_token": session_token}


@router.get("/me")
async def get_me(user: dict = Depends(get_current_user)):
    """Get current authenticated user"""
    subscription = await db.subscriptions.find_one({"user_id": user["user_id"]}, {"_id": 0})
    return {"user": user, "subscription": subscription}


@router.post("/logout")
async def logout(request: Request, response: Response):
    """Logout user and clear session"""
    token = request.cookies.get("session_token")
    if token:
        await db.user_sessions.delete_many({"session_token": token})
    
    response.delete_cookie("session_token", path="/")
    return {"message": "Déconnexion réussie"}


@router.post("/verify-email")
async def verify_email_endpoint(request: Request):
    """Verify email with token"""
    body = await request.json()
    token = body.get("token")
    
    if not token:
        raise HTTPException(status_code=400, detail="Token requis")
    
    token_doc = await db.email_verification_tokens.find_one(
        {"token": token, "used": False},
        {"_id": 0}
    )
    
    if not token_doc:
        raise HTTPException(status_code=400, detail="Token invalide ou déjà utilisé")
    
    expires_at = datetime.fromisoformat(token_doc["expires_at"].replace('Z', '+00:00'))
    if datetime.now(timezone.utc) > expires_at:
        raise HTTPException(status_code=400, detail="Token expiré")
    
    # Mark email as verified
    await db.users.update_one(
        {"user_id": token_doc["user_id"]},
        {"$set": {
            "email_verified": True,
            "email_verified_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    # Mark token as used
    await db.email_verification_tokens.update_one(
        {"token": token},
        {"$set": {"used": True}}
    )
    
    return {"success": True, "message": "Email vérifié avec succès"}


@router.post("/resend-verification")
async def resend_verification_email_endpoint(user: dict = Depends(get_current_user)):
    """Resend verification email"""
    if user.get("email_verified"):
        return {"success": True, "message": "Email déjà vérifié"}
    
    # Delete old tokens
    await db.email_verification_tokens.delete_many({"user_id": user["user_id"]})
    
    # Create new token
    token = await create_verification_token(user["user_id"], user["email"])
    await send_verification_email(user["email"], user["name"], token)
    
    return {"success": True, "message": "Email de vérification envoyé"}


@router.get("/verification-status")
async def get_verification_status(user: dict = Depends(get_current_user)):
    """Get email verification status"""
    return {
        "email_verified": user.get("email_verified", False),
        "email": user.get("email")
    }


@router.get("/providers")
async def get_auth_providers():
    """Get available authentication providers"""
    return {
        "providers": {
            "google": True,
            "microsoft": bool(MICROSOFT_CLIENT_ID and MICROSOFT_CLIENT_SECRET),
            "linkedin": bool(LINKEDIN_CLIENT_ID and LINKEDIN_CLIENT_SECRET),
            "magic_link": True
        }
    }
