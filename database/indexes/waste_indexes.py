"""
Waste Collection Index Definitions.
Supports statutory waste stream category queries.
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


def create_waste_indexes() -> list[str]:
    """
    Creates indexes for the 'waste' collection.

    Indexes:
    1. Unique index on 'category' ('Wet', 'Dry', 'Sanitary', 'Special Care').

    Returns:
        List of created index names.
    """
    col = get_collection(CollectionNames.WASTE.value)
    created = []

    idx_cat = safe_create_index(
        col,
        [("category", pymongo.ASCENDING)],
        unique=True,
        name="idx_waste_category_unique",
    )
    created.append(idx_cat)

    logger.info(f"Created/verified indexes for '{CollectionNames.WASTE.value}': {created}")
    return created
