"""
Demo / Test Users Seed Module.
Idempotently seeds a development demonstration user into MongoDB only in non-production environments.
"""

import uuid
from database.collections.users import users_collection
from database.schemas.user_schema import UserDocument
from database.config.database_config import db_settings
from database.utils.logger import logger

DEMO_USER_EMAIL = "citizen.demo@nudgewaste.ai"


def seed_demo_users(force: bool = False) -> list[str]:
    """
    Idempotently seeds a demo user account for testing/development environments.

    Args:
        force: Force seeding even if environment is not development/test.

    Returns:
        List of seeded user IDs.
    """
    seeded = []
    # Safeguard: Do not seed demo users in production unless explicitly forced
    if db_settings.MONGODB_DB_NAME.endswith("_prod") and not force:
        logger.warning("Skipping demo user seeding in production database configuration.")
        return seeded

    existing = users_collection.get_user_by_email(DEMO_USER_EMAIL)
    if existing:
        logger.info(f"Demo user '{DEMO_USER_EMAIL}' already exists (id='{existing.id}'). Skipping insertion.")
        return [existing.id]

    demo_id = str(uuid.uuid4())
    # Note: Dummy hashed password for demo user testing
    demo_user = UserDocument(
        _id=demo_id,
        name="Civic Citizen Demo",
        email=DEMO_USER_EMAIL,
        mobile="+919876543210",
        hashed_password="$2b$12$eImiTXuWVxfM37uY4JANjO5E/T4XhJ9v1S8E1pP1lO3K4M5N6O7P8",
        swachh_credits=50.0,
        status="active",
        is_active=True,
    )

    try:
        users_collection.create_user(demo_user)
        seeded.append(demo_id)
        logger.info(f"Successfully seeded demo user '{DEMO_USER_EMAIL}' (id='{demo_id}')")
    except Exception as exc:
        logger.warning(f"Failed to seed demo user: {exc}")

    return seeded
