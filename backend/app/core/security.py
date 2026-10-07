"""
Security and Authentication Helpers.
Provides functions for password hashing/verification and JWT token generation/decoding.
"""

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional
import bcrypt
import jwt
from app.core.config import settings  # pyrefly: ignore [missing-import]
from app.utils.logger import logger  # pyrefly: ignore [missing-import]


def hash_password(password: str) -> str:
    """
    Hashes a raw password string using bcrypt.

    Args:
        password: Raw plaintext password.

    Returns:
        str: Bcrypt hashed password.
    """
    pwd_bytes = password.encode("utf-8")
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(pwd_bytes, salt)
    return hashed.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verifies a plaintext password against a stored bcrypt hash.

    Args:
        plain_password: Password input to verify.
        hashed_password: Stored bcrypt hash string.

    Returns:
        bool: True if password matches hash, False otherwise.
    """
    try:
        return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))
    except Exception as exc:
        logger.warning(f"Password verification failed: {exc}")
        return False


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """
    Creates a signed JWT access token containing subject data and expiration time.

    Args:
        data: Dictionary of claims to include in payload (e.g. {"sub": user_id, "email": email}).
        expires_delta: Optional custom token expiration duration.

    Returns:
        str: Encoded JWT token string.
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )
    return encoded_jwt


def decode_access_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Decodes and validates a JWT access token.

    Args:
        token: Signed JWT token string.

    Returns:
        Optional[Dict[str, Any]]: Token payload dict if valid, None if invalid or expired.
    """
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )
        return payload
    except jwt.PyJWTError as exc:
        logger.warning(f"JWT Token validation failed: {exc}")
        return None
