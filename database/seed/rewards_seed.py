"""
Municipal Rewards Catalog Seed Module.
Idempotently seeds municipal incentive rewards catalog items into MongoDB.
"""

from database.collections.rewards import rewards_collection
from database.schemas.reward_schema import RewardCatalogDocument
from database.utils.logger import logger

DEFAULT_REWARDS = [
    {
        "reward_id": "reward_tax_5pct",
        "title": "Property Tax Rebate Voucher (5%)",
        "description": "Redeemable for a 5% discount on municipal property tax assessment.",
        "credit_cost": 100.0,
        "reward_type": "tax_discount",
        "is_available": True,
    },
    {
        "reward_id": "reward_transit_pass",
        "title": "Public Transit Metro Pass (1 Week)",
        "description": "Unlimited 7-day municipal metro & bus transit pass voucher.",
        "credit_cost": 50.0,
        "reward_type": "transit_pass",
        "is_available": True,
    },
    {
        "reward_id": "reward_utility_rebate",
        "title": "Municipal Water & Electricity Bill Rebate",
        "description": "Direct credit rebate on municipal water supply or electricity utility bill.",
        "credit_cost": 75.0,
        "reward_type": "utility_rebate",
        "is_available": True,
    },
    {
        "reward_id": "reward_compost_kit",
        "title": "Home Segregation & Compost Kit",
        "description": "Voucher for a free municipal home composting bin and bio-enzyme kit.",
        "credit_cost": 30.0,
        "reward_type": "eco_voucher",
        "is_available": True,
    },
]


def seed_rewards_catalog() -> list[str]:
    """
    Idempotently seeds municipal incentive rewards catalog.

    Returns:
        List of seeded reward IDs.
    """
    seeded = []
    for item in DEFAULT_REWARDS:
        doc = RewardCatalogDocument(**item)
        rewards_collection.create_reward_catalog_item(doc)
        seeded.append(doc.reward_id)
    logger.info(f"Successfully seeded municipal rewards catalog: {seeded}")
    return seeded
