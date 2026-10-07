"""
User Service and Database Access Layer.
Implements user registration, authentication, and lookup delegating persistence to database.collections.users.
"""

from datetime import datetime, timezone
import uuid
from typing import Dict, Any, Optional

from app.core.security import hash_password, verify_password  # pyrefly: ignore [missing-import]
from app.schemas.user import UserRegister, UserInDB, UserResponse  # pyrefly: ignore [missing-import]
from app.utils.logger import logger  # pyrefly: ignore [missing-import]

from database.collections.users import users_collection  # pyrefly: ignore [missing-import]
from database.schemas.user_schema import UserDocument  # pyrefly: ignore [missing-import]


class UserService:
    """Isolated User Repository & Service manager backed by database.collections.users with memory fallback."""

    def __init__(self):
        self._in_memory_store: Dict[str, Dict[str, Any]] = {}

    def get_user_by_email(self, email: str) -> Optional[UserInDB]:
        """Fetches user model by email."""
        email_clean = email.strip().lower()
        try:
            db_user = users_collection.get_user_by_email(email_clean)
            if db_user:
                return UserInDB(**db_user.to_mongo_dict())
        except Exception as exc:
            logger.warning(f"MongoDB search error in get_user_by_email: {exc}")

        # In-memory store fallback
        for user_dict in self._in_memory_store.values():
            if user_dict["email"] == email_clean:
                return UserInDB(**user_dict)
        return None

    def get_user_by_id(self, user_id: str) -> Optional[UserInDB]:
        """Fetches user model by unique user ID."""
        try:
            db_user = users_collection.get_user_by_id(user_id)
            if db_user:
                return UserInDB(**db_user.to_mongo_dict())
        except Exception as exc:
            logger.warning(f"MongoDB lookup error in get_user_by_id: {exc}")

        # In-memory store fallback
        user_dict = self._in_memory_store.get(user_id)
        if user_dict:
            return UserInDB(**user_dict)
        return None

    def create_user(self, user_data: UserRegister) -> UserResponse:
        """
        Creates and stores a new user.

        Raises:
            ValueError: If user with email already exists.
        """
        email_clean = user_data.email.strip().lower()
        if self.get_user_by_email(email_clean):
            raise ValueError(f"User with email '{email_clean}' already exists")

        user_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc)
        hashed_pwd = hash_password(user_data.password)

        user_doc_dict = {
            "_id": user_id,
            "id": user_id,
            "name": user_data.name.strip(),
            "email": email_clean,
            "mobile": user_data.mobile,
            "city": getattr(user_data, "city", None) or "Indore Municipal Corporation",
            "hashed_password": hashed_pwd,
            "swachh_credits": 500.0,
            "status": "active",
            "is_active": True,
            "created_at": now,
            "updated_at": now,
        }

        # Store via database collection wrapper
        try:
            user_doc = UserDocument(**user_doc_dict)
            users_collection.create_user(user_doc)
        except Exception as exc:
            logger.warning(f"MongoDB user insert fallback warning: {exc}")

        # Record registration bonus credit transaction (+500)
        from app.services.credits_service import credits_service  # pyrefly: ignore [missing-import]
        credits_service.record_registration_bonus(user_id=user_id, amount=500.0)

        # Always update in-memory store for fast fallback lookup
        self._in_memory_store[user_id] = user_doc_dict

        return UserResponse(
            id=user_id,
            name=user_doc_dict["name"],
            email=user_doc_dict["email"],
            mobile=user_doc_dict["mobile"],
            city=user_doc_dict["city"],
            swachh_credits=user_doc_dict["swachh_credits"],
            status=user_doc_dict["status"],
            is_active=user_doc_dict["is_active"],
            created_at=user_doc_dict["created_at"],
            updated_at=user_doc_dict["updated_at"],
        )

    def authenticate_user(self, email: str, password: str) -> Optional[UserInDB]:
        """
        Authenticates user with email and raw password.

        Returns:
            Optional[UserInDB]: User model if authenticated, None otherwise.
        """
        user = self.get_user_by_email(email)
        if not user:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        return user

    def delete_user_account(self, user_id: str) -> bool:
        """
        Permanently deletes authenticated user account and all associated personal data from MongoDB.

        Collections purged for user_id:
        - users
        - predictions
        - disposals
        - nudges
        - credit_transactions
        - reward_redemptions

        Args:
            user_id: Authenticated user ID string.

        Returns:
            bool: True if account was successfully deleted.

        Raises:
            ValueError: If user account is not found.
            RuntimeError: If deletion fails at database layer.
        """
        user = self.get_user_by_id(user_id)
        if not user:
            raise ValueError(f"User account '{user_id}' not found")

        user_email = user.email.strip().lower() if user.email else ""
        disposal_ids = []
        prediction_ids = []

        try:
            from database.collections.users import users_collection
            from database.collections.disposals import disposals_collection
            from database.collections.predictions import predictions_collection
            from database.collections.nudges import nudges_collection
            from database.collections.credits import credits_collection
            from database.collections.rewards import rewards_collection
            from database.connection.mongodb import get_mongo_client

            # Collect disposal IDs
            user_disposals = disposals_collection.get_user_disposal_history(user_id, limit=1000, skip=0)
            disposal_ids = [d.disposal_id for d in user_disposals if d.disposal_id]

            # Attempt MongoDB session transaction for atomicity
            client = get_mongo_client()
            session_success = False

            try:
                with client.start_session() as session:
                    with session.start_transaction():
                        disposals_collection.delete_user_disposals(user_id, session=session)
                        predictions_collection.delete_user_predictions(user_id, session=session)
                        nudges_collection.delete_user_nudges(
                            user_id, disposal_ids=disposal_ids, prediction_ids=prediction_ids, session=session
                        )
                        credits_collection.delete_user_credit_transactions(user_id, session=session)
                        rewards_collection.delete_user_redemptions(user_id, session=session)
                        users_collection.delete_user(user_id, email=user_email, session=session)
                        session_success = True
            except Exception as txn_exc:
                logger.warning(f"MongoDB transaction execution notice (falling back to sequential delete): {txn_exc}")

            if not session_success:
                # Safe sequential execution fallback for standalone MongoDB deployments
                disposals_collection.delete_user_disposals(user_id)
                predictions_collection.delete_user_predictions(user_id)
                nudges_collection.delete_user_nudges(user_id, disposal_ids=disposal_ids, prediction_ids=prediction_ids)
                credits_collection.delete_user_credit_transactions(user_id)
                rewards_collection.delete_user_redemptions(user_id)
                users_collection.delete_user(user_id, email=user_email)

        except Exception as exc:
            logger.error(f"Failed to delete user account '{user_id}' from database: {exc}", exc_info=True)
            raise RuntimeError("Database error occurred while deleting account") from exc

        # Clear in-memory store by user_id and email
        keys_to_remove = [
            k for k, v in self._in_memory_store.items()
            if k == user_id or v.get("id") == user_id or (user_email and v.get("email") == user_email)
        ]
        for k in keys_to_remove:
            self._in_memory_store.pop(k, None)

        try:
            from app.services.disposal_service import disposal_service
            disposal_service._in_memory_store = {
                k: v for k, v in disposal_service._in_memory_store.items() if v.get("user_id") != user_id
            }
        except Exception:
            pass

        try:
            from app.services.credits_service import credits_service
            credits_service._in_memory_tx = {
                k: v for k, v in credits_service._in_memory_tx.items() if v.get("user_id") != user_id
            }
            credits_service._user_balances.pop(user_id, None)
            if disposal_ids:
                credits_service._processed_disposals.difference_update(disposal_ids)
        except Exception:
            pass

        try:
            from app.services.reward_service import reward_service
            reward_service._in_memory_redemptions = {
                k: v for k, v in reward_service._in_memory_redemptions.items() if v.get("user_id") != user_id
            }
        except Exception:
            pass

        try:
            from app.services.nudge_service import nudge_service
            nudge_service._in_memory_store = {
                k: v for k, v in nudge_service._in_memory_store.items()
                if v.get("user_id") != user_id and v.get("disposal_id") not in disposal_ids
            }
        except Exception:
            pass

        logger.info(f"User account '{user_id}' and all associated data permanently deleted.")
        return True


# Singleton instance
user_service = UserService()
