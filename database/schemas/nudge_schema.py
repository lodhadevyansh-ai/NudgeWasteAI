"""
Nudge Database Schema.
Defines MongoDB persistence document schema for behavioural micro-nudge guidance.
"""

from datetime import datetime, timezone
from typing import Dict, Any, Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator
from database.utils.validators import convert_objectid_to_str, validate_statutory_category, validate_nudge_severity


class NudgeDocument(BaseModel):
    """Document schema for MongoDB nudges collection."""

    nudge_id: str = Field(..., alias="_id", description="Unique nudge UUID or ObjectId string")
    waste_category: str = Field(..., description="Predicted/input waste category")
    target_category: str = Field(..., description="Recommended statutory destination stream")
    title: str = Field(..., description="Encouraging micro-nudge title")
    message: str = Field(..., description="Primary micro-nudge message text")
    explanation: str = Field(..., description="Educational explanation of segregation risk")
    action: str = Field(..., description="Recommended concrete user action step")
    severity: str = Field(..., description="Severity level: 'information', 'guidance', or 'warning'")
    language: str = Field(default="en", description="Language code")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="UTC timestamp")
    disposal_id: Optional[str] = Field(default=None, description="Associated disposal ID")
    prediction_id: Optional[str] = Field(default=None, description="Associated prediction ID")

    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        from_attributes=True,
    )

    @field_validator("nudge_id", mode="before")
    @classmethod
    def validate_id_field(cls, v: Any) -> str:
        return convert_objectid_to_str(v)

    @field_validator("waste_category", "target_category")
    @classmethod
    def check_valid_category(cls, v: str) -> str:
        if not validate_statutory_category(v):
            raise ValueError(f"Invalid statutory category '{v}'. Must be one of: Wet, Dry, Sanitary, Special Care.")
        return v

    @field_validator("severity")
    @classmethod
    def check_valid_severity(cls, v: str) -> str:
        if not validate_nudge_severity(v):
            raise ValueError(f"Invalid severity '{v}'. Must be one of: information, guidance, warning.")
        return v

    def to_mongo_dict(self) -> Dict[str, Any]:
        """Serializes document for PyMongo storage."""
        doc = self.model_dump(by_alias=True)
        doc["_id"] = self.nudge_id
        doc["nudge_id"] = self.nudge_id
        return doc
