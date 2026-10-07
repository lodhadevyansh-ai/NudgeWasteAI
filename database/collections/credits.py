"""
Credits Collection Data-Access Module.
Provides insertion, duplicate prevention, and user transaction history retrieval for Swachh Credits.
"""

from typing import List, Optional
import pymongo
from pymongo.errors import PyMongoError, DuplicateKeyError

from database.connection.mongodb import get_collection
from database.config.collections_config import CollectionNames
from database.schemas.credit_schema import CreditTransactionDocument
from database.utils.logger import logger


class CreditsCollection:
    """Data-access manager for the 'credit_transactions' collection."""

    def __init__(self):
        self.collection_name = CollectionNames.CREDIT_TRANSACTIONS.value

    def _get_col(self):
        return get_collection(self.collection_name)

    def create_transaction(self, tx_doc: CreditTransactionDocument) -> CreditTransactionDocument:
        """
        Inserts an auditable credit transaction document into MongoDB.

        Args:
            tx_doc: Validated CreditTransactionDocument instance.

        Returns:
            CreditTransactionDocument: Created transaction model.
        """
        col = self._get_col()
        mongo_dict = tx_doc.to_mongo_dict()
        try:
            col.insert_one(mongo_dict)
            logger.info(f"Inserted credit transaction: id='{tx_doc.transaction_id}', amount={tx_doc.amount}")
            return tx_doc
        except DuplicateKeyError as exc:
            logger.warning(f"Duplicate transaction insert attempt for id '{tx_doc.transaction_id}': {exc}")
            raise ValueError(f"Credit transaction '{tx_doc.transaction_id}' already exists") from exc
        except PyMongoError as exc:
            logger.error(f"MongoDB credit transaction insert error: {exc}")
            raise

    def get_transaction_by_disposal_id(self, disposal_id: str) -> Optional[CreditTransactionDocument]:
        """
        Retrieves transaction document associated with a specific disposal ID (duplicate prevention check).

        Args:
            disposal_id: Disposal ID string.

        Returns:
            Optional[CreditTransactionDocument]: Transaction model if found, None otherwise.
        """
        col = self._get_col()
        try:
            doc = col.find_one({"disposal_id": disposal_id})
            if doc:
                doc["_id"] = str(doc.get("_id") or doc.get("transaction_id"))
                return CreditTransactionDocument(**doc)
            return None
        except PyMongoError as exc:
            logger.warning(f"MongoDB get_transaction_by_disposal_id error: {exc}")
            return None

    def get_user_credit_history(self, user_id: str, limit: int = 50, skip: int = 0) -> List[CreditTransactionDocument]:
        """
        Retrieves paginated credit transaction logs for a user.

        Args:
            user_id: Target user ID.
            limit: Maximum records to return.
            skip: Number of records to skip.

        Returns:
            List[CreditTransactionDocument]: List of credit transaction documents sorted by timestamp DESC.
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
                doc["_id"] = str(doc.get("_id") or doc.get("transaction_id"))
                results.append(CreditTransactionDocument(**doc))
            return results
        except PyMongoError as exc:
            logger.warning(f"MongoDB get_user_credit_history error: {exc}")
            return []

    def delete_user_credit_transactions(
        self, user_id: str, session: Optional[pymongo.client_session.ClientSession] = None
    ) -> int:
        """
        Deletes all credit transaction logs for a user.

        Args:
            user_id: Target user ID.
            session: Optional PyMongo ClientSession.

        Returns:
            int: Number of credit transaction documents deleted.
        """
        col = self._get_col()
        try:
            result = col.delete_many({"user_id": user_id}, session=session)
            logger.info(f"Deleted {result.deleted_count} credit transactions for user '{user_id}'")
            return result.deleted_count
        except PyMongoError as exc:
            logger.error(f"MongoDB delete_user_credit_transactions error: {exc}")
            raise


credits_collection = CreditsCollection()
