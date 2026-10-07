"""
User Database Schema.
Defines MongoDB persistence document schema for user accounts.
"""

from datetime import datetime, timezone
from typing import Optional, Dict, Any
from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator
from database.utils.validators import convert_objectid_to_str
from database.utils.timestamps import ensure_utc


class UserDocument(BaseModel):
    """Document schema for MongoDB users collection."""

    id: str = Field(..., alias="_id", description="Unique user ID string or ObjectId string")
    name: str = Field(..., min_length=2, max_length=100, description="User full name")
    email: EmailStr = Field(..., description="Unique email address")
    mobile: Optional[str] = Field(default=None, description="Optional mobile number")
    city: Optional[str] = Field(default="Indore Municipal Corporation", description="City or Municipality")
    hashed_password: str = Field(..., description="Bcrypt password hash")
    swachh_credits: float = Field(default=500.0, ge=0.0, description="Swachh Credits balance")
    status: str = Field(default="active", description="Account status")
    is_active: bool = Field(default=True, description="Account active flag")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Creation timestamp")
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Last update timestamp")

    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        from_attributes=True,
    )

    @field_validator("id", mode="before")
    @classmethod
    def validate_id_field(cls, v: Any) -> str:
        """Converts ObjectId or string ID to clean string representation."""
        return convert_objectid_to_str(v)

    @field_validator("email", mode="before")
    @classmethod
    def sanitize_email(cls, v: str) -> str:
        """Normalizes email to lowercase stripped string."""
        if isinstance(v, str):
            return v.strip().lower()
        return v

    @field_validator("created_at", "updated_at", mode="before")
    @classmethod
    def coerce_utc(cls, v: Any) -> Optional[datetime]:
        return ensure_utc(v)

    def to_mongo_dict(self) -> Dict[str, Any]:
        """Serializes document to PyMongo dictionary representation with _id."""
        doc = self.model_dump(by_alias=True)
        doc["_id"] = self.id
        doc["id"] = self.id
        return doc

    def to_public_dict(self) -> Dict[str, Any]:
        """Serializes document omitting secret password hash."""
        doc = self.model_dump(exclude={"hashed_password"})
        doc["id"] = self.id
        return doc
