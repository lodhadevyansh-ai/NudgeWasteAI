"""
Municipal Reward Service.
Manages municipal incentive catalog, credit redemption logic, and voucher generation using database collections.
"""

from datetime import datetime, timezone
import uuid
from typing import Dict, Any, List, Optional

from app.schemas.reward import RewardResponse, RewardRedemptionResponse  # pyrefly: ignore [missing-import]
from app.services.credits_service import credits_service  # pyrefly: ignore [missing-import]
from app.utils.logger import logger  # pyrefly: ignore [missing-import]

from database.collections.rewards import rewards_collection  # pyrefly: ignore [missing-import]
from database.schemas.reward_schema import RewardRedemptionDocument, RewardCatalogDocument  # pyrefly: ignore [missing-import]

DEFAULT_MUNICIPAL_REWARDS: List[Dict[str, Any]] = [
    {
        "reward_id": "reward_tax_5pct",
        "title": "Property Tax Rebate Voucher (5%)",
        "description": "Redeemable for a 5% discount on municipal property tax assessment.",
        "credit_cost": 100.0,
        "cost_credits": 100.0,
        "reward_type": "tax_discount",
        "is_available": True,
    },
    {
        "reward_id": "reward_tax_10pct",
        "title": "10% Property Tax Rebate",
        "description": "Direct deduction from annual residential property tax assessment.",
        "credit_cost": 500.0,
        "cost_credits": 500.0,
        "reward_type": "tax_discount",
        "is_available": True,
    },
    {
        "reward_id": "reward_transit_pass",
        "title": "Metro Rail Monthly Pass Voucher",
        "description": "Recharge voucher for city metro rail transit pass.",
        "credit_cost": 750.0,
        "cost_credits": 750.0,
        "reward_type": "transit_pass",
        "is_available": True,
    },
    {
        "reward_id": "reward_compost_5kg",
        "title": "Organic Fertilizer 5kg Pack",
        "description": "Claim 5kg rich organic compost produced at municipal processing plants.",
        "credit_cost": 300.0,
        "cost_credits": 300.0,
        "reward_type": "eco_voucher",
        "is_available": True,
    },
    {
        "reward_id": "reward_jute_bags",
        "title": "Eco Jute Shopping Bag Set",
        "description": "Durable eco-friendly jute shopping bags to reduce single-use plastic.",
        "credit_cost": 200.0,
        "cost_credits": 200.0,
        "reward_type": "merchandise",
        "is_available": True,
    },
]


class RewardService:
    """Service layer managing municipal reward catalog and user redemptions."""

    def __init__(self):
        self._rewards_catalog: Dict[str, Dict[str, Any]] = {str(r["reward_id"]): r for r in DEFAULT_MUNICIPAL_REWARDS}
        self._in_memory_redemptions: Dict[str, Dict[str, Any]] = {}

    def get_available_rewards(self) -> List[RewardResponse]:
        """Retrieves list of active municipal rewards."""
        try:
            db_rewards = rewards_collection.get_available_rewards()
            if db_rewards:
                return [RewardResponse(**r.to_mongo_dict()) for r in db_rewards]
        except Exception as exc:
            logger.warning(f"MongoDB catalog query warning: {exc}")

        return [RewardResponse(**r) for r in self._rewards_catalog.values() if r.get("is_available", True)]

    def get_reward_by_id(self, reward_id: str) -> Optional[RewardResponse]:
        """Retrieves a single reward from catalog."""
        try:
            db_reward = rewards_collection.get_reward_by_id(reward_id)
            if db_reward:
                return RewardResponse(**db_reward.to_mongo_dict())
        except Exception as exc:
            logger.warning(f"MongoDB get_reward_by_id warning: {exc}")

        r = self._rewards_catalog.get(reward_id)
        return RewardResponse(**r) if r else None

    def redeem_reward(self, user_id: str, reward_id: str) -> RewardRedemptionResponse:
        """
        Redeems a municipal reward using user's Swachh Credits.

        Raises:
            ValueError: If reward_id is invalid or user has insufficient credits.
        """
        reward = self.get_reward_by_id(reward_id)
        if not reward or not reward.is_available:
            raise ValueError(f"Reward '{reward_id}' is invalid or unavailable for redemption")

        cost = float(reward.credit_cost)
        reason = f"Redeemed {reward.title}"

        # Deduct credits atomically via credits_service (validates sufficient balance)
        credits_service.deduct_credits(user_id=user_id, amount=cost, reason=reason, reward_id=reward_id)

        redemption_id = str(uuid.uuid4())
        voucher_code = f"SWACHH-{reward.reward_type.upper()[:4]}-{uuid.uuid4().hex[:8].upper()}"
        now = datetime.now(timezone.utc)

        redemption_doc_dict = {
            "_id": redemption_id,
            "redemption_id": redemption_id,
            "user_id": user_id,
            "reward_id": reward_id,
            "reward_title": reward.title,
            "credit_cost": cost,
            "redemption_code": voucher_code,
            "status": "active",
            "timestamp": now,
        }

        try:
            doc = RewardRedemptionDocument(**redemption_doc_dict)
            rewards_collection.create_redemption(doc)
        except Exception as exc:
            logger.warning(f"MongoDB redemption insert warning: {exc}")

        self._in_memory_redemptions[redemption_id] = redemption_doc_dict
        logger.info(f"User {user_id} redeemed reward '{reward_id}' ({voucher_code})")

        return RewardRedemptionResponse(**redemption_doc_dict)

    def get_user_redemptions(self, user_id: str) -> List[RewardRedemptionResponse]:
        """Retrieves redemption history exclusively for the authenticated user."""
        try:
            db_reds = rewards_collection.get_user_redemptions(user_id)
            if db_reds:
                return [RewardRedemptionResponse(**r.to_mongo_dict()) for r in db_reds]
        except Exception as exc:
            logger.warning(f"MongoDB redemption search warning: {exc}")

        user_reds = [r for r in self._in_memory_redemptions.values() if r["user_id"] == user_id]
        user_reds.sort(key=lambda x: x["timestamp"], reverse=True)
        return [RewardRedemptionResponse(**r) for r in user_reds]


# Singleton instance
reward_service = RewardService()
