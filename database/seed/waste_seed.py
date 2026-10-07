"""
Statutory Waste Streams Seed Module.
Idempotently seeds the 4 statutory waste stream category definitions into MongoDB.
"""

from database.collections.waste import waste_collection, DEFAULT_STATUTORY_WASTE_STREAMS
from database.schemas.waste_schema import WasteStreamDocument
from database.utils.logger import logger


def seed_waste_streams() -> list[str]:
    """
    Idempotently seeds statutory waste stream definitions ('Wet', 'Dry', 'Sanitary', 'Special Care').

    Returns:
        List of seeded statutory category names.
    """
    seeded = []
    for item in DEFAULT_STATUTORY_WASTE_STREAMS:
        doc = WasteStreamDocument(**item)
        waste_collection.upsert_waste_stream(doc)
        seeded.append(doc.category)
    logger.info(f"Successfully seeded statutory waste streams: {seeded}")
    return seeded
