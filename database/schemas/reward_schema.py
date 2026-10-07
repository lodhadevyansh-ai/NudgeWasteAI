"""
Municipal Rewards Database Schema.
Defines MongoDB document schemas for municipal reward catalog items and user redemptions.
"""

from datetime import datetime, timezone
from typing import Dict, Any, Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator
from database.utils.validators import convert_objectid_to_str


class RewardCatalogDocument(BaseModel):
    """Document schema for MongoDB rewards catalog items collection."""

    reward_id: str = Field(..., alias="_id", description="Unique reward identifier")
    title: str = Field(..., description="Incentive title")
    description: str = Field(..., description="Incentive description")
    credit_cost: float = Field(..., gt=0.0, description="Swachh Credits required for redemption")
    reward_type: str = Field(..., description="Category type (tax_discount, transit_pass, utility_rebate, eco_voucher)")
    is_available: bool = Field(default=True, description="Availability flag")

    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        from_attributes=True,
    )

    @field_validator("reward_id", mode="before")
    @classmethod
    def validate_id_field(cls, v: Any) -> str:
        return convert_objectid_to_str(v)

    def to_mongo_dict(self) -> Dict[str, Any]:
        doc = self.model_dump(by_alias=True)
        doc["_id"] = self.reward_id
        doc["reward_id"] = self.reward_id
        return doc


class RewardRedemptionDocument(BaseModel):
    """Document schema for MongoDB reward_redemptions collection."""

    redemption_id: str = Field(..., alias="_id", description="Unique redemption record UUID or ObjectId string")
    user_id: str = Field(..., description="Authenticated user ID who redeemed reward")
    reward_id: str = Field(..., description="ID of redeemed reward")
    reward_title: str = Field(..., description="Title of redeemed reward")
    credit_cost: float = Field(..., gt=0.0, description="Credits deducted for redemption")
    redemption_code: str = Field(..., description="Voucher / claim code")
    status: str = Field(default="active", description="Redemption status (active, used, expired)")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="UTC timestamp")

    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        from_attributes=True,
    )

    @field_validator("redemption_id", mode="before")
    @classmethod
    def validate_id_field(cls, v: Any) -> str:
        return convert_objectid_to_str(v)

    def to_mongo_dict(self) -> Dict[str, Any]:
        doc = self.model_dump(by_alias=True)
        doc["_id"] = self.redemption_id
        doc["redemption_id"] = self.redemption_id
        return doc
