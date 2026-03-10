"""
Authentication Router
Handles all authentication related endpoints including:
- Session management (Emergent Auth)
- Microsoft OAuth
- LinkedIn OAuth
- Magic Link authentication
- Password reset
- Email verification
"""
from fastapi import APIRouter, HTTPException, Request, Response, Depends
from fastapi.responses import RedirectResponse
from typing import Optional, Dict, Any
from datetime import datetime, timezone, timedelta
from pydantic import BaseModel, EmailStr
import uuid
import secrets
import hashlib
import httpx
import logging
import asyncio

from ..core.database import db
from ..core.config import (
    BLOCKED_EMAIL_DOMAINS, 
    SUBSCRIPTION_PLANS,
    FRONTEND_URL,
    MICROSOFT_CLIENT_ID,
    MICROSOFT_CLIENT_SECRET,
    LINKEDIN_CLIENT_ID,
    LINKEDIN_CLIENT_SECRET,
    RESEND_API_KEY,
    SENDER_EMAIL
)
from ..services.email_service import email_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


# ================== REQUEST MODELS ==================

class PasswordResetRequest(BaseModel):
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str


class MagicLinkRequest(BaseModel):
    email: EmailStr


# ================== EMAIL TEMPLATES ==================

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
                        <tr>
                            <td style="background: linear-gradient(135deg, #7c3aed 0%, #06b6d4 100%); padding: 40px; text-align: center;">
                                <h1 style="color: #ffffff; font-size: 28px; margin: 0; font-weight: 700;">IAskan</h1>
                                <p style="color: rgba(255,255,255,0.9); margin: 10px 0 0 0; font-size: 14px;">Réinitialisation de mot de passe</p>
                            </td>
                        </tr>
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
                        <tr>
                            <td style="background-color: #f8fafc; padding: 30px; text-align: center; border-top: 1px solid #e2e8f0;">
                                <p style="color: #94a3b8; font-size: 14px; margin: 0;">© 2026 IAskan. Tous droits réservés.</p>
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
                        <tr>
                            <td style="background: linear-gradient(135deg, #7c3aed 0%, #06b6d4 100%); padding: 40px; text-align: center;">
                                <h1 style="color: #ffffff; font-size: 28px; margin: 0; font-weight: 700;">IAskan</h1>
                                <p style="color: rgba(255,255,255,0.9); margin: 10px 0 0 0; font-size: 14px;">Connexion sécurisée</p>
                            </td>
                        </tr>
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
                        <tr>
                            <td style="background-color: #f8fafc; padding: 30px; text-align: center; border-top: 1px solid #e2e8f0;">
                                <p style="color: #94a3b8; font-size: 14px; margin: 0;">© 2026 IAskan. Tous droits réservés.</p>
                            </td>
                        </tr>
                    </table>
                </td>
            </tr>
        </table>
    </body>
    </html>
    """


# ================== HELPER FUNCTIONS ==================

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


async def send_email_async(to_email: str, subject: str, html_content: str) -> dict:
    """Send email using Resend API (non-blocking)"""
    import resend
    
    if not RESEND_API_KEY:
        logger.warning(f"Email not sent (no API key): {subject} to {to_email}")
        return {"status": "skipped", "reason": "No Resend API key configured"}
    
    resend.api_key = RESEND_API_KEY
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


async def create_oauth_user_session(email: str, name: str, picture: str, provider: str, response: Response) -> dict:
    """Create or update user and create session for OAuth providers"""
    existing_user = await db.users.find_one({"email": email}, {"_id": 0})
    
    if existing_user:
        user_id = existing_user["user_id"]
        # Update auth provider if not set
        if not existing_user.get("auth_provider"):
            await db.users.update_one(
                {"user_id": user_id},
                {"$set": {"auth_provider": provider}}
            )
    else:
        # Create new user
        user_id = f"user_{uuid.uuid4().hex[:12]}"
        user_doc = {
            "user_id": user_id,
            "email": email,
            "name": name,
            "picture": picture,
            "auth_provider": provider,
            "email_verified": True,  # OAuth emails are pre-verified
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
        
        # Send welcome email
        await email_service.send_welcome_email(email, name)
        logger.info(f"New user registered via {provider}: email={email}")
    
    # Create session
    session_token = f"sess_{uuid.uuid4().hex}"
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
        max_age=30 * 24 * 60 * 60
    )
    
    return {"user_id": user_id, "session_token": session_token}


# ================== ROUTES - SESSION MANAGEMENT ==================

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


# ================== ROUTES - EMAIL VERIFICATION ==================

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


# ================== ROUTES - AUTH PROVIDERS ==================

@router.get("/providers")
async def get_auth_providers():
    """Get available authentication providers"""
    return {
        "providers": {
            "google": True,  # Always available via Emergent Auth
            "microsoft": bool(MICROSOFT_CLIENT_ID and MICROSOFT_CLIENT_SECRET),
            "linkedin": bool(LINKEDIN_CLIENT_ID and LINKEDIN_CLIENT_SECRET),
            "magic_link": True
        }
    }


# ================== ROUTES - MICROSOFT OAUTH ==================

@router.get("/microsoft/login")
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


@router.get("/microsoft/callback")
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


# ================== ROUTES - LINKEDIN OAUTH ==================

@router.get("/linkedin/login")
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


@router.get("/linkedin/callback")
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


# ================== ROUTES - PASSWORD RESET ==================

@router.post("/forgot-password")
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


@router.post("/reset-password")
async def reset_password(body: PasswordResetConfirm):
    """Reset password with token"""
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


# ================== ROUTES - MAGIC LINK ==================

@router.post("/magic-link")
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


@router.get("/magic-verify")
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
