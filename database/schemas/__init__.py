"""
Database document schemas package exports.
"""

from database.schemas.user_schema import UserDocument
from database.schemas.waste_schema import WasteStreamDocument
from database.schemas.prediction_schema import PredictionDocument
from database.schemas.disposal_schema import DisposalDocument
from database.schemas.nudge_schema import NudgeDocument
from database.schemas.credit_schema import CreditTransactionDocument
from database.schemas.reward_schema import RewardCatalogDocument, RewardRedemptionDocument
from database.schemas.analytics_schema import AnalyticsSummaryDocument

__all__ = [
    "UserDocument",
    "WasteStreamDocument",
    "PredictionDocument",
    "DisposalDocument",
    "NudgeDocument",
    "CreditTransactionDocument",
    "RewardCatalogDocument",
    "RewardRedemptionDocument",
    "AnalyticsSummaryDocument",
]
