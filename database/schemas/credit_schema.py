"""
Swachh Credit Database Schema.
Defines MongoDB persistence document schema for auditable credit transactions.
"""

from datetime import datetime, timezone
from typing import Dict, Any, Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator
from database.utils.validators import convert_objectid_to_str, validate_transaction_type
from database.utils.timestamps import ensure_utc


class CreditTransactionDocument(BaseModel):
    """Document schema for MongoDB credit_transactions collection."""

    transaction_id: str = Field(..., alias="_id", description="Unique transaction UUID or ObjectId string")
    user_id: str = Field(..., description="User ID associated with credit transaction")
    amount: float = Field(..., description="Transaction amount (positive for earn, negative for redeem)")
    transaction_type: str = Field(..., description="Type of transaction ('earn', 'redeem', 'adjustment')")
    reason: str = Field(..., description="Auditable description for credit change")
    disposal_id: Optional[str] = Field(default=None, description="Reference disposal ID if earned")
    reward_id: Optional[str] = Field(default=None, description="Reference reward ID if redeemed")
    balance_before: Optional[float] = Field(default=None, description="User balance prior to transaction execution")
    balance_after: Optional[float] = Field(default=None, description="User balance after transaction execution")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="UTC timestamp")

    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        from_attributes=True,
    )

    @field_validator("transaction_id", mode="before")
    @classmethod
    def validate_id_field(cls, v: Any) -> str:
        return convert_objectid_to_str(v)

    @field_validator("transaction_type")
    @classmethod
    def check_valid_type(cls, v: str) -> str:
        if not validate_transaction_type(v):
            raise ValueError(f"Invalid transaction type '{v}'. Must be one of: earn, redeem, adjustment.")
        return v

    @field_validator("timestamp", mode="before")
    @classmethod
    def coerce_utc(cls, v: Any) -> Optional[datetime]:
        return ensure_utc(v)

    def to_mongo_dict(self) -> Dict[str, Any]:
        """Serializes document for PyMongo storage."""
        doc = self.model_dump(by_alias=True)
        doc["_id"] = self.transaction_id
        doc["transaction_id"] = self.transaction_id
        return doc
