"""
Nudges Collection Data-Access Module.
Provides CRUD and retrieval operations for behavioural micro-nudge guidance records.
"""

from typing import Optional
import pymongo
from pymongo.errors import PyMongoError, DuplicateKeyError

from database.connection.mongodb import get_collection
from database.config.collections_config import CollectionNames
from database.schemas.nudge_schema import NudgeDocument
from database.utils.logger import logger


class NudgesCollection:
    """Data-access manager for the 'nudges' collection."""

    def __init__(self):
        self.collection_name = CollectionNames.NUDGES.value

    def _get_col(self):
        return get_collection(self.collection_name)

    def create_nudge(self, nudge_doc: NudgeDocument) -> NudgeDocument:
        """
        Inserts a new micro-nudge document into MongoDB.

        Args:
            nudge_doc: Validated NudgeDocument instance.

        Returns:
            NudgeDocument: Created nudge document instance.
        """
        col = self._get_col()
        mongo_dict = nudge_doc.to_mongo_dict()
        try:
            col.insert_one(mongo_dict)
            logger.info(f"Inserted nudge document: id='{nudge_doc.nudge_id}', category='{nudge_doc.waste_category}'")
            return nudge_doc
        except DuplicateKeyError as exc:
            logger.warning(f"Duplicate nudge insert attempt for id '{nudge_doc.nudge_id}': {exc}")
            raise ValueError(f"Nudge record '{nudge_doc.nudge_id}' already exists") from exc
        except PyMongoError as exc:
            logger.error(f"MongoDB nudge insert error: {exc}")
            raise

    def get_nudge_by_id(self, nudge_id: str) -> Optional[NudgeDocument]:
        """
        Retrieves a single nudge record by ID.

        Args:
            nudge_id: Unique nudge UUID string.

        Returns:
            Optional[NudgeDocument]: Nudge document if found, None otherwise.
        """
        col = self._get_col()
        try:
            doc = col.find_one({"$or": [{"_id": nudge_id}, {"nudge_id": nudge_id}]})
            if doc:
                doc["_id"] = str(doc.get("_id") or doc.get("nudge_id"))
                return NudgeDocument(**doc)
            return None
        except PyMongoError as exc:
            logger.warning(f"MongoDB get_nudge_by_id error: {exc}")
            return None

    def delete_user_nudges(
        self,
        user_id: str,
        disposal_ids: Optional[list] = None,
        prediction_ids: Optional[list] = None,
        session: Optional[pymongo.client_session.ClientSession] = None,
    ) -> int:
        """
        Deletes micro-nudge guidance documents associated with a user or user's disposals/predictions.

        Args:
            user_id: Target user ID.
            disposal_ids: Optional list of disposal IDs owned by the user.
            prediction_ids: Optional list of prediction IDs owned by the user.
            session: Optional PyMongo ClientSession.

        Returns:
            int: Number of nudge documents deleted.
        """
        col = self._get_col()
        or_clauses = [{"user_id": user_id}]
        if disposal_ids:
            or_clauses.append({"disposal_id": {"$in": disposal_ids}})
        if prediction_ids:
            or_clauses.append({"prediction_id": {"$in": prediction_ids}})

        try:
            result = col.delete_many({"$or": or_clauses}, session=session)
            logger.info(f"Deleted {result.deleted_count} nudge documents for user '{user_id}'")
            return result.deleted_count
        except PyMongoError as exc:
            logger.error(f"MongoDB delete_user_nudges error: {exc}")
            raise


nudges_collection = NudgesCollection()
