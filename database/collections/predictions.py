"""
Predictions Collection Data-Access Module.
Provides insertion and query operations for waste classification predictions.
"""

from typing import Optional
import pymongo
from pymongo.errors import PyMongoError, DuplicateKeyError

from database.connection.mongodb import get_collection
from database.config.collections_config import CollectionNames
from database.schemas.prediction_schema import PredictionDocument
from database.utils.logger import logger


class PredictionsCollection:
    """Data-access manager for the 'predictions' collection."""

    def __init__(self):
        self.collection_name = CollectionNames.PREDICTIONS.value

    def _get_col(self):
        return get_collection(self.collection_name)

    def create_prediction(self, pred_doc: PredictionDocument) -> PredictionDocument:
        """
        Inserts a new waste classification prediction document into MongoDB.

        Args:
            pred_doc: Validated PredictionDocument instance.

        Returns:
            PredictionDocument: Created prediction document model.
        """
        col = self._get_col()
        mongo_dict = pred_doc.to_mongo_dict()
        try:
            col.insert_one(mongo_dict)
            logger.info(f"Inserted prediction document: id='{pred_doc.prediction_id}'")
            return pred_doc
        except DuplicateKeyError as exc:
            logger.warning(f"Duplicate prediction insert attempt for id '{pred_doc.prediction_id}': {exc}")
            raise ValueError(f"Prediction record '{pred_doc.prediction_id}' already exists") from exc
        except PyMongoError as exc:
            logger.error(f"MongoDB prediction insert error: {exc}")
            raise

    def get_prediction_by_id(self, prediction_id: str) -> Optional[PredictionDocument]:
        """
        Retrieves a single prediction record by ID.

        Args:
            prediction_id: Unique prediction UUID string.

        Returns:
            Optional[PredictionDocument]: Prediction document if found, None otherwise.
        """
        col = self._get_col()
        try:
            doc = col.find_one({"$or": [{"_id": prediction_id}, {"prediction_id": prediction_id}]})
            if doc:
                doc["_id"] = str(doc.get("_id") or doc.get("prediction_id"))
                return PredictionDocument(**doc)
            return None
        except PyMongoError as exc:
            logger.warning(f"MongoDB get_prediction_by_id error: {exc}")
            return None

    def delete_user_predictions(self, user_id: str, session: Optional[pymongo.client_session.ClientSession] = None) -> int:
        """
        Deletes all waste classification prediction documents for a specific user.

        Args:
            user_id: Target user ID.
            session: Optional PyMongo ClientSession.

        Returns:
            int: Number of prediction documents deleted.
        """
        col = self._get_col()
        try:
            result = col.delete_many({"user_id": user_id}, session=session)
            logger.info(f"Deleted {result.deleted_count} prediction documents for user '{user_id}'")
            return result.deleted_count
        except PyMongoError as exc:
            logger.error(f"MongoDB delete_user_predictions error: {exc}")
            raise


predictions_collection = PredictionsCollection()
