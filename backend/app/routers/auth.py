"""
Authentication Router - PostgreSQL Version
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
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, Dict, Any
from datetime import datetime, timezone, timedelta
from pydantic import BaseModel, EmailStr
import uuid
import secrets
import hashlib
import httpx
import logging
import asyncio

from ..db.database import get_db, async_session_maker
from ..db.services import UserService, SessionService, SubscriptionService, NotificationService, generate_id
from ..db.models import User, UserSession, Subscription, EmailVerificationToken, PasswordReset, MagicLink
from ..core.config import (
    BLOCKED_EMAIL_DOMAINS, 
    SUBSCRIPTION_PLANS,
    FRONTEND_URL,
    GOOGLE_CLIENT_ID,
    GOOGLE_CLIENT_SECRET,
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


async def get_current_user(request: Request) -> dict:
    """Dependency to get current authenticated user"""
    token = request.cookies.get("session_token")
    if not token:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
    
    if not token:
        raise HTTPException(status_code=401, detail="Non authentifié")
    
    async with async_session_maker() as db:
        session = await SessionService.get_by_token(db, token)
        if not session:
            raise HTTPException(status_code=401, detail="Session expirée")
        
        user = await UserService.get_by_user_id(db, session.user_id)
        if not user:
            raise HTTPException(status_code=401, detail="Utilisateur non trouvé")
        
        return UserService.to_dict(user)


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
    magic_link_url = f"{frontend_url}/auth/magic?token={magic_token}"
    html = get_email_template_magic_link(name or "cher utilisateur", magic_link_url)
    return await send_email_async(email, "Votre lien de connexion IAskan", html)


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
    
    async with async_session_maker() as db:
        existing_user = await UserService.get_by_email(db, email)
        
        if existing_user:
            user_id = existing_user.user_id
            user = existing_user
        else:
            # Create new user
            user = await UserService.create(
                db,
                email=email,
                name=name,
                picture=picture,
                auth_provider="google",
                registration_ip=client_ip,
                registration_fingerprint=fingerprint
            )
            user_id = user.user_id
            
            # Create free subscription
            await SubscriptionService.create_free(db, user_id)
            
            # Send welcome email
            await email_service.send_welcome_email(email, name)
            
            # Create welcome notification
            await NotificationService.create(
                db,
                user_id=user_id,
                type="welcome",
                title="Bienvenue sur IAskan ! 🎉",
                message=f"Bonjour {name or 'utilisateur'}, votre compte a été créé avec succès. Commencez par créer votre premier projet pour analyser votre visibilité IA.",
                data={"action": "create_project"}
            )
            
            logger.info(f"New user registered: email={email}")
        
        # Create session
        session = await SessionService.create(db, user_id, session_token)
        
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
        
        user_dict = UserService.to_dict(user)
        return {"user": user_dict, "session_token": session_token}


@router.get("/me")
async def get_me(user: dict = Depends(get_current_user)):
    """Get current authenticated user"""
    async with async_session_maker() as db:
        subscription = await SubscriptionService.get_by_user_id(db, user["user_id"])
        return {"user": user, "subscription": SubscriptionService.to_dict(subscription)}


@router.post("/logout")
async def logout(request: Request, response: Response):
    """Logout user and clear session"""
    token = request.cookies.get("session_token")
    if token:
        async with async_session_maker() as db:
            await SessionService.delete_by_token(db, token)
    
    response.delete_cookie("session_token", path="/")
    return {"message": "Déconnexion réussie"}


# ================== ROUTES - AUTH PROVIDERS ==================

@router.get("/providers")
async def get_auth_providers():
    """Get available authentication providers"""
    return {
        "providers": {
            "google": bool(GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET),
            "microsoft": bool(MICROSOFT_CLIENT_ID and MICROSOFT_CLIENT_SECRET),
            "linkedin": bool(LINKEDIN_CLIENT_ID and LINKEDIN_CLIENT_SECRET),
            "magic_link": True
        }
    }


# ================== ROUTES - GOOGLE OAUTH ==================

@router.get("/google/login")
async def google_login(request: Request):
    """Initiate Google OAuth2 login"""
    if not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET:
        raise HTTPException(status_code=501, detail="Google OAuth non configuré. Veuillez configurer GOOGLE_CLIENT_ID et GOOGLE_CLIENT_SECRET.")
    
    referer = request.headers.get("referer", "")
    frontend_url = referer.split("/login")[0] if "/login" in referer else request.headers.get("origin", FRONTEND_URL)
    
    # Encode frontend_url in state to make OAuth stateless (works across multiple instances)
    import base64
    state_data = f"{secrets.token_urlsafe(16)}|{frontend_url}"
    state = base64.urlsafe_b64encode(state_data.encode()).decode()
    
    # Build redirect URI - force HTTPS for production
    base_url = str(request.base_url)
    if base_url.startswith("http://") and "localhost" not in base_url and "127.0.0.1" not in base_url:
        base_url = base_url.replace("http://", "https://", 1)
    redirect_uri = base_url + "api/auth/google/callback"
    
    auth_url = (
        f"https://accounts.google.com/o/oauth2/v2/auth?"
        f"client_id={GOOGLE_CLIENT_ID}&"
        f"response_type=code&"
        f"redirect_uri={redirect_uri}&"
        f"scope=openid profile email&"
        f"state={state}&"
        f"access_type=offline&"
        f"prompt=consent"
    )
    
    return RedirectResponse(url=auth_url)


@router.get("/google/callback")
async def google_callback(request: Request, response: Response, code: str = None, state: str = None, error: str = None):
    """Handle Google OAuth2 callback"""
    import base64
    
    # Decode frontend_url from state (stateless OAuth)
    try:
        state_data = base64.urlsafe_b64decode(state.encode()).decode()
        _, frontend_url = state_data.split("|", 1)
    except Exception:
        frontend_url = FRONTEND_URL
    
    if error:
        logger.error(f"Google OAuth error: {error}")
        return RedirectResponse(url=f"{frontend_url}/login?error=google_auth_failed&detail={error}")
    
    if not code:
        logger.error("No authorization code received")
        return RedirectResponse(url=f"{frontend_url}/login?error=google_auth_failed&detail=no_code")
    
    # Build redirect URI - force HTTPS for production (must match login endpoint)
    base_url = str(request.base_url)
    if base_url.startswith("http://") and "localhost" not in base_url and "127.0.0.1" not in base_url:
        base_url = base_url.replace("http://", "https://", 1)
    redirect_uri = base_url + "api/auth/google/callback"
    
    try:
        # Exchange code for tokens
        async with httpx.AsyncClient(timeout=15.0) as client:
            token_response = await client.post(
                "https://oauth2.googleapis.com/token",
                data={
                    "code": code,
                    "client_id": GOOGLE_CLIENT_ID,
                    "client_secret": GOOGLE_CLIENT_SECRET,
                    "redirect_uri": redirect_uri,
                    "grant_type": "authorization_code"
                }
            )
            
            if token_response.status_code != 200:
                logger.error(f"Google token exchange failed: {token_response.text}")
                return RedirectResponse(url=f"{frontend_url}/login?error=token_exchange_failed")
            
            tokens = token_response.json()
            access_token = tokens.get("access_token")
            
            # Get user info
            userinfo_response = await client.get(
                "https://www.googleapis.com/oauth2/v2/userinfo",
                headers={"Authorization": f"Bearer {access_token}"}
            )
            
            if userinfo_response.status_code != 200:
                logger.error(f"Google userinfo failed: {userinfo_response.text}")
                return RedirectResponse(url=f"{frontend_url}/login?error=userinfo_failed")
            
            user_info = userinfo_response.json()
            
        email = user_info.get("email")
        name = user_info.get("name", email.split("@")[0])
        picture = user_info.get("picture", "")
        
        if not email:
            return RedirectResponse(url=f"{frontend_url}/login?error=no_email")
        
        # Check for temporary email
        if is_temporary_email(email):
            return RedirectResponse(url=f"{frontend_url}/login?error=temporary_email_blocked")
        
        client_ip = get_client_ip(request)
        session_token = secrets.token_urlsafe(32)
        
        async with async_session_maker() as db:
            existing_user = await UserService.get_by_email(db, email)
            
            if existing_user:
                user_id = existing_user.user_id
                user = existing_user
            else:
                # Create new user
                user = await UserService.create(
                    db,
                    email=email,
                    name=name,
                    picture=picture,
                    auth_provider="google",
                    registration_ip=client_ip,
                    registration_fingerprint="google_oauth"
                )
                user_id = user.user_id
                
                # Create free subscription
                await SubscriptionService.create_free(db, user_id)
                
                # Send welcome email
                await email_service.send_welcome_email(email, name)
                
                # Create welcome notification
                await NotificationService.create(
                    db,
                    user_id=user_id,
                    type="welcome",
                    title="Bienvenue sur IAskan ! 🎉",
                    message=f"Bonjour {name or 'utilisateur'}, votre compte a été créé avec succès. Commencez par créer votre premier projet pour analyser votre visibilité IA.",
                    data={"action": "create_project"}
                )
                
                logger.info(f"New user registered via Google: email={email}")
            
            # Create session
            await SessionService.create(db, user_id, session_token)
        
        # Set cookie
        response = RedirectResponse(url=f"{frontend_url}/dashboard")
        response.set_cookie(
            key="session_token",
            value=session_token,
            httponly=True,
            secure=True,
            samesite="none",
            path="/",
            max_age=7 * 24 * 60 * 60
        )
        
        logger.info(f"Google OAuth success: email={email}")
        return response
        
    except httpx.TimeoutException:
        logger.error("Google OAuth timeout")
        return RedirectResponse(url=f"{frontend_url}/login?error=timeout")
    except Exception as e:
        logger.error(f"Google OAuth error: {e}")
        return RedirectResponse(url=f"{frontend_url}/login?error=google_auth_failed")


# ================== ROUTES - MICROSOFT OAUTH ==================

@router.get("/microsoft/login")
async def microsoft_login(request: Request):
    """Initiate Microsoft OAuth2 login"""
    if not MICROSOFT_CLIENT_ID or not MICROSOFT_CLIENT_SECRET:
        raise HTTPException(status_code=501, detail="Microsoft OAuth non configuré.")
    
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
async def microsoft_callback(request: Request, response: Response, code: str = None, state: str = None, error: str = None):
    """Handle Microsoft OAuth2 callback"""
    frontend_url = request.session.get("frontend_url", FRONTEND_URL)
    
    if error:
        return RedirectResponse(url=f"{frontend_url}/login?error=microsoft_auth_failed")
    
    stored_state = request.session.get("oauth_state")
    if not stored_state or stored_state != state:
        return RedirectResponse(url=f"{frontend_url}/login?error=invalid_state")
    
    redirect_uri = str(request.base_url) + "api/auth/microsoft/callback"
    
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
        
        user_response = await client.get(
            "https://graph.microsoft.com/v1.0/me",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        
        if user_response.status_code != 200:
            return RedirectResponse(url=f"{frontend_url}/login?error=user_info_failed")
        
        user_data = user_response.json()
    
    email = user_data.get("mail") or user_data.get("userPrincipalName")
    name = user_data.get("displayName")
    
    # Create or get user and session
    async with async_session_maker() as db:
        existing_user = await UserService.get_by_email(db, email)
        
        if existing_user:
            user_id = existing_user.user_id
            if not existing_user.auth_provider:
                await UserService.update(db, user_id, auth_provider="microsoft")
        else:
            user = await UserService.create(
                db, email=email, name=name, auth_provider="microsoft", email_verified=True
            )
            user_id = user.user_id
            await SubscriptionService.create_free(db, user_id)
            await email_service.send_welcome_email(email, name)
            
            # Create welcome notification
            await NotificationService.create(
                db,
                user_id=user_id,
                type="welcome",
                title="Bienvenue sur IAskan ! 🎉",
                message=f"Bonjour {name or 'utilisateur'}, votre compte a été créé avec succès.",
                data={"action": "create_project"}
            )
        
        session_token = f"sess_{uuid.uuid4().hex}"
        await SessionService.create(db, user_id, session_token, expires_days=30)
    
    redirect_response = RedirectResponse(url=f"{frontend_url}/projects")
    redirect_response.set_cookie(
        key="session_token", value=session_token,
        httponly=True, secure=True, samesite="none", path="/", max_age=30*24*60*60
    )
    return redirect_response


# ================== ROUTES - LINKEDIN OAUTH ==================

@router.get("/linkedin/login")
async def linkedin_login(request: Request):
    """Initiate LinkedIn OAuth2 login"""
    if not LINKEDIN_CLIENT_ID or not LINKEDIN_CLIENT_SECRET:
        raise HTTPException(status_code=501, detail="LinkedIn OAuth non configuré.")
    
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
async def linkedin_callback(request: Request, response: Response, code: str = None, state: str = None, error: str = None):
    """Handle LinkedIn OAuth2 callback"""
    frontend_url = request.session.get("frontend_url", FRONTEND_URL)
    
    if error:
        return RedirectResponse(url=f"{frontend_url}/login?error=linkedin_auth_failed")
    
    stored_state = request.session.get("oauth_state")
    if not stored_state or stored_state != state:
        return RedirectResponse(url=f"{frontend_url}/login?error=invalid_state")
    
    redirect_uri = str(request.base_url) + "api/auth/linkedin/callback"
    
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
    
    async with async_session_maker() as db:
        existing_user = await UserService.get_by_email(db, email)
        
        if existing_user:
            user_id = existing_user.user_id
        else:
            user = await UserService.create(
                db, email=email, name=name, picture=picture, auth_provider="linkedin", email_verified=True
            )
            user_id = user.user_id
            await SubscriptionService.create_free(db, user_id)
            await email_service.send_welcome_email(email, name)
            
            # Create welcome notification
            await NotificationService.create(
                db,
                user_id=user_id,
                type="welcome",
                title="Bienvenue sur IAskan ! 🎉",
                message=f"Bonjour {name or 'utilisateur'}, votre compte a été créé avec succès.",
                data={"action": "create_project"}
            )
        
        session_token = f"sess_{uuid.uuid4().hex}"
        await SessionService.create(db, user_id, session_token, expires_days=30)
    
    redirect_response = RedirectResponse(url=f"{frontend_url}/projects")
    redirect_response.set_cookie(
        key="session_token", value=session_token,
        httponly=True, secure=True, samesite="none", path="/", max_age=30*24*60*60
    )
    return redirect_response


# ================== ROUTES - PASSWORD RESET ==================

@router.post("/forgot-password")
async def forgot_password(request: Request, body: PasswordResetRequest):
    """Request password reset email"""
    async with async_session_maker() as db:
        user = await UserService.get_by_email(db, body.email)
        
        if not user:
            return {"message": "Si un compte existe avec cet email, vous recevrez un lien de réinitialisation."}
        
        reset_token = secrets.token_urlsafe(32)
        expires_at = datetime.now(timezone.utc) + timedelta(hours=1)
        
        password_reset = PasswordReset(
            token=reset_token,
            user_id=user.user_id,
            email=body.email,
            expires_at=expires_at
        )
        db.add(password_reset)
        await db.commit()
    
    referer = request.headers.get("referer", "")
    frontend_url = referer.split("/")[0] + "//" + referer.split("/")[2] if "//" in referer else FRONTEND_URL
    
    asyncio.create_task(send_password_reset_email(body.email, user.name or "", reset_token, frontend_url))
    
    return {"message": "Si un compte existe avec cet email, vous recevrez un lien de réinitialisation."}


@router.post("/reset-password")
async def reset_password(body: PasswordResetConfirm):
    """Reset password with token"""
    from sqlalchemy import select, update
    
    async with async_session_maker() as db:
        result = await db.execute(
            select(PasswordReset).where(PasswordReset.token == body.token, PasswordReset.used == False)
        )
        reset_doc = result.scalar_one_or_none()
        
        if not reset_doc:
            raise HTTPException(status_code=400, detail="Lien de réinitialisation invalide ou expiré.")
        
        if datetime.now(timezone.utc) > reset_doc.expires_at:
            raise HTTPException(status_code=400, detail="Ce lien a expiré.")
        
        password_hash = hashlib.sha256(body.new_password.encode()).hexdigest()
        
        await UserService.update(db, reset_doc.user_id, password_hash=password_hash)
        
        await db.execute(
            update(PasswordReset).where(PasswordReset.token == body.token).values(used=True)
        )
        await db.commit()
        
        await SessionService.delete_by_user(db, reset_doc.user_id)
    
    return {"message": "Mot de passe mis à jour avec succès."}


# ================== ROUTES - MAGIC LINK ==================

@router.post("/magic-link")
async def request_magic_link(request: Request, body: MagicLinkRequest):
    """Request magic link login email"""
    is_new_user = False
    async with async_session_maker() as db:
        user = await UserService.get_by_email(db, body.email)
        
        if not user:
            user = await UserService.create(
                db, email=body.email, name=body.email.split("@")[0], auth_provider="magic_link"
            )
            await SubscriptionService.create_free(db, user.user_id)
            is_new_user = True
            
            # Create welcome notification
            await NotificationService.create(
                db,
                user_id=user.user_id,
                type="welcome",
                title="Bienvenue sur IAskan ! 🎉",
                message=f"Bonjour, votre compte a été créé avec succès. Commencez par créer votre premier projet.",
                data={"action": "create_project"}
            )
        
        magic_token = secrets.token_urlsafe(32)
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=15)
        
        magic_link = MagicLink(
            token=magic_token,
            user_id=user.user_id,
            email=body.email,
            expires_at=expires_at
        )
        db.add(magic_link)
        await db.commit()
    
    referer = request.headers.get("referer", "")
    frontend_url = referer.split("/")[0] + "//" + referer.split("/")[2] if "//" in referer else FRONTEND_URL
    
    # Send magic link email
    asyncio.create_task(send_magic_link_email(body.email, user.name or "", magic_token, frontend_url))
    
    # Send welcome email for new users
    if is_new_user:
        await email_service.send_welcome_email(body.email, user.name or body.email.split("@")[0])
        logger.info(f"New user registered via Magic Link: email={body.email}")
    
    return {"message": "Un lien de connexion a été envoyé à votre adresse email."}


@router.get("/magic-verify")
async def verify_magic_link(token: str, response: Response):
    """Verify magic link and create session"""
    from sqlalchemy import select, update
    
    async with async_session_maker() as db:
        result = await db.execute(
            select(MagicLink).where(MagicLink.token == token, MagicLink.used == False)
        )
        magic_doc = result.scalar_one_or_none()
        
        if not magic_doc:
            raise HTTPException(status_code=400, detail="Lien de connexion invalide ou déjà utilisé.")
        
        if datetime.now(timezone.utc) > magic_doc.expires_at:
            raise HTTPException(status_code=400, detail="Ce lien a expiré.")
        
        await db.execute(update(MagicLink).where(MagicLink.token == token).values(used=True))
        await db.commit()
        
        user = await UserService.get_by_user_id(db, magic_doc.user_id)
        if not user:
            raise HTTPException(status_code=404, detail="Utilisateur non trouvé.")
        
        session_token = f"sess_{uuid.uuid4().hex}"
        await SessionService.create(db, user.user_id, session_token, expires_days=7)
        
        response.set_cookie(
            key="session_token", value=session_token,
            httponly=True, secure=True, samesite="none", path="/", max_age=7*24*60*60
        )
        
        return {"message": "Connexion réussie", "user": UserService.to_dict(user)}
