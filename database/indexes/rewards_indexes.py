"""
Rewards Collection Index Definitions.
Supports reward catalog queries and user redemption voucher history.
"""

import pymongo
from pymongo.errors import OperationFailure
from database.connection.mongodb import get_collection
from database.config.collections_config import CollectionNames
from database.utils.logger import logger


def safe_create_index(col, keys, **kwargs) -> str:
    """Safely creates index, handling pre-existing index name conflicts."""
    try:
        return col.create_index(keys, **kwargs)
    except OperationFailure as exc:
        if exc.code == 85 or "Index already exists" in str(exc):
            logger.info(f"Index on {keys} already exists with different options/name. Using existing index.")
            return f"existing_{keys[0][0]}"
        raise


def create_rewards_indexes() -> list[str]:
    """
    Creates indexes for the 'rewards' catalog and 'reward_redemptions' collections.

    Indexes:
    1. Unique index on 'reward_id' in catalog collection.
    2. Index on 'is_available' in catalog collection.
    3. Unique index on 'redemption_id' in redemptions collection.
    4. Compound index on ('user_id', ASCENDING) and ('timestamp', DESCENDING) in redemptions collection.

    Returns:
        List of created index names across reward collections.
    """
    cat_col = get_collection(CollectionNames.REWARDS.value)
    red_col = get_collection(CollectionNames.REWARD_REDEMPTIONS.value)
    created = []

    idx_cat_id = safe_create_index(
        cat_col,
        [("reward_id", pymongo.ASCENDING)],
        unique=True,
        name="idx_rewards_catalog_id_unique",
    )
    created.append(f"rewards.{idx_cat_id}")

    idx_avail = safe_create_index(
        cat_col,
        [("is_available", pymongo.ASCENDING)],
        name="idx_rewards_catalog_available",
    )
    created.append(f"rewards.{idx_avail}")

    idx_red_id = safe_create_index(
        red_col,
        [("redemption_id", pymongo.ASCENDING)],
        unique=True,
        name="idx_reward_redemptions_id_unique",
    )
    created.append(f"reward_redemptions.{idx_red_id}")

    idx_red_user_ts = safe_create_index(
        red_col,
        [("user_id", pymongo.ASCENDING), ("timestamp", pymongo.DESCENDING)],
        name="idx_reward_redemptions_user_timestamp",
    )
    created.append(f"reward_redemptions.{idx_red_user_ts}")

    logger.info(f"Created/verified indexes for reward collections: {created}")
    return created
