"""
Swachh Credits Pydantic Schemas.
Data validation and response serialization models for user credit balances and auditable transaction logs.
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class CreditBalanceResponse(BaseModel):
    """User Swachh Credits balance summary schema."""

    user_id: str = Field(..., description="Unique user ID")
    swachh_credits: float = Field(..., ge=0.0, description="Current available Swachh Credits balance")
    total_earned: float = Field(default=0.0, ge=0.0, description="Lifetime total Swachh Credits earned")
    total_redeemed: float = Field(default=0.0, ge=0.0, description="Lifetime total Swachh Credits redeemed")
    updated_at: datetime = Field(..., description="UTC timestamp of last balance update")

    model_config = ConfigDict(from_attributes=True)


class CreditTransactionResponse(BaseModel):
    """Auditable credit transaction log schema."""

    transaction_id: str = Field(..., description="Unique UUID for this transaction event")
    user_id: str = Field(..., description="User ID associated with transaction")
    amount: float = Field(..., description="Credit transaction amount")
    transaction_type: str = Field(..., description="Transaction type ('earn', 'redeem', 'adjustment')")
    reason: str = Field(..., description="Auditable description for the credit change")
    disposal_id: Optional[str] = Field(default=None, description="Associated disposal ID if earned via disposal")
    reward_id: Optional[str] = Field(default=None, description="Associated reward ID if redeemed for incentive")
    balance_before: Optional[float] = Field(default=None, description="Credit balance prior to transaction")
    balance_after: Optional[float] = Field(default=None, description="Credit balance after transaction")
    timestamp: datetime = Field(..., description="UTC timestamp of transaction execution")

    model_config = ConfigDict(from_attributes=True)
