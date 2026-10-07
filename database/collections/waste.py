"""
Waste Collection Data-Access Module.
Provides query and management operations for the 4 statutory waste stream categories.
"""

from typing import List, Optional
from pymongo.errors import PyMongoError

from database.connection.mongodb import get_collection
from database.config.collections_config import CollectionNames
from database.schemas.waste_schema import WasteStreamDocument
from database.utils.logger import logger


DEFAULT_STATUTORY_WASTE_STREAMS = [
    {
        "category": "Wet",
        "description": "Biodegradable organic kitchen scrap food waste, garden leaves, and compostables.",
        "bin_color": "Green",
        "credit_award": 10.0,
        "guidance_nudge": "Place in Green Bin for municipal composting and organic recycling.",
    },
    {
        "category": "Dry",
        "description": "Non-biodegradable recyclable paper, plastic packaging, cardboard, glass, and metal cans.",
        "bin_color": "Blue",
        "credit_award": 10.0,
        "guidance_nudge": "Place in Blue Bin for material recycling (ensure items are clean and dry).",
    },
    {
        "category": "Sanitary",
        "description": "Biohazard personal hygiene waste, used diapers, bandages, medical swabs, and masks.",
        "bin_color": "Red",
        "credit_award": 15.0,
        "guidance_nudge": "Wrap securely in newspaper/marked pouch and place in Red Sanitary Bin.",
    },
    {
        "category": "Special Care",
        "description": "Domestic hazardous waste, e-waste, dead batteries, chemical containers, and fluorescent bulbs.",
        "bin_color": "Black",
        "credit_award": 20.0,
        "guidance_nudge": "Hand over to E-Waste / Hazardous Waste collector or place in Black Bin.",
    },
]


class WasteCollection:
    """Data-access manager for statutory waste stream definitions."""

    def __init__(self):
        self.collection_name = CollectionNames.WASTE.value

    def _get_col(self):
        return get_collection(self.collection_name)

    def upsert_waste_stream(self, stream: WasteStreamDocument) -> WasteStreamDocument:
        """Upserts a statutory waste stream document."""
        col = self._get_col()
        mongo_dict = stream.to_mongo_dict()
        try:
            col.replace_one({"_id": stream.category}, mongo_dict, upsert=True)
            logger.info(f"Upserted statutory waste stream: '{stream.category}'")
            return stream
        except PyMongoError as exc:
            logger.error(f"MongoDB upsert_waste_stream error: {exc}")
            raise

    def get_waste_stream_by_category(self, category: str) -> Optional[WasteStreamDocument]:
        """Retrieves a statutory waste stream by category name."""
        col = self._get_col()
        try:
            doc = col.find_one({"$or": [{"_id": category}, {"category": category}]})
            if doc:
                return WasteStreamDocument(**doc)
            return None
        except PyMongoError as exc:
            logger.warning(f"MongoDB get_waste_stream_by_category error: {exc}")
            return None

    def get_all_waste_streams(self) -> List[WasteStreamDocument]:
        """Retrieves all statutory waste stream definitions."""
        col = self._get_col()
        try:
            cursor = col.find({})
            results = [WasteStreamDocument(**doc) for doc in cursor]
            if not results:
                # Seed defaults if database collection is empty
                for item in DEFAULT_STATUTORY_WASTE_STREAMS:
                    stream = WasteStreamDocument(**item)
                    self.upsert_waste_stream(stream)
                    results.append(stream)
            return results
        except PyMongoError as exc:
            logger.warning(f"MongoDB get_all_waste_streams error: {exc}")
            return [WasteStreamDocument(**item) for item in DEFAULT_STATUTORY_WASTE_STREAMS]


waste_collection = WasteCollection()
