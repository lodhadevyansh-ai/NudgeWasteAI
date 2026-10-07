"""
Analytics Database Schema.
Defines document schemas for pre-aggregated platform municipal analytics summaries and trend snapshots.
"""

from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class AnalyticsSummaryDocument(BaseModel):
    """Document schema for platform waste segregation metrics snapshots."""

    total_disposal_attempts: int = Field(..., ge=0, description="Total waste disposal events")
    verified_disposals: int = Field(..., ge=0, description="Count of verified correct disposals")
    correct_segregation_rate: float = Field(..., ge=0.0, le=100.0, description="Segregation success percentage")
    incorrect_segregation_count: int = Field(..., ge=0, description="Count of stream mismatches")
    uncertain_classification_count: int = Field(..., ge=0, description="Count of low confidence classifications")
    total_credits_issued: float = Field(..., ge=0.0, description="Total Swachh Credits issued")
    total_reward_redemptions: int = Field(..., ge=0, description="Total reward vouchers redeemed")
    total_active_users: int = Field(..., ge=0, description="Total participating citizens")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="UTC calculation timestamp")

    model_config = ConfigDict(
        populate_by_name=True,
        from_attributes=True,
    )

    def to_mongo_dict(self) -> Dict[str, Any]:
        return self.model_dump()
