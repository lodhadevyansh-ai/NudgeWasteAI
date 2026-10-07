"""
Users Collection Index Definitions.
Supports unique email lookups, authentication, and user profile queries.
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
            logger.info(f"Index on {keys} already exists with different options/name ({exc.details.get('errmsg', str(exc))}). Using existing index.")
            return f"existing_{keys[0][0]}"
        raise


def create_users_indexes() -> list[str]:
    """
    Creates indexes for the 'users' collection.

    Indexes:
    1. Unique index on 'email' (lowercased normalization for login lookup).
    2. Unique index on 'id' / '_id' for direct user profile lookup.

    Returns:
        List of created index names.
    """
    col = get_collection(CollectionNames.USERS.value)
    created = []

    # 1. Unique index on email
    idx_email = safe_create_index(
        col,
        [("email", pymongo.ASCENDING)],
        unique=True,
        name="idx_users_email_unique",
    )
    created.append(idx_email)

    # 2. Unique index on domain ID
    idx_id = safe_create_index(
        col,
        [("id", pymongo.ASCENDING)],
        unique=True,
        name="idx_users_id_unique",
    )
    created.append(idx_id)

    logger.info(f"Created/verified indexes for '{CollectionNames.USERS.value}': {created}")
    return created
