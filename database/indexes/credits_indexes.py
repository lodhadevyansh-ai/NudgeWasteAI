"""
Credits Collection Index Definitions.
Supports duplicate credit award prevention and user transaction log pagination.
"""

import pymongo
from pymongo.errors import OperationFailure, DuplicateKeyError
from database.connection.mongodb import get_collection
from database.config.collections_config import CollectionNames
from database.utils.logger import logger


def safe_create_index(col, keys, **kwargs) -> str:
    """Safely creates index, handling pre-existing index name conflicts or partial index options."""
    try:
        return col.create_index(keys, **kwargs)
    except (OperationFailure, DuplicateKeyError) as exc:
        err_msg = str(exc)
        if getattr(exc, "code", None) == 85 or "Index already exists" in err_msg:
            logger.info(f"Index on {keys} already exists with different options/name. Using existing index.")
            return f"existing_{keys[0][0]}"
        elif getattr(exc, "code", None) == 11000 or "duplicate key error" in err_msg:
            logger.warning(f"Index build on {keys} skipped due to existing duplicate keys ({err_msg}).")
            return f"skipped_{keys[0][0]}"
        raise


def create_credits_indexes() -> list[str]:
    """
    Creates indexes for the 'credit_transactions' collection.

    Indexes:
    1. Unique index on 'transaction_id'.
    2. Unique partial index on 'disposal_id' (filtering for non-null strings) to enforce duplicate award prevention for disposal events.
    3. Compound index on ('user_id', ASCENDING) and ('timestamp', DESCENDING) for user credit history pagination.

    Returns:
        List of created index names.
    """
    col = get_collection(CollectionNames.CREDIT_TRANSACTIONS.value)
    created = []

    idx_id = safe_create_index(
        col,
        [("transaction_id", pymongo.ASCENDING)],
        unique=True,
        name="idx_credits_tx_id_unique",
    )
    created.append(idx_id)

    # Partial index ensures string disposal_ids are unique while allowing multiple reward transactions where disposal_id is None
    idx_disp = safe_create_index(
        col,
        [("disposal_id", pymongo.ASCENDING)],
        unique=True,
        partialFilterExpression={"disposal_id": {"$type": "string"}},
        name="idx_credits_disposal_id_unique_partial",
    )
    created.append(idx_disp)

    idx_user_ts = safe_create_index(
        col,
        [("user_id", pymongo.ASCENDING), ("timestamp", pymongo.DESCENDING)],
        name="idx_credits_user_timestamp",
    )
    created.append(idx_user_ts)

    logger.info(f"Created/verified indexes for '{CollectionNames.CREDIT_TRANSACTIONS.value}': {created}")
    return created
