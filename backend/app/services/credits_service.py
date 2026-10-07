"""
Swachh Credits Service.
Manages user credit balances, auditable transaction logs, and disposal reward calculations using database collections.
"""

from datetime import datetime, timezone
import uuid
from typing import Dict, Any, List, Optional

from app.core.constants import (  # pyrefly: ignore [missing-import]
    CREDIT_TRANSACTION_TYPE_EARN,
    CREDIT_TRANSACTION_TYPE_REDEEM,
    CREDIT_RULES_BY_CATEGORY,
    DEFAULT_CREDIT_AWARD,
    DISPOSAL_STATUS_VERIFIED,
)
from app.schemas.credits import CreditBalanceResponse, CreditTransactionResponse  # pyrefly: ignore [missing-import]
from app.services.user_service import user_service  # pyrefly: ignore [missing-import]
from app.utils.logger import logger  # pyrefly: ignore [missing-import]

from database.collections.credits import credits_collection  # pyrefly: ignore [missing-import]
from database.collections.users import users_collection  # pyrefly: ignore [missing-import]
from database.schemas.credit_schema import CreditTransactionDocument  # pyrefly: ignore [missing-import]


class CreditsService:
    """Service layer managing Swachh Credits balances and transaction logs."""

    def __init__(self):
        self._in_memory_tx: Dict[str, Dict[str, Any]] = {}
        self._processed_disposals: set = set()
        self._user_balances: Dict[str, Dict[str, Any]] = {}

    def calculate_disposal_credits(self, confirmed_category: str) -> float:
        """Calculates earned credits based on statutory category rules."""
        return CREDIT_RULES_BY_CATEGORY.get(confirmed_category, DEFAULT_CREDIT_AWARD)

    def record_registration_bonus(self, user_id: str, amount: float = 500.0) -> CreditTransactionResponse:
        """
        Records the initial registration welcome bonus transaction (+500 Swachh Credits).
        """
        now = datetime.now(timezone.utc)
        tx_id = str(uuid.uuid4())
        reason = "Welcome bonus"

        tx_doc_dict = {
            "_id": tx_id,
            "transaction_id": tx_id,
            "user_id": user_id,
            "amount": amount,
            "transaction_type": CREDIT_TRANSACTION_TYPE_EARN,
            "reason": reason,
            "disposal_id": None,
            "reward_id": None,
            "balance_before": 0.0,
            "balance_after": amount,
            "timestamp": now,
        }

        self._user_balances[user_id] = {
            "user_id": user_id,
            "swachh_credits": amount,
            "total_earned": amount,
            "total_redeemed": 0.0,
            "updated_at": now,
        }

        try:
            tx_doc = CreditTransactionDocument(**tx_doc_dict)
            credits_collection.create_transaction(tx_doc)
        except Exception as exc:
            logger.warning(f"MongoDB registration credit transaction insert error: {exc}")

        self._in_memory_tx[tx_id] = tx_doc_dict
        logger.info(f"Recorded initial registration bonus (+{amount}) for user {user_id}")
        return CreditTransactionResponse(**tx_doc_dict)

    def award_disposal_credits(
        self,
        user_id: str,
        disposal_id: str,
        confirmed_category: str,
        verification_status: str,
        is_correctly_segregated: bool,
    ) -> Optional[CreditTransactionResponse]:
        """
        Awards Swachh Credits for a verified disposal event.
        Prevents duplicate credit awards for the same disposal_id.
        """
        if not is_correctly_segregated or verification_status != DISPOSAL_STATUS_VERIFIED:
            logger.info(f"No credits awarded for disposal {disposal_id}: status='{verification_status}'")
            return None

        # Duplicate Prevention Check
        if disposal_id in self._processed_disposals:
            logger.warning(f"Duplicate credit award attempt blocked in memory for disposal '{disposal_id}'")
            return None

        try:
            existing = credits_collection.get_transaction_by_disposal_id(disposal_id)
            if existing:
                self._processed_disposals.add(disposal_id)
                logger.warning(f"Duplicate credit award attempt blocked in DB for disposal '{disposal_id}'")
                return None
        except Exception as exc:
            logger.warning(f"MongoDB duplicate credit check warning: {exc}")

        current_bal = self.get_user_balance(user_id)
        bal_before = current_bal.swachh_credits
        amount = self.calculate_disposal_credits(confirmed_category)
        bal_after = bal_before + amount

        now = datetime.now(timezone.utc)
        tx_id = str(uuid.uuid4())
        reason = f"Verified {confirmed_category} Waste Segregation Disposal"

        tx_doc_dict = {
            "_id": tx_id,
            "transaction_id": tx_id,
            "user_id": user_id,
            "amount": amount,
            "transaction_type": CREDIT_TRANSACTION_TYPE_EARN,
            "reason": reason,
            "disposal_id": disposal_id,
            "reward_id": None,
            "balance_before": bal_before,
            "balance_after": bal_after,
            "timestamp": now,
        }

        # Update balance locally and in database
        self._update_user_balance(user_id, credit_change=amount, earned_change=amount, redeemed_change=0.0)
        self._processed_disposals.add(disposal_id)

        # Persistence via database collection
        try:
            tx_doc = CreditTransactionDocument(**tx_doc_dict)
            credits_collection.create_transaction(tx_doc)
        except Exception as exc:
            logger.warning(f"MongoDB credit transaction insert error: {exc}")

        self._in_memory_tx[tx_id] = tx_doc_dict
        logger.info(f"Awarded {amount} Swachh Credits to user {user_id} for disposal {disposal_id}")

        return CreditTransactionResponse(**tx_doc_dict)

    def deduct_credits(
        self,
        user_id: str,
        amount: float,
        reason: str,
        reward_id: str,
    ) -> CreditTransactionResponse:
        """
        Deducts credits from user balance for reward redemption.

        Raises:
            ValueError: If user has insufficient credits.
        """
        balance = self.get_user_balance(user_id)
        if balance.swachh_credits < amount:
            raise ValueError(f"Insufficient Swachh Credits balance ({balance.swachh_credits:.1f} < required {amount:.1f})")

        bal_before = balance.swachh_credits
        bal_after = bal_before - amount
        now = datetime.now(timezone.utc)
        tx_id = str(uuid.uuid4())

        tx_doc_dict = {
            "_id": tx_id,
            "transaction_id": tx_id,
            "user_id": user_id,
            "amount": -amount,
            "transaction_type": CREDIT_TRANSACTION_TYPE_REDEEM,
            "reason": reason,
            "disposal_id": None,
            "reward_id": reward_id,
            "balance_before": bal_before,
            "balance_after": bal_after,
            "timestamp": now,
        }

        self._update_user_balance(user_id, credit_change=-amount, earned_change=0.0, redeemed_change=amount)

        try:
            tx_doc = CreditTransactionDocument(**tx_doc_dict)
            credits_collection.create_transaction(tx_doc)
        except Exception as exc:
            logger.warning(f"MongoDB deduction insert error: {exc}")

        self._in_memory_tx[tx_id] = tx_doc_dict
        logger.info(f"Deducted {amount} credits from user {user_id} for reward {reward_id}")

        return CreditTransactionResponse(**tx_doc_dict)

    def _update_user_balance(
        self, user_id: str, credit_change: float, earned_change: float, redeemed_change: float
    ) -> None:
        """Helper to update balance in memory and database."""
        if user_id not in self._user_balances:
            user = user_service.get_user_by_id(user_id)
            current_credits = user.swachh_credits if user else 0.0
            self._user_balances[user_id] = {
                "user_id": user_id,
                "swachh_credits": current_credits,
                "total_earned": current_credits,
                "total_redeemed": 0.0,
                "updated_at": datetime.now(timezone.utc),
            }

        bal = self._user_balances[user_id]
        bal["swachh_credits"] = max(0.0, bal["swachh_credits"] + credit_change)
        bal["total_earned"] += max(0.0, earned_change)
        bal["total_redeemed"] += max(0.0, redeemed_change)
        bal["updated_at"] = datetime.now(timezone.utc)

        # Update in-memory user_service dict if present
        if user_id in user_service._in_memory_store:
            user_service._in_memory_store[user_id]["swachh_credits"] = bal["swachh_credits"]

        # Atomic update in database users collection
        try:
            users_collection.update_user_credits(user_id, credit_change)
        except Exception as exc:
            logger.warning(f"Failed to update user credits in MongoDB: {exc}")

    def get_user_balance(self, user_id: str) -> CreditBalanceResponse:
        """Retrieves credit balance for authenticated user."""
        if user_id not in self._user_balances:
            user = user_service.get_user_by_id(user_id)
            current_credits = user.swachh_credits if user else 0.0
            self._user_balances[user_id] = {
                "user_id": user_id,
                "swachh_credits": current_credits,
                "total_earned": current_credits,
                "total_redeemed": 0.0,
                "updated_at": datetime.now(timezone.utc),
            }

        return CreditBalanceResponse(**self._user_balances[user_id])

    def get_user_credit_history(self, user_id: str, limit: int = 50, skip: int = 0) -> List[CreditTransactionResponse]:
        """Retrieves credit transaction history exclusively for the authorized user."""
        try:
            db_txs = credits_collection.get_user_credit_history(user_id, limit=limit, skip=skip)
            if db_txs:
                return [CreditTransactionResponse(**t.to_mongo_dict()) for t in db_txs]
        except Exception as exc:
            logger.warning(f"MongoDB credit history search error: {exc}")

        # In-memory fallback
        user_txs = [tx for tx in self._in_memory_tx.values() if tx["user_id"] == user_id]
        user_txs.sort(key=lambda x: x["timestamp"], reverse=True)
        paginated = user_txs[skip : skip + limit]
        return [CreditTransactionResponse(**t) for t in paginated]


# Singleton instance
credits_service = CreditsService()
