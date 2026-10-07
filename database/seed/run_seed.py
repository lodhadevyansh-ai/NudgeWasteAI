"""
Seed Master Runner.
Executes all database seed functions idempotently.
"""

from database.seed.waste_seed import seed_waste_streams
from database.seed.rewards_seed import seed_rewards_catalog
from database.seed.users_seed import seed_demo_users
from database.utils.logger import logger


def run_all_seeds(include_demo_users: bool = True) -> dict[str, list[str]]:
    """
    Executes all database seeding operations idempotently.

    Args:
        include_demo_users: Flag indicating whether demo users should be seeded.

    Returns:
        Dict mapping entity names to seeded identifier lists.
    """
    logger.info("Starting database seed process...")
    waste_seeded = seed_waste_streams()
    rewards_seeded = seed_rewards_catalog()
    users_seeded = seed_demo_users() if include_demo_users else []

    summary = {
        "waste_streams": waste_seeded,
        "rewards": rewards_seeded,
        "users": users_seeded,
    }
    logger.info(f"Database seed process finished cleanly: {summary}")
    return summary


if __name__ == "__main__":
    run_all_seeds()
