"""
User Pydantic Schemas.
Data validation and serialization models for user registration, authentication, profiles, and tokens.
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserBase(BaseModel):
    """Base user schema with common attributes."""

    name: str = Field(..., min_length=2, max_length=100, description="Full name of the user")
    email: EmailStr = Field(..., description="Unique email address")
    mobile: Optional[str] = Field(default=None, description="Optional mobile phone number")
    city: Optional[str] = Field(default="Indore Municipal Corporation", description="City or Municipality")


class UserRegister(UserBase):
    """Schema for user registration payload."""

    password: str = Field(..., min_length=6, max_length=128, description="User password (min 6 characters)")


class UserLogin(BaseModel):
    """Schema for user login credentials payload."""

    email: EmailStr = Field(..., description="Registered email address")
    password: str = Field(..., description="User password")


class UserUpdate(BaseModel):
    """Schema for updating user profile."""

    name: Optional[str] = Field(default=None, min_length=2, max_length=100)
    mobile: Optional[str] = Field(default=None)
    city: Optional[str] = Field(default=None)
    password: Optional[str] = Field(default=None, min_length=6, max_length=128)


class UserResponse(UserBase):
    """Public user response schema (never exposes password or password hashes)."""

    id: str = Field(..., description="Unique user ID")
    swachh_credits: float = Field(default=500.0, description="Swachh Credits balance")
    status: str = Field(default="active", description="Account status (active, suspended, etc.)")
    is_active: bool = Field(default=True, description="Account active status flag")
    created_at: datetime = Field(..., description="Account creation timestamp")
    updated_at: datetime = Field(..., description="Last profile update timestamp")

    model_config = ConfigDict(from_attributes=True)


class UserInDB(UserBase):
    """Internal user model representation stored in database."""

    id: str
    hashed_password: str
    swachh_credits: float = 500.0
    status: str = "active"
    is_active: bool = True
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class Token(BaseModel):
    """JWT Access Token response model."""

    access_token: str = Field(..., description="JWT Bearer access token")
    token_type: str = Field(default="bearer", description="Token type")


class TokenData(BaseModel):
    """Data payload embedded inside JWT tokens."""

    user_id: Optional[str] = None
    email: Optional[str] = None
