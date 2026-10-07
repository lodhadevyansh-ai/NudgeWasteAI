"""
API Dependencies.
Reusable dependency foundations for route handlers, authentication, and database access.
"""

from typing import Dict, Any
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pymongo.database import Database

from app.core.config import settings  # pyrefly: ignore [missing-import]
from app.core.security import decode_access_token  # pyrefly: ignore [missing-import]
from app.schemas.user import UserResponse  # pyrefly: ignore [missing-import]
from app.services.user_service import user_service  # pyrefly: ignore [missing-import]

from database.connection import get_db  # pyrefly: ignore [missing-import]

security_bearer = HTTPBearer(auto_error=True)


async def get_app_settings() -> Dict[str, Any]:
    """Dependency helper to provide global application settings."""
    return {
        "app_name": settings.APP_NAME,
        "environment": settings.ENVIRONMENT,
        "debug": settings.DEBUG,
        "version": settings.APP_VERSION,
    }


async def get_db_session() -> Database:
    """Dependency helper providing access to the shared MongoDB database connection."""
    return get_db()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security_bearer),
) -> UserResponse:
    """
    Validates JWT Bearer token and retrieves current authenticated user.

    Raises:
        HTTPException 401: If token is missing, invalid, or expired.
        HTTPException 400: If user account is inactive.
    """
    token = credentials.credentials
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials or token expired",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id: str | None = payload.get("sub") or payload.get("user_id")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = user_service.get_user_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user account",
        )

    return UserResponse.model_validate(user.model_dump())
