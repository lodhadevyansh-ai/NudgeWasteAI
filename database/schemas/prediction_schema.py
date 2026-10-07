"""
Prediction Database Schema.
Defines MongoDB persistence document schema for waste classification predictions.
"""

from datetime import datetime, timezone
from typing import Dict, Any, Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator
from database.utils.validators import convert_objectid_to_str, validate_statutory_category
from database.utils.timestamps import ensure_utc


class PredictionDocument(BaseModel):
    """Document schema for MongoDB predictions collection."""

    prediction_id: str = Field(..., alias="_id", description="Unique prediction UUID or ObjectId string")
    user_id: Optional[str] = Field(default=None, description="Optional user ID if authenticated")
    category: Optional[str] = Field(default=None, description="Predicted category or None if uncertain")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Classification confidence score")
    is_uncertain: bool = Field(..., description="Flag indicating if prediction confidence is below threshold")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="UTC timestamp")
    model_version: str = Field(..., description="Classification model version string")
    item_label: Optional[str] = Field(default=None, description="Recognized item label")
    processing_time_ms: float = Field(..., ge=0.0, description="Execution time in milliseconds")
    feedback_nudge: Optional[str] = Field(default=None, description="Civic disposal guidance nudge")
    all_probabilities: Optional[Dict[str, float]] = Field(default=None, description="Category probability distribution")

    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        from_attributes=True,
    )

    @field_validator("prediction_id", mode="before")
    @classmethod
    def validate_id_field(cls, v: Any) -> str:
        return convert_objectid_to_str(v)

    @field_validator("category")
    @classmethod
    def check_valid_category(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and not validate_statutory_category(v):
            raise ValueError(f"Invalid statutory waste category '{v}'. Must be one of: Wet, Dry, Sanitary, Special Care.")
        return v

    @field_validator("timestamp", mode="before")
    @classmethod
    def coerce_utc(cls, v: Any) -> Optional[datetime]:
        return ensure_utc(v)

    def to_mongo_dict(self) -> Dict[str, Any]:
        """Serializes document to PyMongo dictionary format."""
        doc = self.model_dump(by_alias=True)
        doc["_id"] = self.prediction_id
        doc["prediction_id"] = self.prediction_id
        return doc
