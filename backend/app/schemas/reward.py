"""
Municipal Rewards Pydantic Schemas.
Data validation and response serialization models for municipal incentive catalog and user redemptions.
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class RewardResponse(BaseModel):
    """Municipal incentive reward catalog item schema."""

    reward_id: str = Field(..., description="Unique reward identifier")
    title: str = Field(..., description="Incentive title (e.g., Property Tax Rebate Voucher)")
    description: str = Field(..., description="Detailed description of the municipal incentive")
    credit_cost: float = Field(..., gt=0.0, description="Swachh Credits required for redemption")
    cost_credits: Optional[float] = Field(default=None, description="Alias for credit_cost")
    reward_type: str = Field(..., description="Category type (tax_discount, transit_pass, utility_rebate, eco_voucher)")
    is_available: bool = Field(default=True, description="Reward availability flag")

    model_config = ConfigDict(from_attributes=True)


class RewardRedemptionResponse(BaseModel):
    """Record of a successful reward redemption event."""

    redemption_id: str = Field(..., description="Unique UUID for this redemption record")
    user_id: str = Field(..., description="User ID who redeemed the reward")
    reward_id: str = Field(..., description="ID of the redeemed reward")
    reward_title: str = Field(..., description="Title of the redeemed reward")
    credit_cost: float = Field(..., description="Swachh Credits deducted for redemption")
    redemption_code: str = Field(..., description="Voucher/claim code for municipal redemption")
    status: str = Field(default="active", description="Redemption status (active, used, expired)")
    timestamp: datetime = Field(..., description="UTC timestamp of redemption execution")

    model_config = ConfigDict(from_attributes=True)
