"""
Disposal Pydantic Schemas.
Data validation and response serialization models for waste disposal verification and event records.
"""

from datetime import datetime
from typing import Dict, Any, Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator
from app.utils.validators import validate_waste_category, validate_disposal_status  # pyrefly: ignore [missing-import]
from database.utils.timestamps import ensure_utc


class DisposalCreate(BaseModel):
    """Schema for recording a new waste disposal event."""

    prediction_id: str = Field(..., description="UUID reference of associated prediction event")
    predicted_category: Optional[str] = Field(default=None, description="Category predicted by classification engine")
    confirmed_category: Optional[str] = Field(
        default=None,
        description="Category confirmed by user/collector. Defaults to predicted_category if omitted.",
    )
    selected_bin_category: Optional[str] = Field(default=None, description="Selected bin stream category")
    confirmation_proof: Optional[str] = Field(default=None, description="Image or video disposal confirmation proof")
    confidence: Optional[float] = Field(default=0.85, ge=0.0, le=1.0, description="Classification confidence score")
    item_label: Optional[str] = Field(default=None, description="Optional waste item description")
    location_zone: Optional[str] = Field(default=None, description="Municipal zone / location identifier")
    device_metadata: Optional[Dict[str, Any]] = Field(default=None, description="Optional device source metadata")

    @field_validator("predicted_category", "confirmed_category", "selected_bin_category")
    @classmethod
    def check_valid_category(cls, v: Optional[str]) -> Optional[str]:
        """Ensures waste category is strictly one of the 4 statutory categories."""
        if v is not None and not validate_waste_category(v):
            raise ValueError(f"Invalid statutory waste category '{v}'. Must be one of: Wet, Dry, Sanitary, Special Care.")
        return v


class DisposalResponse(BaseModel):
    """Response schema representing a verified waste disposal event record."""

    disposal_id: str = Field(..., description="Unique UUID for this disposal record")
    user_id: str = Field(..., description="Authenticated user ID")
    prediction_id: str = Field(..., description="Reference prediction event ID")
    predicted_category: str = Field(..., description="Category predicted by ML model")
    confirmed_category: str = Field(..., description="Final category confirmed during disposal")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score")
    verification_status: str = Field(..., description="Verification result status")
    verified: bool = Field(default=True, description="Verification flag")
    is_correctly_segregated: bool = Field(..., description="Flag indicating if item was correctly segregated into statutory stream")
    feedback_nudge: str = Field(..., description="Civic segregation nudge or status feedback")
    item_label: Optional[str] = Field(default=None, description="Item label")
    location_zone: Optional[str] = Field(default=None, description="Location/zone identifier")
    timestamp: datetime = Field(..., description="UTC timestamp of disposal event")
    credits_awarded: float = Field(default=0.0, description="Swachh credits awarded")

    # Real Bin Verification Details
    expected_category: Optional[str] = Field(default=None, description="Expected statutory category")
    expected_bin: Optional[str] = Field(default=None, description="Expected bin stream/color")
    detected_category: Optional[str] = Field(default=None, description="Detected waste category")
    detected_bin: Optional[str] = Field(default=None, description="Detected bin color/stream")
    error_code: Optional[str] = Field(default=None, description="Verification error code if rejected")
    message: Optional[str] = Field(default=None, description="Detailed verification status message")

    @field_validator("timestamp", mode="before")
    @classmethod
    def coerce_utc(cls, v: Any) -> Optional[datetime]:
        return ensure_utc(v)

    @field_validator("verification_status")
    @classmethod
    def check_valid_status(cls, v: str) -> str:
        """Ensures verification status matches recognized system status constants."""
        if not validate_disposal_status(v):
            raise ValueError(f"Invalid disposal status '{v}'.")
        return v
