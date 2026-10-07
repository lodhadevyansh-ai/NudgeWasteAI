"""
Disposals Collection Data-Access Module.
Provides CRUD and query operations for verified waste disposal event records.
"""

from typing import List, Optional
import pymongo
from pymongo.errors import PyMongoError, DuplicateKeyError

from database.connection.mongodb import get_collection
from database.config.collections_config import CollectionNames
from database.schemas.disposal_schema import DisposalDocument
from database.utils.logger import logger


class DisposalsCollection:
    """Data-access manager for the 'disposals' collection."""

    def __init__(self):
        self.collection_name = CollectionNames.DISPOSALS.value

    def _get_col(self):
        return get_collection(self.collection_name)

    def create_disposal(self, disposal_doc: DisposalDocument) -> DisposalDocument:
        """
        Inserts a new waste disposal event document into MongoDB.

        Args:
            disposal_doc: Validated DisposalDocument instance.

        Returns:
            DisposalDocument: Created disposal document instance.
        """
        col = self._get_col()
        mongo_dict = disposal_doc.to_mongo_dict()
        try:
            col.insert_one(mongo_dict)
            logger.info(f"Inserted disposal document: id='{disposal_doc.disposal_id}', user_id='{disposal_doc.user_id}'")
            return disposal_doc
        except DuplicateKeyError as exc:
            logger.warning(f"Duplicate disposal insert attempt for id '{disposal_doc.disposal_id}': {exc}")
            raise ValueError(f"Disposal record '{disposal_doc.disposal_id}' already exists") from exc
        except PyMongoError as exc:
            logger.error(f"MongoDB disposal insert error: {exc}")
            raise

    def get_disposal_by_id(self, disposal_id: str, user_id: Optional[str] = None) -> Optional[DisposalDocument]:
        """
        Retrieves a single disposal record by ID. Option to enforce user ownership isolation.

        Args:
            disposal_id: Unique disposal UUID string.
            user_id: Optional authorized user ID filter.

        Returns:
            Optional[DisposalDocument]: Disposal document if found, None otherwise.
        """
        col = self._get_col()
        query = {"$or": [{"_id": disposal_id}, {"disposal_id": disposal_id}]}
        if user_id:
            query["user_id"] = user_id

        try:
            doc = col.find_one(query)
            if doc:
                doc["_id"] = str(doc.get("_id") or doc.get("disposal_id"))
                return DisposalDocument(**doc)
            return None
        except PyMongoError as exc:
            logger.warning(f"MongoDB get_disposal_by_id error: {exc}")
            return None

    def get_disposal_by_prediction_id(self, prediction_id: str, user_id: Optional[str] = None) -> Optional[DisposalDocument]:
        """Retrieves disposal record by prediction_id to prevent duplicate processing."""
        col = self._get_col()
        query = {"prediction_id": prediction_id}
        if user_id:
            query["user_id"] = user_id
        try:
            doc = col.find_one(query)
            if doc:
                doc["_id"] = str(doc.get("_id") or doc.get("disposal_id"))
                return DisposalDocument(**doc)
            return None
        except PyMongoError as exc:
            logger.warning(f"MongoDB get_disposal_by_prediction_id error: {exc}")
            return None

    def get_user_disposal_history(self, user_id: str, limit: int = 50, skip: int = 0) -> List[DisposalDocument]:
        """
        Retrieves paginated disposal history exclusively for a specific user.

        Args:
            user_id: Target user ID.
            limit: Maximum records to return.
            skip: Number of records to skip.

        Returns:
            List[DisposalDocument]: List of disposal documents sorted by timestamp DESC.
        """
        col = self._get_col()
        try:
            cursor = (
                col.find({"user_id": user_id})
                .sort("timestamp", pymongo.DESCENDING)
                .skip(skip)
                .limit(limit)
            )
            results = []
            for doc in cursor:
                doc["_id"] = str(doc.get("_id") or doc.get("disposal_id"))
                results.append(DisposalDocument(**doc))
            return results
        except PyMongoError as exc:
            logger.warning(f"MongoDB get_user_disposal_history error: {exc}")
            return []

    def count_disposals(self, user_id: Optional[str] = None) -> int:
        """Counts total disposal records, optionally filtered by user_id."""
        col = self._get_col()
        query = {"user_id": user_id} if user_id else {}
        try:
            return col.count_documents(query)
        except PyMongoError as exc:
            logger.warning(f"MongoDB count_disposals error: {exc}")
            return 0

    def delete_user_disposals(self, user_id: str, session: Optional[pymongo.client_session.ClientSession] = None) -> int:
        """
        Deletes all disposal documents belonging to a specific user.

        Args:
            user_id: Target user ID.
            session: Optional PyMongo ClientSession.

        Returns:
            int: Number of disposal documents deleted.
        """
        col = self._get_col()
        try:
            result = col.delete_many({"user_id": user_id}, session=session)
            logger.info(f"Deleted {result.deleted_count} disposal documents for user '{user_id}'")
            return result.deleted_count
        except PyMongoError as exc:
            logger.error(f"MongoDB delete_user_disposals error: {exc}")
            raise


disposals_collection = DisposalsCollection()
