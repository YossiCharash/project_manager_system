"""
OAuth Service - handles Google OAuth login.
"""
from __future__ import annotations

import logging
from typing import Optional
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class OAuthService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_google_authorization_url(self, state: str = "") -> str:
        """Build Google OAuth2 authorization URL."""
        try:
            from backend.core.config import settings
            from urllib.parse import urlencode

            google_client_id = getattr(settings, "GOOGLE_CLIENT_ID", None)
            redirect_uri = getattr(settings, "GOOGLE_REDIRECT_URI", None)

            if not google_client_id or not redirect_uri:
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="Google OAuth is not configured"
                )

            params = {
                "client_id": google_client_id,
                "redirect_uri": redirect_uri,
                "response_type": "code",
                "scope": "openid email profile",
                "state": state,
                "access_type": "offline",
                "prompt": "consent",
            }
            return "https://accounts.google.com/o/oauth2/v2/auth?" + urlencode(params)
        except HTTPException:
            raise
        except Exception as e:
            logger.exception("Error building Google authorization URL")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to initiate OAuth flow"
            )

    async def handle_google_callback(self, code: str, state: Optional[str] = None) -> dict:
        """Exchange authorization code for tokens and get/create user."""
        try:
            from backend.core.config import settings
            import httpx

            google_client_id = getattr(settings, "GOOGLE_CLIENT_ID", None)
            google_client_secret = getattr(settings, "GOOGLE_CLIENT_SECRET", None)
            redirect_uri = getattr(settings, "GOOGLE_REDIRECT_URI", None)

            if not google_client_id or not google_client_secret or not redirect_uri:
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="Google OAuth is not configured"
                )

            # Exchange code for tokens
            async with httpx.AsyncClient() as client:
                token_response = await client.post(
                    "https://oauth2.googleapis.com/token",
                    data={
                        "code": code,
                        "client_id": google_client_id,
                        "client_secret": google_client_secret,
                        "redirect_uri": redirect_uri,
                        "grant_type": "authorization_code",
                    }
                )

            if token_response.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Failed to exchange authorization code"
                )

            token_data = token_response.json()
            access_token = token_data.get("access_token")

            # Get user info
            async with httpx.AsyncClient() as client:
                user_response = await client.get(
                    "https://www.googleapis.com/oauth2/v2/userinfo",
                    headers={"Authorization": f"Bearer {access_token}"}
                )

            if user_response.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Failed to get user info from Google"
                )

            user_info = user_response.json()
            email = user_info.get("email")
            full_name = user_info.get("name", email)

            if not email:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Could not get email from Google"
                )

            # Get or create user
            from backend.repositories.user_repository import UserRepository
            from backend.models.user import User, UserRole
            from backend.core.security import create_token_pair

            user_repo = UserRepository(self.db)
            user = await user_repo.get_by_email(email)

            if not user:
                user = User(
                    email=email,
                    full_name=full_name,
                    password_hash=None,
                    role=UserRole.MEMBER.value,
                    email_verified=True,
                )
                user = await user_repo.create(user)
            elif not user.is_active:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Account is inactive"
                )

            tokens = create_token_pair(user.id, remember_me=True)
            return tokens

        except HTTPException:
            raise
        except Exception:
            logger.exception("Error handling Google OAuth callback")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="OAuth authentication failed"
            )
