"""
Database indexes package exports.
"""

from database.indexes.users_indexes import create_users_indexes
from database.indexes.waste_indexes import create_waste_indexes
from database.indexes.predictions_indexes import create_predictions_indexes
from database.indexes.disposals_indexes import create_disposals_indexes
from database.indexes.nudges_indexes import create_nudges_indexes
from database.indexes.credits_indexes import create_credits_indexes
from database.indexes.rewards_indexes import create_rewards_indexes
from database.indexes.analytics_indexes import create_analytics_indexes


def create_all_indexes() -> dict[str, list[str]]:
    """
    Creates indexes across all MongoDB collections in NudgeWasteAI.

    Returns:
        Dict mapping collection names to created index names.
    """
    results = {
        "users": create_users_indexes(),
        "waste": create_waste_indexes(),
        "predictions": create_predictions_indexes(),
        "disposals": create_disposals_indexes(),
        "nudges": create_nudges_indexes(),
        "credits": create_credits_indexes(),
        "rewards": create_rewards_indexes(),
        "analytics": create_analytics_indexes(),
    }
    return results


__all__ = [
    "create_users_indexes",
    "create_waste_indexes",
    "create_predictions_indexes",
    "create_disposals_indexes",
    "create_nudges_indexes",
    "create_credits_indexes",
    "create_rewards_indexes",
    "create_analytics_indexes",
    "create_all_indexes",
]
