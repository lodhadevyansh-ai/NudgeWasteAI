"""
Database CLI Script: Create Indexes.
Idempotent script to create all MongoDB indexes required by NudgeWasteAI.
"""

from database.connection import init_mongo_connection, close_mongo_connection
from database.indexes import create_all_indexes
from database.utils.logger import logger


def main():
    """CLI entrypoint for creating database indexes."""
    logger.info("Initializing database connection for index creation...")
    init_mongo_connection()
    try:
        results = create_all_indexes()
        logger.info(f"Successfully created database indexes across {len(results)} collections.")
        for col_name, idx_list in results.items():
            print(f"  - Collection '{col_name}': {len(idx_list)} indexes verified/created.")
    finally:
        close_mongo_connection()


if __name__ == "__main__":
    main()
