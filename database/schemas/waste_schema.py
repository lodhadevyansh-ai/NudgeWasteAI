"""
Waste Stream Database Schema.
Defines document schema for the 4 statutory waste stream categories.
"""

from typing import Dict, Any
from pydantic import BaseModel, ConfigDict, Field, field_validator
from database.utils.validators import validate_statutory_category


class WasteStreamDocument(BaseModel):
    """Document schema for statutory waste stream rules and guidance."""

    category: str = Field(..., description="Statutory waste category ('Wet', 'Dry', 'Sanitary', 'Special Care')")
    description: str = Field(..., description="Category description and examples")
    bin_color: str = Field(..., description="Municipal bin color identifier (Green, Blue, Red, Black)")
    credit_award: float = Field(..., ge=0.0, description="Default Swachh Credits award for correct disposal")
    guidance_nudge: str = Field(..., description="Default civic segregation guidance text")

    model_config = ConfigDict(
        populate_by_name=True,
        from_attributes=True,
    )

    @field_validator("category")
    @classmethod
    def check_valid_category(cls, v: str) -> str:
        """Validates that category is strictly one of the 4 statutory categories."""
        if not validate_statutory_category(v):
            raise ValueError(f"Invalid statutory waste category '{v}'. Must be one of: Wet, Dry, Sanitary, Special Care.")
        return v

    def to_mongo_dict(self) -> Dict[str, Any]:
        """Serializes document for PyMongo storage."""
        doc = self.model_dump()
        doc["_id"] = self.category
        return doc
