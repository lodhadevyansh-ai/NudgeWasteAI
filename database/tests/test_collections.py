"""
Unit Tests for Database Collections Data-Access Modules.
"""

from unittest.mock import MagicMock, patch
import uuid
import pytest
from pymongo.errors import DuplicateKeyError, PyMongoError

from database.schemas.user_schema import UserDocument
from database.schemas.disposal_schema import DisposalDocument
from database.schemas.nudge_schema import NudgeDocument
from database.schemas.credit_schema import CreditTransactionDocument
from database.schemas.reward_schema import RewardCatalogDocument, RewardRedemptionDocument
from database.schemas.prediction_schema import PredictionDocument
from database.schemas.waste_schema import WasteStreamDocument

from database.collections.users import UsersCollection, users_collection
from database.collections.disposals import DisposalsCollection, disposals_collection
from database.collections.nudges import NudgesCollection, nudges_collection
from database.collections.credits import CreditsCollection, credits_collection
from database.collections.rewards import RewardsCollection, rewards_collection
from database.collections.predictions import PredictionsCollection, predictions_collection
from database.collections.waste import WasteCollection, waste_collection
from database.collections.analytics import AnalyticsCollection, analytics_collection


# --- UsersCollection Tests ---

@patch.object(UsersCollection, "_get_col")
def test_users_collection_create_success(mock_get_col):
    mock_col = MagicMock()
    mock_get_col.return_value = mock_col

    user_id = str(uuid.uuid4())
    user = UserDocument(
        _id=user_id,
        name="Test User",
        email="test@example.com",
        hashed_password="hash_pwd_secret",
    )

    created = users_collection.create_user(user)
    assert created.id == user_id
    mock_col.insert_one.assert_called_once()


@patch.object(UsersCollection, "_get_col")
def test_users_collection_create_duplicate_error(mock_get_col):
    mock_col = MagicMock()
    mock_col.insert_one.side_effect = DuplicateKeyError("E11000 duplicate key error email")
    mock_get_col.return_value = mock_col

    user = UserDocument(
        _id=str(uuid.uuid4()),
        name="Dup User",
        email="dup@example.com",
        hashed_password="hash_pwd_secret",
    )

    with pytest.raises(ValueError, match="already exists"):
        users_collection.create_user(user)


@patch.object(UsersCollection, "_get_col")
def test_users_collection_get_by_email_found_and_not_found(mock_get_col):
    mock_col = MagicMock()
    user_id = str(uuid.uuid4())
    mock_col.find_one.side_effect = [
        {
            "_id": user_id,
            "id": user_id,
            "name": "Found User",
            "email": "found@example.com",
            "hashed_password": "hash",
            "swachh_credits": 10.0,
            "status": "active",
            "is_active": True,
        },
        None,
    ]
    mock_get_col.return_value = mock_col

    found = users_collection.get_user_by_email("found@example.com")
    assert found is not None
    assert found.email == "found@example.com"

    not_found = users_collection.get_user_by_email("missing@example.com")
    assert not_found is None


@patch.object(UsersCollection, "_get_col")
def test_users_collection_update_credits(mock_get_col):
    mock_col = MagicMock()
    mock_result = MagicMock()
    mock_result.matched_count = 1
    mock_col.update_one.return_value = mock_result
    mock_get_col.return_value = mock_col

    res = users_collection.update_user_credits("user_123", 15.0)
    assert res is True
    mock_col.update_one.assert_called_once()


# --- DisposalsCollection Tests ---

@patch.object(DisposalsCollection, "_get_col")
def test_disposals_collection_create_and_get(mock_get_col):
    mock_col = MagicMock()
    mock_get_col.return_value = mock_col

    disp_id = str(uuid.uuid4())
    disp = DisposalDocument(
        _id=disp_id,
        user_id="user_123",
        prediction_id="pred_123",
        predicted_category="Wet",
        confirmed_category="Wet",
        confidence=0.9,
        verification_status="verified",
        is_correctly_segregated=True,
        feedback_nudge="Great job!",
        credits_awarded=10.0,
    )

    disposals_collection.create_disposal(disp)
    mock_col.insert_one.assert_called_once()

    mock_col.find_one.return_value = disp.to_mongo_dict()
    found = disposals_collection.get_disposal_by_id(disp_id, user_id="user_123")
    assert found is not None
    assert found.disposal_id == disp_id


@patch.object(DisposalsCollection, "_get_col")
def test_disposals_collection_history(mock_get_col):
    mock_col = MagicMock()
    mock_cursor = MagicMock()
    disp_dict = {
        "_id": "disp_1",
        "disposal_id": "disp_1",
        "user_id": "user_123",
        "prediction_id": "pred_1",
        "predicted_category": "Dry",
        "confirmed_category": "Dry",
        "confidence": 0.95,
        "verification_status": "verified",
        "is_correctly_segregated": True,
        "feedback_nudge": "Verified!",
        "credits_awarded": 10.0,
    }
    mock_cursor.__iter__.return_value = iter([disp_dict])
    mock_cursor.sort.return_value = mock_cursor
    mock_cursor.skip.return_value = mock_cursor
    mock_cursor.limit.return_value = mock_cursor
    mock_col.find.return_value = mock_cursor
    mock_get_col.return_value = mock_col

    history = disposals_collection.get_user_disposal_history("user_123", limit=10, skip=0)
    assert len(history) == 1
    assert history[0].disposal_id == "disp_1"


