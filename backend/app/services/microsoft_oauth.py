"""
Microsoft OAuth 2.0 Authentication
Handles Microsoft/Azure AD SSO login flow
"""
import os
import logging
import secrets
from typing import Optional, Dict, Any
from datetime import datetime, timezone
import httpx
from authlib.integrations.starlette_client import OAuth

logger = logging.getLogger(__name__)

# Microsoft OAuth configuration
MICROSOFT_CLIENT_ID = os.environ.get('MICROSOFT_CLIENT_ID', '')
MICROSOFT_CLIENT_SECRET = os.environ.get('MICROSOFT_CLIENT_SECRET', '')
MICROSOFT_TENANT_ID = os.environ.get('MICROSOFT_TENANT_ID', 'common')  # 'common' for multi-tenant

# Microsoft OAuth endpoints
MICROSOFT_AUTHORIZATION_URL = f"https://login.microsoftonline.com/{MICROSOFT_TENANT_ID}/oauth2/v2.0/authorize"
MICROSOFT_TOKEN_URL = f"https://login.microsoftonline.com/{MICROSOFT_TENANT_ID}/oauth2/v2.0/token"
MICROSOFT_USERINFO_URL = "https://graph.microsoft.com/v1.0/me"


class MicrosoftOAuth:
    """
    Microsoft OAuth 2.0 handler for FastAPI.
    Supports Azure AD authentication for enterprise SSO.
    """
    
    def __init__(
        self, 
        client_id: str = None, 
        client_secret: str = None,
        tenant_id: str = None,
        redirect_uri: str = None
    ):
        self.client_id = client_id or MICROSOFT_CLIENT_ID
        self.client_secret = client_secret or MICROSOFT_CLIENT_SECRET
        self.tenant_id = tenant_id or MICROSOFT_TENANT_ID
        self.redirect_uri = redirect_uri
        
        # Update endpoints with tenant
        self.authorization_url = f"https://login.microsoftonline.com/{self.tenant_id}/oauth2/v2.0/authorize"
        self.token_url = f"https://login.microsoftonline.com/{self.tenant_id}/oauth2/v2.0/token"
        self.userinfo_url = "https://graph.microsoft.com/v1.0/me"
        
        # State storage (in production, use Redis or DB)
        self._states: Dict[str, datetime] = {}
    
    def is_configured(self) -> bool:
        """Check if Microsoft OAuth is properly configured"""
        return bool(self.client_id and self.client_secret)
    
    def generate_state(self) -> str:
        """Generate a secure state token for CSRF protection"""
        state = secrets.token_urlsafe(32)
        self._states[state] = datetime.now(timezone.utc)
        # Clean old states (older than 10 minutes)
        self._cleanup_states()
        return state
    
    def validate_state(self, state: str) -> bool:
        """Validate state token"""
        if state not in self._states:
            return False
        # Remove used state
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
        Generate Microsoft OAuth authorization URL.
        
        Args:
            redirect_uri: URL to redirect after authentication
            state: CSRF state token (generated if not provided)
            
        Returns:
            Authorization URL to redirect user to
        """
        if not state:
            state = self.generate_state()
        
        params = {
            "client_id": self.client_id,
            "response_type": "code",
            "redirect_uri": redirect_uri,
            "response_mode": "query",
            "scope": "openid email profile User.Read",
            "state": state,
        }
        
        query_string = "&".join(f"{k}={v}" for k, v in params.items())
        return f"{self.authorization_url}?{query_string}"
    
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
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "code": code,
            "redirect_uri": redirect_uri,
            "grant_type": "authorization_code",
            "scope": "openid email profile User.Read",
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.token_url,
                    data=data,
                    headers={"Content-Type": "application/x-www-form-urlencoded"}
                )
                
                if response.status_code == 200:
                    return response.json()
                else:
                    logger.error(f"Microsoft token exchange failed: {response.status_code} - {response.text}")
                    return None
                    
        except Exception as e:
            logger.error(f"Microsoft token exchange error: {e}")
            return None
    
    async def get_user_info(self, access_token: str) -> Optional[Dict[str, Any]]:
        """
        Get user information from Microsoft Graph API.
        
        Args:
            access_token: Valid access token
            
        Returns:
            User info dict or None if failed
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    self.userinfo_url,
                    headers={"Authorization": f"Bearer {access_token}"}
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return {
                        "id": data.get("id"),
                        "email": data.get("mail") or data.get("userPrincipalName"),
                        "name": data.get("displayName"),
                        "given_name": data.get("givenName"),
                        "family_name": data.get("surname"),
                        "picture": None,  # Microsoft Graph requires different endpoint for photo
                        "provider": "microsoft"
                    }
                else:
                    logger.error(f"Microsoft userinfo failed: {response.status_code} - {response.text}")
                    return None
                    
        except Exception as e:
            logger.error(f"Microsoft userinfo error: {e}")
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
            logger.warning("Invalid Microsoft OAuth state")
            return None
        
        # Exchange code for token
        token_response = await self.exchange_code_for_token(code, redirect_uri)
        if not token_response:
            return None
        
        access_token = token_response.get("access_token")
        if not access_token:
            logger.error("No access token in Microsoft response")
            return None
        
        # Get user info
        user_info = await self.get_user_info(access_token)
        if user_info:
            # Add token info for potential future use
            user_info["access_token"] = access_token
            user_info["id_token"] = token_response.get("id_token")
            user_info["expires_in"] = token_response.get("expires_in")
        
        return user_info


# Singleton instance
microsoft_oauth = MicrosoftOAuth()
