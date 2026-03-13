"""
LinkedIn OAuth 2.0 Authentication
Handles LinkedIn SSO login flow using OpenID Connect
"""
import os
import logging
import secrets
from typing import Optional, Dict, Any
from datetime import datetime, timezone
import httpx

logger = logging.getLogger(__name__)

# LinkedIn OAuth configuration
LINKEDIN_CLIENT_ID = os.environ.get('LINKEDIN_CLIENT_ID', '')
LINKEDIN_CLIENT_SECRET = os.environ.get('LINKEDIN_CLIENT_SECRET', '')

# LinkedIn OAuth endpoints (OpenID Connect)
LINKEDIN_AUTHORIZATION_URL = "https://www.linkedin.com/oauth/v2/authorization"
LINKEDIN_TOKEN_URL = "https://www.linkedin.com/oauth/v2/accessToken"
LINKEDIN_USERINFO_URL = "https://api.linkedin.com/v2/userinfo"


class LinkedInOAuth:
    """
    LinkedIn OAuth 2.0 handler for FastAPI.
    Uses OpenID Connect for authentication.
    """
    
    def __init__(
        self, 
        client_id: str = None, 
        client_secret: str = None,
        redirect_uri: str = None
    ):
        self.client_id = client_id or LINKEDIN_CLIENT_ID
        self.client_secret = client_secret or LINKEDIN_CLIENT_SECRET
        self.redirect_uri = redirect_uri
        
        # State storage (in production, use Redis or DB)
        self._states: Dict[str, datetime] = {}
    
    def is_configured(self) -> bool:
        """Check if LinkedIn OAuth is properly configured"""
        return bool(self.client_id and self.client_secret)
    
    def generate_state(self) -> str:
        """Generate a secure state token for CSRF protection"""
        state = secrets.token_urlsafe(32)
        self._states[state] = datetime.now(timezone.utc)
        self._cleanup_states()
        return state
    
    def validate_state(self, state: str) -> bool:
        """Validate state token"""
        if state not in self._states:
            return False
        del self._states[state]
        return True
    
    def _cleanup_states(self):
        """Remove expired states"""
        from datetime import timedelta
        now = datetime.now(timezone.utc)
        expired = [
            s for s, t in self._states.items() 
            if (now - t) > timedelta(minutes=10)
        ]
        for s in expired:
            del self._states[s]
    
    def get_authorization_url(self, redirect_uri: str, state: str = None) -> str:
        """
        Generate LinkedIn OAuth authorization URL.
        
        Args:
            redirect_uri: URL to redirect after authentication
            state: CSRF state token (generated if not provided)
            
        Returns:
            Authorization URL to redirect user to
        """
        if not state:
            state = self.generate_state()
        
        # Use OpenID Connect scopes
        params = {
            "response_type": "code",
            "client_id": self.client_id,
            "redirect_uri": redirect_uri,
            "state": state,
            "scope": "openid profile email",
        }
        
        query_string = "&".join(f"{k}={v}" for k, v in params.items())
        return f"{LINKEDIN_AUTHORIZATION_URL}?{query_string}"
    
    async def exchange_code_for_token(
        self, 
        code: str, 
        redirect_uri: str
    ) -> Optional[Dict[str, Any]]:
        """
        Exchange authorization code for access token.
        
        Args:
            code: Authorization code from callback
            redirect_uri: Same redirect URI used in authorization
            
        Returns:
            Token response dict or None if failed
        """
        data = {
            "grant_type": "authorization_code",
            "code": code,
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "redirect_uri": redirect_uri,
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    LINKEDIN_TOKEN_URL,
                    data=data,
                    headers={"Content-Type": "application/x-www-form-urlencoded"}
                )
                
                if response.status_code == 200:
                    return response.json()
                else:
                    logger.error(f"LinkedIn token exchange failed: {response.status_code} - {response.text}")
                    return None
                    
        except Exception as e:
            logger.error(f"LinkedIn token exchange error: {e}")
            return None
    
    async def get_user_info(self, access_token: str) -> Optional[Dict[str, Any]]:
        """
        Get user information from LinkedIn UserInfo endpoint (OpenID Connect).
        
        Args:
            access_token: Valid access token
            
        Returns:
            User info dict or None if failed
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    LINKEDIN_USERINFO_URL,
                    headers={"Authorization": f"Bearer {access_token}"}
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return {
                        "id": data.get("sub"),
                        "email": data.get("email"),
                        "name": data.get("name"),
                        "given_name": data.get("given_name"),
                        "family_name": data.get("family_name"),
                        "picture": data.get("picture"),
                        "locale": data.get("locale"),
                        "email_verified": data.get("email_verified", False),
                        "provider": "linkedin"
                    }
                else:
                    logger.error(f"LinkedIn userinfo failed: {response.status_code} - {response.text}")
                    return None
                    
        except Exception as e:
            logger.error(f"LinkedIn userinfo error: {e}")
            return None
    
    async def authenticate(
        self, 
        code: str, 
        redirect_uri: str, 
        state: str = None
    ) -> Optional[Dict[str, Any]]:
        """
        Complete authentication flow: exchange code and get user info.
        
        Args:
            code: Authorization code from callback
            redirect_uri: Redirect URI used
            state: State token to validate (optional)
            
        Returns:
            User info dict or None if failed
        """
        # Validate state if provided
        if state and not self.validate_state(state):
            logger.warning("Invalid LinkedIn OAuth state")
            return None
        
        # Exchange code for token
        token_response = await self.exchange_code_for_token(code, redirect_uri)
        if not token_response:
            return None
        
        access_token = token_response.get("access_token")
        if not access_token:
            logger.error("No access token in LinkedIn response")
            return None
        
        # Get user info
        user_info = await self.get_user_info(access_token)
        if user_info:
            user_info["access_token"] = access_token
            user_info["id_token"] = token_response.get("id_token")
            user_info["expires_in"] = token_response.get("expires_in")
        
        return user_info


# Singleton instance
linkedin_oauth = LinkedInOAuth()
