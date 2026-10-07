"""
Nudges Collection Index Definitions.
Supports nudge ID lookups and relationship references.
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


def create_nudges_indexes() -> list[str]:
    """
    Creates indexes for the 'nudges' collection.

    Indexes:
    1. Unique index on 'nudge_id'.

    Returns:
        List of created index names.
    """
    col = get_collection(CollectionNames.NUDGES.value)
    created = []

    idx_id = safe_create_index(
        col,
        [("nudge_id", pymongo.ASCENDING)],
        unique=True,
        name="idx_nudges_id_unique",
    )
    created.append(idx_id)

    logger.info(f"Created/verified indexes for '{CollectionNames.NUDGES.value}': {created}")
    return created
