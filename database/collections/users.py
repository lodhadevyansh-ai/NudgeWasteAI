"""
Users Collection Data-Access Module.
Provides CRUD and atomic update operations for the MongoDB users collection.
"""

from typing import Dict, Any, Optional
import pymongo
from pymongo.errors import PyMongoError, DuplicateKeyError

from database.connection.mongodb import get_collection
from database.config.collections_config import CollectionNames
from database.schemas.user_schema import UserDocument
from database.utils.logger import logger


class UsersCollection:
    """Data-access manager for the 'users' collection."""

    def __init__(self):
        self.collection_name = CollectionNames.USERS.value

    def _get_col(self):
        return get_collection(self.collection_name)

    def create_user(self, user_doc: UserDocument) -> UserDocument:
        """
        Inserts a new user document into MongoDB.

        Args:
            user_doc: Validated UserDocument schema instance.

        Returns:
            UserDocument: Created user document instance.

        Raises:
            ValueError: If email or user ID already exists.
            PyMongoError: If database operation fails.
        """
        col = self._get_col()
        mongo_dict = user_doc.to_mongo_dict()
        try:
            col.insert_one(mongo_dict)
            logger.info(f"Inserted user document: id='{user_doc.id}', email='{user_doc.email}'")
            return user_doc
        except DuplicateKeyError as exc:
            logger.warning(f"Duplicate user insert attempt for email '{user_doc.email}': {exc}")
            raise ValueError(f"User with email '{user_doc.email}' already exists") from exc
        except PyMongoError as exc:
            logger.error(f"MongoDB user insert error: {exc}")
            raise

    def get_user_by_email(self, email: str) -> Optional[UserDocument]:
        """
        Retrieves user document by email.

        Args:
            email: User email address string.

        Returns:
            Optional[UserDocument]: UserDocument model if found, None otherwise.
        """
        email_clean = email.strip().lower()
        col = self._get_col()
        try:
            doc = col.find_one({"email": email_clean})
            if doc:
                doc["_id"] = str(doc.get("_id") or doc.get("id"))
                return UserDocument(**doc)
            return None
        except PyMongoError as exc:
            logger.warning(f"MongoDB get_user_by_email error: {exc}")
            return None

    def get_user_by_id(self, user_id: str) -> Optional[UserDocument]:
        """
        Retrieves user document by unique user ID string or _id.

        Args:
            user_id: Unique user ID string.

        Returns:
            Optional[UserDocument]: UserDocument model if found, None otherwise.
        """
        col = self._get_col()
        try:
            doc = col.find_one({"$or": [{"_id": user_id}, {"id": user_id}]})
            if doc:
                doc["_id"] = str(doc.get("_id") or doc.get("id"))
                return UserDocument(**doc)
            return None
        except PyMongoError as exc:
            logger.warning(f"MongoDB get_user_by_id error: {exc}")
            return None

    def update_user_credits(self, user_id: str, credit_change: float) -> bool:
        """
        Atomically increments/decrements user's Swachh Credits balance.

        Args:
            user_id: Target user ID.
            credit_change: Delta amount to add or subtract.

        Returns:
            bool: True if document was matched and updated, False otherwise.
        """
        col = self._get_col()
        try:
            result = col.update_one(
                {"$or": [{"_id": user_id}, {"id": user_id}]},
                {"$inc": {"swachh_credits": credit_change}},
            )
            return result.matched_count > 0
        except PyMongoError as exc:
            logger.error(f"MongoDB update_user_credits error: {exc}")
            return False

    def delete_user(
        self,
        user_id: str,
        email: Optional[str] = None,
        session: Optional[pymongo.client_session.ClientSession] = None,
    ) -> bool:
        """
        Deletes user document(s) from MongoDB by unique user ID, _id, or email.

        Args:
            user_id: Target user ID string.
            email: Optional email address string.
            session: Optional PyMongo ClientSession for transaction support.

        Returns:
            bool: True if user document was matched and deleted, False otherwise.
        """
        col = self._get_col()
        or_clauses = [{"_id": user_id}, {"id": user_id}]
        if email:
            or_clauses.append({"email": email.strip().lower()})

        try:
            result = col.delete_many(
                {"$or": or_clauses},
                session=session,
            )
            if result.deleted_count > 0:
                logger.info(f"Deleted {result.deleted_count} user document(s) for user_id='{user_id}', email='{email}'")
                return True
            logger.warning(f"No user document found to delete for user_id='{user_id}'")
            return False
        except PyMongoError as exc:
            logger.error(f"MongoDB delete_user error: {exc}")
            raise


users_collection = UsersCollection()
