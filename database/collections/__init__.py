"""
Database collections package exports.
"""

from database.collections.users import UsersCollection, users_collection
from database.collections.disposals import DisposalsCollection, disposals_collection
from database.collections.nudges import NudgesCollection, nudges_collection
from database.collections.credits import CreditsCollection, credits_collection
from database.collections.rewards import RewardsCollection, rewards_collection
from database.collections.predictions import PredictionsCollection, predictions_collection
from database.collections.waste import WasteCollection, waste_collection
from database.collections.analytics import AnalyticsCollection, analytics_collection

__all__ = [
    "UsersCollection",
    "users_collection",
    "DisposalsCollection",
    "disposals_collection",
    "NudgesCollection",
    "nudges_collection",
    "CreditsCollection",
    "credits_collection",
    "RewardsCollection",
    "rewards_collection",
    "PredictionsCollection",
    "predictions_collection",
    "WasteCollection",
    "waste_collection",
    "AnalyticsCollection",
    "analytics_collection",
]
