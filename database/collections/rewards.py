"""
Rewards Collection Data-Access Module.
Provides catalog lookup and voucher redemption storage for municipal incentives.
"""

from typing import List, Optional
import pymongo
from pymongo.errors import PyMongoError, DuplicateKeyError

from database.connection.mongodb import get_collection
from database.config.collections_config import CollectionNames
from database.schemas.reward_schema import RewardCatalogDocument, RewardRedemptionDocument
from database.utils.logger import logger


class RewardsCollection:
    """Data-access manager for municipal rewards catalog and user redemptions."""

    def __init__(self):
        self.catalog_col_name = CollectionNames.REWARDS.value
        self.redemptions_col_name = CollectionNames.REWARD_REDEMPTIONS.value

    def _get_catalog_col(self):
        return get_collection(self.catalog_col_name)

    def _get_redemptions_col(self):
        return get_collection(self.redemptions_col_name)

    # --- Catalog Operations ---

    def create_reward_catalog_item(self, item: RewardCatalogDocument) -> RewardCatalogDocument:
        """Inserts or upserts a municipal reward catalog item."""
        col = self._get_catalog_col()
        mongo_dict = item.to_mongo_dict()
        try:
            col.replace_one({"_id": item.reward_id}, mongo_dict, upsert=True)
            logger.info(f"Upserted reward catalog item: '{item.reward_id}'")
            return item
        except PyMongoError as exc:
            logger.error(f"MongoDB create_reward_catalog_item error: {exc}")
            raise

    def get_available_rewards(self) -> List[RewardCatalogDocument]:
        """Retrieves all active available municipal incentive rewards."""
        col = self._get_catalog_col()
        try:
            cursor = col.find({"is_available": True})
            results = []
            for doc in cursor:
                doc["_id"] = str(doc.get("_id") or doc.get("reward_id"))
                results.append(RewardCatalogDocument(**doc))
            return results
        except PyMongoError as exc:
            logger.warning(f"MongoDB get_available_rewards error: {exc}")
            return []

    def get_reward_by_id(self, reward_id: str) -> Optional[RewardCatalogDocument]:
        """Retrieves a single reward catalog item by ID."""
        col = self._get_catalog_col()
        try:
            doc = col.find_one({"$or": [{"_id": reward_id}, {"reward_id": reward_id}]})
            if doc:
                doc["_id"] = str(doc.get("_id") or doc.get("reward_id"))
                return RewardCatalogDocument(**doc)
            return None
        except PyMongoError as exc:
            logger.warning(f"MongoDB get_reward_by_id error: {exc}")
            return None

    # --- Redemption Operations ---

    def create_redemption(self, redemption_doc: RewardRedemptionDocument) -> RewardRedemptionDocument:
        """Inserts a new reward redemption voucher record."""
        col = self._get_redemptions_col()
        mongo_dict = redemption_doc.to_mongo_dict()
        try:
            col.insert_one(mongo_dict)
            logger.info(f"Inserted redemption record: id='{redemption_doc.redemption_id}', user_id='{redemption_doc.user_id}'")
            return redemption_doc
        except DuplicateKeyError as exc:
            logger.warning(f"Duplicate redemption insert attempt: {exc}")
            raise ValueError(f"Redemption record '{redemption_doc.redemption_id}' already exists") from exc
        except PyMongoError as exc:
            logger.error(f"MongoDB create_redemption error: {exc}")
            raise

    def get_user_redemptions(self, user_id: str) -> List[RewardRedemptionDocument]:
        """Retrieves all reward redemption records for a user sorted by timestamp DESC."""
        col = self._get_redemptions_col()
        try:
            cursor = col.find({"user_id": user_id}).sort("timestamp", pymongo.DESCENDING)
            results = []
            for doc in cursor:
                doc["_id"] = str(doc.get("_id") or doc.get("redemption_id"))
                results.append(RewardRedemptionDocument(**doc))
            return results
        except PyMongoError as exc:
            logger.warning(f"MongoDB get_user_redemptions error: {exc}")
            return []

    def delete_user_redemptions(
        self, user_id: str, session: Optional[pymongo.client_session.ClientSession] = None
    ) -> int:
        """
        Deletes all reward redemption voucher records for a user.
        Does NOT delete catalog rewards.

        Args:
            user_id: Target user ID.
            session: Optional PyMongo ClientSession.

        Returns:
            int: Number of redemption records deleted.
        """
        col = self._get_redemptions_col()
        try:
            result = col.delete_many({"user_id": user_id}, session=session)
            logger.info(f"Deleted {result.deleted_count} redemption records for user '{user_id}'")
            return result.deleted_count
        except PyMongoError as exc:
            logger.error(f"MongoDB delete_user_redemptions error: {exc}")
            raise


rewards_collection = RewardsCollection()
