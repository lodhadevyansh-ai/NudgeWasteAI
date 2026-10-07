"""
Database CLI Script: Setup Database.
Initializes database connection pool, creates collection indexes, and seeds baseline reference data.
"""

from database.connection import init_mongo_connection, close_mongo_connection
from database.indexes import create_all_indexes
from database.seed import run_all_seeds
from database.utils.logger import logger


def setup_database(include_demo_users: bool = True) -> dict:
    """
    Executes complete database initialization, index setup, and reference data seeding.

    Returns:
        Dict of setup results.
    """
    logger.info("Starting NudgeWasteAI Database Setup...")
    init_mongo_connection()
    try:
        indexes = create_all_indexes()
        seed_summary = run_all_seeds(include_demo_users=include_demo_users)
        logger.info("NudgeWasteAI Database Setup completed successfully.")
        return {
            "status": "success",
            "indexes_created": indexes,
            "seed_summary": seed_summary,
        }
    finally:
        close_mongo_connection()


if __name__ == "__main__":
    setup_database()
