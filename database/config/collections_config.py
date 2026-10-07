"""
Collection Names Configuration.
Centralized source of truth for all MongoDB collection names used across NudgeWasteAI.
"""

from enum import Enum


class CollectionNames(str, Enum):
    """Statutory and platform MongoDB collection name constants."""

    USERS = "users"
    DISPOSALS = "disposals"
    NUDGES = "nudges"
    CREDIT_TRANSACTIONS = "credit_transactions"
    CREDITS = "credit_transactions"
    REWARDS = "rewards"
    REWARD_REDEMPTIONS = "reward_redemptions"
    PREDICTIONS = "predictions"
    WASTE = "waste"


COLLECTIONS = {
    "users": CollectionNames.USERS.value,
    "disposals": CollectionNames.DISPOSALS.value,
    "nudges": CollectionNames.NUDGES.value,
    "credits": CollectionNames.CREDIT_TRANSACTIONS.value,
    "credit_transactions": CollectionNames.CREDIT_TRANSACTIONS.value,
    "rewards": CollectionNames.REWARDS.value,
    "reward_redemptions": CollectionNames.REWARD_REDEMPTIONS.value,
    "predictions": CollectionNames.PREDICTIONS.value,
    "waste": CollectionNames.WASTE.value,
}
