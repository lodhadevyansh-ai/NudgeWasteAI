"""
Disposal Database Schema.
Defines MongoDB persistence document schema for verified waste disposal event records.
"""

from datetime import datetime, timezone
from typing import Dict, Any, Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator
from database.utils.validators import convert_objectid_to_str, validate_statutory_category, validate_disposal_status
from database.utils.timestamps import ensure_utc


class DisposalDocument(BaseModel):
    """Document schema for MongoDB disposals collection."""

    disposal_id: str = Field(..., alias="_id", description="Unique disposal UUID or ObjectId string")
    user_id: str = Field(..., description="Authenticated user ID")
    prediction_id: str = Field(..., description="Reference prediction event UUID")
    predicted_category: str = Field(..., description="Predicted category from classification engine")
    confirmed_category: str = Field(..., description="Confirmed category during disposal")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score")
    verification_status: str = Field(..., description="Verification status (verified, incorrect, uncertain, pending)")
    is_correctly_segregated: bool = Field(..., description="Flag indicating correct statutory stream placement")
    feedback_nudge: str = Field(..., description="Civic segregation nudge message")
    item_label: Optional[str] = Field(default=None, description="Optional waste item description")
    location_zone: Optional[str] = Field(default=None, description="Location zone identifier")
    device_metadata: Optional[Dict[str, Any]] = Field(default=None, description="Device source metadata")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="UTC timestamp")
    credits_awarded: float = Field(default=0.0, ge=0.0, description="Swachh Credits awarded for this disposal")
    expected_category: Optional[str] = Field(default=None, description="Expected statutory waste category")
    expected_bin: Optional[str] = Field(default=None, description="Expected bin color/name")
    detected_bin: Optional[str] = Field(default=None, description="Detected bin color/name")
    detected_category: Optional[str] = Field(default=None, description="Detected waste stream category")
    verification_confidence: Optional[float] = Field(default=None, description="Bin verification confidence score")
    evidence_type: Optional[str] = Field(default=None, description="Evidence type (image or video)")
    rejection_reason: Optional[str] = Field(default=None, description="Rejection reason or error code")

    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        from_attributes=True,
    )

    @field_validator("disposal_id", mode="before")
    @classmethod
    def validate_id_field(cls, v: Any) -> str:
        return convert_objectid_to_str(v)

    @field_validator("predicted_category", "confirmed_category")
    @classmethod
    def check_valid_category(cls, v: str) -> str:
        if not validate_statutory_category(v):
            raise ValueError(f"Invalid statutory waste category '{v}'. Must be one of: Wet, Dry, Sanitary, Special Care.")
        return v

    @field_validator("timestamp", mode="before")
    @classmethod
    def coerce_utc(cls, v: Any) -> Optional[datetime]:
        return ensure_utc(v)

    @field_validator("verification_status")
    @classmethod
    def check_valid_status(cls, v: str) -> str:
        if not validate_disposal_status(v):
            raise ValueError(f"Invalid disposal status '{v}'. Must be one of: verified, incorrect, uncertain, pending.")
        return v

    def to_mongo_dict(self) -> Dict[str, Any]:
        """Serializes document for PyMongo storage."""
        doc = self.model_dump(by_alias=True)
        doc["_id"] = self.disposal_id
        doc["disposal_id"] = self.disposal_id
        return doc
