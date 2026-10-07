"""
Prediction Pydantic Schemas.
Data validation and response serialization models for waste classification requests and results.
"""

from datetime import datetime
from typing import Dict, Optional, Any
from pydantic import BaseModel, ConfigDict, Field, field_validator
from app.utils.validators import validate_waste_category  # pyrefly: ignore [missing-import]
from database.utils.timestamps import ensure_utc


class PredictionRequest(BaseModel):
    """Payload schema for waste classification / prediction requests."""

    image_base64: Optional[str] = Field(default=None, description="Base64-encoded image string or camera frame")
    image_url: Optional[str] = Field(default=None, description="Remote image URL reference")
    item_label: Optional[str] = Field(default=None, description="Optional item label or text hint")
    min_confidence: Optional[float] = Field(
        default=0.60,
        ge=0.0,
        le=1.0,
        description="Minimum confidence threshold required (default: 0.60)",
    )


class PredictionResponse(BaseModel):
    """Response schema returned by the classification/prediction engine."""

    prediction_id: str = Field(..., description="Unique UUID for this prediction event")
    category: Optional[str] = Field(
        default=None,
        description="Predicted statutory category ('Wet', 'Dry', 'Sanitary', 'Special Care') or None if uncertain",
    )
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score between 0.0 and 1.0")
    is_uncertain: bool = Field(..., description="Flag indicating if prediction confidence is below required threshold")
    timestamp: datetime = Field(..., description="UTC timestamp of prediction execution")
    model_version: str = Field(..., description="Classification model version identifier")
    item_label: Optional[str] = Field(default=None, description="Recognized item label or description")
    processing_time_ms: float = Field(..., ge=0.0, description="Processing execution time in milliseconds")
    feedback_nudge: Optional[str] = Field(default=None, description="Civic disposal guidance or recapture nudge")
    all_probabilities: Optional[Dict[str, float]] = Field(
        default=None,
        description="Probability distribution across statutory waste categories",
    )

    model_config = ConfigDict(from_attributes=True)

    @field_validator("timestamp", mode="before")
    @classmethod
    def coerce_utc(cls, v: Any) -> Optional[datetime]:
        return ensure_utc(v)

    @field_validator("category")
    @classmethod
    def validate_category_value(cls, v: Optional[str]) -> Optional[str]:
        """Ensures that category, if present, is strictly one of the 4 statutory categories."""
        if v is not None and not validate_waste_category(v):
            raise ValueError(f"Invalid waste category '{v}'. Must be one of: Wet, Dry, Sanitary, Special Care.")
        return v
