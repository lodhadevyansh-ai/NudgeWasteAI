"""
Predictions Collection Index Definitions.
Supports classification prediction event lookup and history queries.
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


def create_predictions_indexes() -> list[str]:
    """
    Creates indexes for the 'predictions' collection.

    Indexes:
    1. Unique index on 'prediction_id'.
    2. Index on 'timestamp' DESC for chronological querying.

    Returns:
        List of created index names.
    """
    col = get_collection(CollectionNames.PREDICTIONS.value)
    created = []

    idx_id = safe_create_index(
        col,
        [("prediction_id", pymongo.ASCENDING)],
        unique=True,
        name="idx_predictions_id_unique",
    )
    created.append(idx_id)

    idx_ts = safe_create_index(
        col,
        [("timestamp", pymongo.DESCENDING)],
        name="idx_predictions_timestamp_desc",
    )
    created.append(idx_ts)

    logger.info(f"Created/verified indexes for '{CollectionNames.PREDICTIONS.value}': {created}")
    return created