# --- NudgesCollection Tests ---

@patch.object(NudgesCollection, "_get_col")
def test_nudges_collection_create_and_get(mock_get_col):
    mock_col = MagicMock()
    mock_get_col.return_value = mock_col

    nudge_id = str(uuid.uuid4())
    nudge = NudgeDocument(
        _id=nudge_id,
        waste_category="Sanitary",
        target_category="Sanitary",
        title="Sanitary Alert",
        message="Wrap securely",
        explanation="Prevent biohazard",
        action="Place in Red Bin",
        severity="warning",
    )

    nudges_collection.create_nudge(nudge)
    mock_col.insert_one.assert_called_once()

    mock_col.find_one.return_value = nudge.to_mongo_dict()
    found = nudges_collection.get_nudge_by_id(nudge_id)
    assert found is not None
    assert found.nudge_id == nudge_id


# --- CreditsCollection Tests ---

@patch.object(CreditsCollection, "_get_col")
def test_credits_collection_create_and_get_by_disposal(mock_get_col):
    mock_col = MagicMock()
    mock_get_col.return_value = mock_col

    tx_id = str(uuid.uuid4())
    tx = CreditTransactionDocument(
        _id=tx_id,
        user_id="user_123",
        amount=15.0,
        transaction_type="earn",
        reason="Sanitary Waste Segregation",
        disposal_id="disp_123",
    )

    credits_collection.create_transaction(tx)
    mock_col.insert_one.assert_called_once()

    mock_col.find_one.return_value = tx.to_mongo_dict()
    found = credits_collection.get_transaction_by_disposal_id("disp_123")
    assert found is not None
    assert found.transaction_id == tx_id


# --- RewardsCollection Tests ---

@patch.object(RewardsCollection, "_get_catalog_col")
@patch.object(RewardsCollection, "_get_redemptions_col")
def test_rewards_collection_catalog_and_redemption(mock_get_red_col, mock_get_cat_col):
    mock_cat_col = MagicMock()
    mock_red_col = MagicMock()
    mock_get_cat_col.return_value = mock_cat_col
    mock_get_red_col.return_value = mock_red_col

    reward_item = RewardCatalogDocument(
        _id="reward_transit",
        title="Transit Pass",
        description="7-day pass",
        credit_cost=50.0,
        reward_type="transit_pass",
        is_available=True,
    )
    rewards_collection.create_reward_catalog_item(reward_item)
    mock_cat_col.replace_one.assert_called_once()

    red_id = str(uuid.uuid4())
    red = RewardRedemptionDocument(
        _id=red_id,
        user_id="user_123",
        reward_id="reward_transit",
        reward_title="Transit Pass",
        credit_cost=50.0,
        redemption_code="SWACHH-TRAN-1234",
    )
    rewards_collection.create_redemption(red)
    mock_red_col.insert_one.assert_called_once()


# --- PredictionsCollection Tests ---

@patch.object(PredictionsCollection, "_get_col")
def test_predictions_collection_create_and_get(mock_get_col):
    mock_col = MagicMock()
    mock_get_col.return_value = mock_col

    pred_id = str(uuid.uuid4())
    pred = PredictionDocument(
        _id=pred_id,
        category="Special Care",
        confidence=0.96,
        is_uncertain=False,
        model_version="v1.0.0",
        processing_time_ms=15.0,
    )

    predictions_collection.create_prediction(pred)
    mock_col.insert_one.assert_called_once()

    mock_col.find_one.return_value = pred.to_mongo_dict()
    found = predictions_collection.get_prediction_by_id(pred_id)
    assert found is not None
    assert found.category == "Special Care"


# --- WasteCollection Tests ---

@patch.object(WasteCollection, "_get_col")
def test_waste_collection_get_streams(mock_get_col):
    mock_col = MagicMock()
    mock_cursor = MagicMock()
    wet_stream = {
        "category": "Wet",
        "description": "Organic kitchen waste",
        "bin_color": "Green",
        "credit_award": 10.0,
        "guidance_nudge": "Place in Green Bin",
    }
    mock_cursor.__iter__.return_value = iter([wet_stream])
    mock_col.find.return_value = mock_cursor
    mock_get_col.return_value = mock_col

    streams = waste_collection.get_all_waste_streams()
    assert len(streams) >= 1
    assert streams[0].category == "Wet"


# --- AnalyticsCollection Tests ---

@patch.object(AnalyticsCollection, "_get_disposals")
@patch.object(AnalyticsCollection, "_get_users")
@patch.object(AnalyticsCollection, "_get_redemptions")
def test_analytics_collection_summary(mock_get_red, mock_get_users, mock_get_disp):
    mock_disp = MagicMock()
    mock_users = MagicMock()
    mock_red = MagicMock()
    mock_get_disp.return_value = mock_disp
    mock_get_users.return_value = mock_users
    mock_get_red.return_value = mock_red

    mock_disp.aggregate.return_value = [{
        "total": 10,
        "verified": 8,
        "incorrect": 1,
        "uncertain": 1,
        "credits_sum": 80.0,
    }]
    mock_red.count_documents.return_value = 2
    mock_users.count_documents.return_value = 5

    summary = analytics_collection.get_summary_metrics(user_id=None)
    assert summary.total_disposal_attempts == 10
    assert summary.verified_disposals == 8
    assert summary.correct_segregation_rate == 80.0
    assert summary.total_credits_issued == 80.0
