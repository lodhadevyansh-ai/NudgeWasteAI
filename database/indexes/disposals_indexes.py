"""
Disposals Collection Index Definitions.
Supports user disposal history pagination, prediction relationship lookups, and analytics aggregation pipelines.
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


def create_disposals_indexes() -> list[str]:
    """
    Creates indexes for the 'disposals' collection.

    Indexes:
    1. Unique index on 'disposal_id'.
    2. Compound index on ('user_id', ASCENDING) and ('timestamp', DESCENDING) for user disposal history pagination.
    3. Index on 'prediction_id' for classification event linking.
    4. Index on 'verification_status' and 'confirmed_category' for platform analytics aggregation.

    Returns:
        List of created index names.
    """
    col = get_collection(CollectionNames.DISPOSALS.value)
    created = []

    idx_id = safe_create_index(
        col,
        [("disposal_id", pymongo.ASCENDING)],
        unique=True,
        name="idx_disposals_id_unique",
    )
    created.append(idx_id)

    idx_user_ts = safe_create_index(
        col,
        [("user_id", pymongo.ASCENDING), ("timestamp", pymongo.DESCENDING)],
        name="idx_disposals_user_timestamp",
    )
    created.append(idx_user_ts)

    idx_pred = safe_create_index(
        col,
        [("prediction_id", pymongo.ASCENDING)],
        name="idx_disposals_prediction_id",
    )
    created.append(idx_pred)

    idx_status_cat = safe_create_index(
        col,
        [("verification_status", pymongo.ASCENDING), ("confirmed_category", pymongo.ASCENDING)],
        name="idx_disposals_status_cat_analytics",
    )
    created.append(idx_status_cat)

    logger.info(f"Created/verified indexes for '{CollectionNames.DISPOSALS.value}': {created}")
    return created
