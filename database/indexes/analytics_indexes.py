"""
Analytics Collection Index Definitions.
Supports platform dashboard aggregation queries across disposals, users, and redemptions.
"""

from database.indexes.disposals_indexes import create_disposals_indexes
from database.indexes.credits_indexes import create_credits_indexes
from database.indexes.rewards_indexes import create_rewards_indexes
from database.utils.logger import logger


def create_analytics_indexes() -> list[str]:
    """
    Ensures composite indexes required for analytics pipelines exist.

    Returns:
        List of created index names supporting analytics.
    """
    created = []
    created.extend(create_disposals_indexes())
    created.extend(create_credits_indexes())
    created.extend(create_rewards_indexes())
    logger.info("Ensured all indexes supporting platform analytics aggregation pipelines exist.")
    return created
