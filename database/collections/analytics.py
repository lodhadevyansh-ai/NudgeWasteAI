"""
Analytics Collection Data-Access & Aggregation Module.
Executes efficient MongoDB aggregation pipelines for platform municipal dashboards and citizen reports.
"""

from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional
from pymongo.errors import PyMongoError

from database.connection.mongodb import get_collection
from database.config.collections_config import CollectionNames
from database.schemas.analytics_schema import AnalyticsSummaryDocument
from database.utils.logger import logger

DISPOSAL_STATUS_VERIFIED = "verified"
DISPOSAL_STATUS_INCORRECT = "incorrect"
DISPOSAL_STATUS_UNCERTAIN = "uncertain"


class AnalyticsCollection:
    """Data-access manager for municipal analytics aggregation queries."""

    def __init__(self):
        self.disposals_col_name = CollectionNames.DISPOSALS.value
        self.users_col_name = CollectionNames.USERS.value
        self.redemptions_col_name = CollectionNames.REWARD_REDEMPTIONS.value
        self.tx_col_name = CollectionNames.CREDIT_TRANSACTIONS.value

    def _get_disposals(self):
        return get_collection(self.disposals_col_name)

    def _get_users(self):
        return get_collection(self.users_col_name)

    def _get_redemptions(self):
        return get_collection(self.redemptions_col_name)

    def _get_tx(self):
        return get_collection(self.tx_col_name)

    def get_summary_metrics(self, user_id: Optional[str] = None) -> AnalyticsSummaryDocument:
        """
        Executes MongoDB aggregation pipeline for waste segregation summary metrics.

        Args:
            user_id: Optional user ID to compute personal user metrics; otherwise platform-wide.

        Returns:
            AnalyticsSummaryDocument model instance.
        """
        now = datetime.now(timezone.utc)
        disposals_col = self._get_disposals()

        match_stage = {"$match": {"user_id": user_id}} if user_id else {"$match": {}}
        pipeline = [
            match_stage,
            {
                "$group": {
                    "_id": None,
                    "total": {"$sum": 1},
                    "verified": {"$sum": {"$cond": [{"$eq": ["$verification_status", DISPOSAL_STATUS_VERIFIED]}, 1, 0]}},
                    "incorrect": {"$sum": {"$cond": [{"$eq": ["$verification_status", DISPOSAL_STATUS_INCORRECT]}, 1, 0]}},
                    "uncertain": {"$sum": {"$cond": [{"$eq": ["$verification_status", DISPOSAL_STATUS_UNCERTAIN]}, 1, 0]}},
                    "credits_sum": {"$sum": "$credits_awarded"},
                }
            },
        ]

        try:
            res = list(disposals_col.aggregate(pipeline))
            stats = res[0] if res else {"total": 0, "verified": 0, "incorrect": 0, "uncertain": 0, "credits_sum": 0.0}

            total = stats["total"]
            verified = stats["verified"]
            rate = round((verified / total * 100.0), 2) if total > 0 else 0.0

            redemptions_count = 0
            try:
                redemptions_col = self._get_redemptions()
                redemptions_count = redemptions_col.count_documents({"user_id": user_id} if user_id else {})
            except Exception:
                pass

            active_users = 1 if user_id else 0
            if not user_id:
                try:
                    users_col = self._get_users()
                    active_users = users_col.count_documents({})
                except Exception:
                    active_users = 1

            return AnalyticsSummaryDocument(
                total_disposal_attempts=total,
                verified_disposals=verified,
                correct_segregation_rate=rate,
                incorrect_segregation_count=stats["incorrect"],
                uncertain_classification_count=stats["uncertain"],
                total_credits_issued=float(stats["credits_sum"]),
                total_reward_redemptions=redemptions_count,
                total_active_users=max(1, active_users),
                timestamp=now,
            )
        except PyMongoError as exc:
            logger.warning(f"MongoDB aggregation error in get_summary_metrics: {exc}")
            return AnalyticsSummaryDocument(
                total_disposal_attempts=0,
                verified_disposals=0,
                correct_segregation_rate=0.0,
                incorrect_segregation_count=0,
                uncertain_classification_count=0,
                total_credits_issued=0.0,
                total_reward_redemptions=0,
                total_active_users=1,
                timestamp=now,
            )

    def get_waste_stream_distribution(self, user_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Executes aggregation for stream volume counts and percentage distribution across statutory categories.
        """
        disposals_col = self._get_disposals()
        counts = {"Wet": 0, "Dry": 0, "Sanitary": 0, "Special Care": 0}

        match_stage = {"$match": {"user_id": user_id}} if user_id else {"$match": {}}
        pipeline = [
            match_stage,
            {"$group": {"_id": "$confirmed_category", "count": {"$sum": 1}}},
        ]

        try:
            cursor = disposals_col.aggregate(pipeline)
            for doc in cursor:
                cat = doc.get("_id")
                if cat in counts:
                    counts[cat] = doc.get("count", 0)
        except PyMongoError as exc:
            logger.warning(f"MongoDB get_waste_stream_distribution error: {exc}")

        total = sum(counts.values())
        percentages = {cat: round((c / total * 100.0), 2) if total > 0 else 0.0 for cat, c in counts.items()}

        return {
            "waste_counts_by_stream": counts,
            "stream_percentages": percentages,
            "total_count": total,
        }


analytics_collection = AnalyticsCollection()
