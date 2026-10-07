"""
Database Maintenance CLI Script: Reset Database.
Safely resets development/test database environment with explicit confirmation safeguards.
"""

import sys
from database.connection import get_db, init_mongo_connection, close_mongo_connection
from database.config.database_config import db_settings
from database.config.collections_config import COLLECTIONS
from database.indexes import create_all_indexes
from database.seed import run_all_seeds
from database.utils.logger import logger


def reset_database(confirm: bool = False) -> bool:
    """
    Safely resets database collections in development/test environment.

    Args:
        confirm: Explicit boolean flag authorizing reset.

    Returns:
        bool: True if reset succeeded.

    Raises:
        PermissionError: If executed against production or without explicit confirmation.
    """
    # Safeguard 1: Production database name check
    db_name = db_settings.MONGODB_DB_NAME.lower()
    if "prod" in db_name or "production" in db_name:
        logger.error(f"CRITICAL: Reset operation BLOCKED. Cannot reset production database '{db_settings.MONGODB_DB_NAME}'.")
        raise PermissionError("Destructive reset prohibited on production database.")

    # Safeguard 2: Explicit confirmation flag
    if not confirm:
        logger.error("Reset operation BLOCKED. Requires explicit 'confirm=True' or '--confirm-reset' flag.")
        raise PermissionError("Database reset requires explicit confirmation flag.")

    logger.warning(f"Resetting development/test database '{db_settings.MONGODB_DB_NAME}'...")
    init_mongo_connection()

    try:
        db = get_db()
        for entity, col_name in COLLECTIONS.items():
            db.drop_collection(col_name)
            logger.info(f"Dropped collection '{col_name}'")

        # Re-initialize index structures and seed reference data
        create_all_indexes()
        run_all_seeds()
        logger.info(f"Database '{db_settings.MONGODB_DB_NAME}' reset completed successfully.")
        return True
    finally:
        close_mongo_connection()


if __name__ == "__main__":
    if "--confirm-reset" not in sys.argv:
        print("ERROR: Safety protection active. To reset development database, re-run with '--confirm-reset'.")
        sys.exit(1)
    reset_database(confirm=True)
