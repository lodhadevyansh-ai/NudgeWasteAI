"""
Nudge Pydantic Schemas.
Data validation and response models for behavioural nudge generation and educational feedback.
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator
from app.utils.validators import validate_waste_category  # pyrefly: ignore [missing-import]
from app.core.constants import NUDGE_SEVERITIES  # pyrefly: ignore [missing-import]


class NudgeRequest(BaseModel):
    """Payload for generating a localized behavioural nudge."""

    predicted_category: str = Field(..., description="Category predicted by classification model")
    confirmed_category: Optional[str] = Field(default=None, description="Category confirmed during disposal")
    confidence: Optional[float] = Field(default=0.85, ge=0.0, le=1.0, description="Prediction confidence score")
    item_label: Optional[str] = Field(default=None, description="Optional waste item description")
    disposal_id: Optional[str] = Field(default=None, description="Optional reference disposal ID")
    prediction_id: Optional[str] = Field(default=None, description="Optional reference prediction ID")
    language: Optional[str] = Field(default="en", description="ISO Language code for future localization (e.g. en, hi, kn)")

    @field_validator("predicted_category", "confirmed_category")
    @classmethod
    def check_valid_category(cls, v: Optional[str]) -> Optional[str]:
        """Ensures waste category is strictly one of the 4 statutory categories."""
        if v is not None and not validate_waste_category(v):
            raise ValueError(f"Invalid statutory category '{v}'. Must be one of: Wet, Dry, Sanitary, Special Care.")
        return v


class NudgeResponse(BaseModel):
    """Structured Nudge response model designed for frontend display."""

    nudge_id: str = Field(..., description="Unique UUID for this nudge event")
    waste_category: str = Field(..., description="Detected/input waste category")
    target_category: str = Field(..., description="Recommended statutory destination stream")
    title: str = Field(..., description="Encouraging micro-nudge title")
    message: str = Field(..., description="Primary behavioural micro-nudge text")
    explanation: str = Field(..., description="Educational explanation of why segregation matters and contamination risk")
    action: str = Field(..., description="Recommended concrete user action step")
    severity: str = Field(..., description="Severity level: 'information', 'guidance', or 'warning'")
    language: str = Field(default="en", description="Language code")
    timestamp: datetime = Field(..., description="UTC timestamp of nudge creation")
    disposal_id: Optional[str] = Field(default=None, description="Associated disposal ID reference")
    prediction_id: Optional[str] = Field(default=None, description="Associated prediction ID reference")

    model_config = ConfigDict(from_attributes=True)

    @field_validator("severity")
    @classmethod
    def check_severity_value(cls, v: str) -> str:
        """Validates that severity is one of 'information', 'guidance', or 'warning'."""
        if v not in NUDGE_SEVERITIES:
            raise ValueError(f"Invalid severity '{v}'. Must be one of: {NUDGE_SEVERITIES}")
        return v
