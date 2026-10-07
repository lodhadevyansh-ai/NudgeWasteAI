"""
Analytics Pydantic Schemas.
Data validation and response serialization models for platform municipal analytics, stream distributions, and trends.
"""

from datetime import datetime
from typing import Dict, Any, List
from pydantic import BaseModel, ConfigDict, Field


class AnalyticsSummaryResponse(BaseModel):
    """Platform-wide civic waste segregation summary metrics schema."""

    total_disposal_attempts: int = Field(..., ge=0, description="Total waste disposal events recorded")
    verified_disposals: int = Field(..., ge=0, description="Count of correctly verified disposals")
    correct_segregation_rate: float = Field(..., ge=0.0, le=100.0, description="Percentage of correctly segregated disposals")
    incorrect_segregation_count: int = Field(..., ge=0, description="Count of stream mismatches/incorrect disposals")
    uncertain_classification_count: int = Field(..., ge=0, description="Count of low confidence uncertain classifications")
    total_credits_issued: float = Field(..., ge=0.0, description="Total Swachh Credits issued to citizens")
    total_reward_redemptions: int = Field(..., ge=0, description="Total municipal reward vouchers redeemed")
    total_active_users: int = Field(..., ge=0, description="Total participating citizens")
    timestamp: datetime = Field(..., description="UTC timestamp of analytics calculation")

    model_config = ConfigDict(from_attributes=True)


class WasteDistributionResponse(BaseModel):
    """Distribution counts across the 4 statutory waste streams."""

    waste_counts_by_stream: Dict[str, int] = Field(..., description="Disposal counts for Wet, Dry, Sanitary, Special Care")
    stream_percentages: Dict[str, float] = Field(..., description="Percentage distribution for each statutory stream")
    total_count: int = Field(..., ge=0, description="Total volume of waste items recorded")

    model_config = ConfigDict(from_attributes=True)


class TrendsResponse(BaseModel):
    """Time-series daily disposal and segregation trend data."""

    daily_trends: List[Dict[str, Any]] = Field(..., description="Daily trend records containing date, total, verified, rate")
    period_days: int = Field(default=30, description="Analytics time window in days")

    model_config = ConfigDict(from_attributes=True)


class CreditsAnalyticsResponse(BaseModel):
    """Platform Swachh Credits issuance and redemption summary."""

    total_credits_issued: float = Field(..., ge=0.0, description="Total Swachh Credits issued")
    total_credits_redeemed: float = Field(..., ge=0.0, description="Total Swachh Credits redeemed for vouchers")
    net_circulating_credits: float = Field(..., ge=0.0, description="Current net circulating credits")
    total_redemption_vouchers: int = Field(..., ge=0, description="Total municipal incentive vouchers issued")
    credits_by_category: Dict[str, float] = Field(..., description="Credits issued per statutory category")

    model_config = ConfigDict(from_attributes=True)
