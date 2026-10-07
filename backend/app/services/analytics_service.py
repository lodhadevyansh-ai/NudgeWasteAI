"""
Analytics Service.
Aggregates waste segregation metrics, statutory stream distributions, time-series trends, and credit economics using database collections.
"""

from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional

from app.core.constants import (  # pyrefly: ignore [missing-import]
    WasteCategory,
    DISPOSAL_STATUS_VERIFIED,
    DISPOSAL_STATUS_INCORRECT,
    DISPOSAL_STATUS_UNCERTAIN,
    CREDIT_RULES_BY_CATEGORY,
)
from app.schemas.analytics import (  # pyrefly: ignore [missing-import]
    AnalyticsSummaryResponse,
    WasteDistributionResponse,
    TrendsResponse,
    CreditsAnalyticsResponse,
)
from app.services.disposal_service import disposal_service  # pyrefly: ignore [missing-import]
from app.services.credits_service import credits_service  # pyrefly: ignore [missing-import]
from app.services.reward_service import reward_service  # pyrefly: ignore [missing-import]
from app.services.user_service import user_service  # pyrefly: ignore [missing-import]
from app.utils.logger import logger  # pyrefly: ignore [missing-import]

from database.collections.analytics import analytics_collection  # pyrefly: ignore [missing-import]


class AnalyticsService:
    """Service layer executing efficient aggregation of civic waste data."""

    def get_summary(self, user_id: Optional[str] = None) -> AnalyticsSummaryResponse:
        """
        Calculates waste segregation summary metrics.
        If user_id is provided, aggregates for specific user; otherwise aggregates platform-wide.
        """
        try:
            db_summary = analytics_collection.get_summary_metrics(user_id=user_id)
            if db_summary and db_summary.total_disposal_attempts > 0:
                return AnalyticsSummaryResponse(**db_summary.model_dump())
        except Exception as exc:
            logger.warning(f"MongoDB analytics summary error: {exc}")

        # In-memory aggregation fallback
        now = datetime.now(timezone.utc)
        disposals = list(disposal_service._in_memory_store.values())
        if user_id:
            disposals = [d for d in disposals if d["user_id"] == user_id]

        total = len(disposals)
        verified = sum(1 for d in disposals if d.get("verification_status") == DISPOSAL_STATUS_VERIFIED)
        incorrect = sum(1 for d in disposals if d.get("verification_status") == DISPOSAL_STATUS_INCORRECT)
        uncertain = sum(1 for d in disposals if d.get("verification_status") == DISPOSAL_STATUS_UNCERTAIN)
        rate = round((verified / total * 100.0), 2) if total > 0 else 0.0

        credits_sum = sum(d.get("credits_awarded", 0.0) for d in disposals)
        redemptions = list(reward_service._in_memory_redemptions.values())
        if user_id:
            redemptions = [r for r in redemptions if r["user_id"] == user_id]

        active_users = 1 if user_id else max(1, len(user_service._in_memory_store))

        return AnalyticsSummaryResponse(
            total_disposal_attempts=total,
            verified_disposals=verified,
            correct_segregation_rate=rate,
            incorrect_segregation_count=incorrect,
            uncertain_classification_count=uncertain,
            total_credits_issued=credits_sum,
            total_reward_redemptions=len(redemptions),
            total_active_users=active_users,
            timestamp=now,
        )

    def get_waste_distribution(self, user_id: Optional[str] = None) -> WasteDistributionResponse:
        """Calculates volume counts and percentages across the 4 statutory waste streams."""
        try:
            dist = analytics_collection.get_waste_stream_distribution(user_id=user_id)
            if dist and dist.get("total_count", 0) > 0:
                return WasteDistributionResponse(**dist)
        except Exception as exc:
            logger.warning(f"MongoDB waste distribution error: {exc}")

        counts = {
            WasteCategory.WET.value: 0,
            WasteCategory.DRY.value: 0,
            WasteCategory.SANITARY.value: 0,
            WasteCategory.SPECIAL_CARE.value: 0,
        }

        disposals = list(disposal_service._in_memory_store.values())
        if user_id:
            disposals = [d for d in disposals if d["user_id"] == user_id]
        for d in disposals:
            cat = d.get("confirmed_category")
            if cat in counts:
                counts[cat] += 1

        total = sum(counts.values())
        percentages = {
            cat: round((c / total * 100.0), 2) if total > 0 else 0.0
            for cat, c in counts.items()
        }

        return WasteDistributionResponse(
            waste_counts_by_stream=counts,
            stream_percentages=percentages,
            total_count=total,
        )

    def get_disposal_trends(self, days: int = 30, user_id: Optional[str] = None) -> TrendsResponse:
        """Calculates daily time-series disposal and segregation trends."""
        disposals = list(disposal_service._in_memory_store.values())
        if user_id:
            disposals = [d for d in disposals if d["user_id"] == user_id]

        daily_map: Dict[str, Dict[str, int]] = {}
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)

        for d in disposals:
            ts = d.get("timestamp")
            if isinstance(ts, datetime) and ts >= cutoff:
                date_str = ts.strftime("%Y-%m-%d")
                if date_str not in daily_map:
                    daily_map[date_str] = {"total": 0, "verified": 0}
                daily_map[date_str]["total"] += 1
                if d.get("verification_status") == DISPOSAL_STATUS_VERIFIED:
                    daily_map[date_str]["verified"] += 1

        trends: List[Dict[str, Any]] = []
        for date_str in sorted(daily_map.keys()):
            tot = daily_map[date_str]["total"]
            ver = daily_map[date_str]["verified"]
            rate = round((ver / tot * 100.0), 2) if tot > 0 else 0.0
            trends.append({
                "date": date_str,
                "total_disposals": tot,
                "verified_disposals": ver,
                "segregation_rate": rate,
            })

        return TrendsResponse(daily_trends=trends, period_days=days)

    def get_credits_analytics(self) -> CreditsAnalyticsResponse:
        """Aggregates platform Swachh Credits issuance and redemption economics."""
        summary = self.get_summary()
        redeemed_sum = sum(r.get("credit_cost", 0.0) for r in reward_service._in_memory_redemptions.values())
        vouchers_count = len(reward_service._in_memory_redemptions)

        credits_by_cat = {
            WasteCategory.WET.value: 0.0,
            WasteCategory.DRY.value: 0.0,
            WasteCategory.SANITARY.value: 0.0,
            WasteCategory.SPECIAL_CARE.value: 0.0,
        }
        for d in disposal_service._in_memory_store.values():
            if d.get("verification_status") == DISPOSAL_STATUS_VERIFIED:
                cat = d.get("confirmed_category")
                if cat in credits_by_cat:
                    credits_by_cat[cat] += d.get("credits_awarded", CREDIT_RULES_BY_CATEGORY.get(cat, 10.0))

        net = max(0.0, summary.total_credits_issued - redeemed_sum)

        return CreditsAnalyticsResponse(
            total_credits_issued=summary.total_credits_issued,
            total_credits_redeemed=redeemed_sum,
            net_circulating_credits=net,
            total_redemption_vouchers=vouchers_count,
            credits_by_category=credits_by_cat,
        )


# Singleton instance
analytics_service = AnalyticsService()
