"""
Unit Tests for Database Schemas and Validation Helpers.
"""

from datetime import datetime, timezone
import uuid
import bson
import pytest
from pydantic import ValidationError

from database.utils.validators import (
    validate_statutory_category,
    validate_disposal_status,
    validate_transaction_type,
    validate_nudge_severity,
    convert_objectid_to_str,
)
from database.utils.timestamps import now_utc, ensure_utc, format_iso
from database.schemas.user_schema import UserDocument
from database.schemas.waste_schema import WasteStreamDocument
from database.schemas.prediction_schema import PredictionDocument
from database.schemas.disposal_schema import DisposalDocument
from database.schemas.nudge_schema import NudgeDocument
from database.schemas.credit_schema import CreditTransactionDocument
from database.schemas.reward_schema import RewardCatalogDocument, RewardRedemptionDocument
from database.schemas.analytics_schema import AnalyticsSummaryDocument


def test_validator_helpers():
    """Tests validation utility functions."""
    assert validate_statutory_category("Wet") is True
    assert validate_statutory_category("Dry") is True
    assert validate_statutory_category("Sanitary") is True
    assert validate_statutory_category("Special Care") is True
    assert validate_statutory_category("InvalidCategory") is False
    assert validate_statutory_category(None) is False

    assert validate_disposal_status("verified") is True
    assert validate_disposal_status("incorrect") is True
    assert validate_disposal_status("unknown_status") is False

    assert validate_transaction_type("earn") is True
    assert validate_transaction_type("redeem") is True
    assert validate_transaction_type("invalid_tx") is False

    assert validate_nudge_severity("information") is True
    assert validate_nudge_severity("guidance") is True
    assert validate_nudge_severity("warning") is True
    assert validate_nudge_severity("critical") is False


def test_objectid_conversion():
    """Tests conversion of PyMongo ObjectId and string UUIDs."""
    oid = bson.ObjectId()
    assert convert_objectid_to_str(oid) == str(oid)
    uid = str(uuid.uuid4())
    assert convert_objectid_to_str(uid) == uid
    assert convert_objectid_to_str(None) == ""


def test_timestamp_utilities():
    """Tests UTC timestamp creation and ISO string formatting."""
    now = now_utc()
    assert now.tzinfo is not None
    assert now.tzinfo == timezone.utc

    iso = format_iso(now)
    assert isinstance(iso, str)

    naive = datetime.now()
    utc_naive = ensure_utc(naive)
    assert utc_naive.tzinfo == timezone.utc


def test_user_document_valid_and_mongo_dict():
    """Tests UserDocument validation and serialization."""
    user_id = str(uuid.uuid4())
    user_data = {
        "_id": user_id,
        "name": "Jane Doe",
        "email": "JANE@Example.com  ",
        "hashed_password": "hashed_secret_bcrypt",
        "swachh_credits": 25.0,
    }
    doc = UserDocument(**user_data)
    assert doc.id == user_id
    assert doc.email == "jane@example.com"
    assert doc.swachh_credits == 25.0

    mongo_dict = doc.to_mongo_dict()
    assert mongo_dict["_id"] == user_id
    assert mongo_dict["hashed_password"] == "hashed_secret_bcrypt"

    pub_dict = doc.to_public_dict()
    assert "hashed_password" not in pub_dict


def test_user_document_invalid():
    """Tests UserDocument validation failures."""
    with pytest.raises(ValidationError):
        UserDocument(
            _id="123",
            name="A",  # Too short (<2 chars)
            email="invalid-email",
            hashed_password="pwd",
        )


def test_waste_stream_document_valid_and_invalid():
    """Tests WasteStreamDocument category validation."""
    valid_waste = WasteStreamDocument(
        category="Wet",
        description="Organic food waste",
        bin_color="Green",
        credit_award=10.0,
        guidance_nudge="Place in Green Bin for composting.",
    )
    assert valid_waste.category == "Wet"

    with pytest.raises(ValidationError):
        WasteStreamDocument(
            category="HazardousChemicals",  # Invalid non-statutory category
            description="Test",
            bin_color="Red",
            credit_award=5.0,
            guidance_nudge="Nudge",
        )


def test_prediction_document():
    """Tests PredictionDocument creation and statutory category validation."""
    pred_id = str(uuid.uuid4())
    pred = PredictionDocument(
        _id=pred_id,
        category="Dry",
        confidence=0.92,
        is_uncertain=False,
        model_version="v1.0.0",
        processing_time_ms=12.5,
    )
    assert pred.prediction_id == pred_id
    assert pred.category == "Dry"
    assert pred.confidence == 0.92

    with pytest.raises(ValidationError):
        PredictionDocument(
            _id=pred_id,
            category="InvalidStream",
            confidence=0.5,
            is_uncertain=True,
            model_version="v1",
            processing_time_ms=10.0,
        )


def test_disposal_document():
    """Tests DisposalDocument verification status and statutory stream validation."""
    disp_id = str(uuid.uuid4())
    disp = DisposalDocument(
        _id=disp_id,
        user_id="user_123",
        prediction_id="pred_123",
        predicted_category="Sanitary",
        confirmed_category="Sanitary",
        confidence=0.95,
        verification_status="verified",
        is_correctly_segregated=True,
        feedback_nudge="Disposal verified!",
        credits_awarded=15.0,
    )
    assert disp.disposal_id == disp_id
    assert disp.verification_status == "verified"
    assert disp.credits_awarded == 15.0

    with pytest.raises(ValidationError):
        DisposalDocument(
            _id=disp_id,
            user_id="user_123",
            prediction_id="pred_123",
            predicted_category="Wet",
            confirmed_category="Wet",
            confidence=0.9,
            verification_status="invalid_status_enum",
            is_correctly_segregated=True,
            feedback_nudge="Nudge",
        )


def test_nudge_document():
    """Tests NudgeDocument severity constraint validation."""
    nudge_id = str(uuid.uuid4())
    nudge = NudgeDocument(
        _id=nudge_id,
        waste_category="Special Care",
        target_category="Special Care",
        title="Special Care Waste Safety",
        message="Handle e-waste carefully.",
        explanation="Prevent toxic leaching.",
        action="Deposit in Black Bin.",
        severity="warning",
    )
    assert nudge.nudge_id == nudge_id
    assert nudge.severity == "warning"

    with pytest.raises(ValidationError):
        NudgeDocument(
            _id=nudge_id,
            waste_category="Special Care",
            target_category="Special Care",
            title="Title",
            message="Msg",
            explanation="Exp",
            action="Act",
            severity="extreme_critical",  # Invalid severity
        )


def test_credit_transaction_document():
    """Tests CreditTransactionDocument type validation."""
    tx_id = str(uuid.uuid4())
    tx = CreditTransactionDocument(
        _id=tx_id,
        user_id="user_123",
        amount=10.0,
        transaction_type="earn",
        reason="Verified Disposal",
    )
    assert tx.transaction_id == tx_id
    assert tx.transaction_type == "earn"

    with pytest.raises(ValidationError):
        CreditTransactionDocument(
            _id=tx_id,
            user_id="user_123",
            amount=10.0,
            transaction_type="invalid_type",
            reason="Test",
        )


def test_reward_documents():
    """Tests RewardCatalogDocument and RewardRedemptionDocument."""
    cat = RewardCatalogDocument(
        _id="reward_tax_5pct",
        title="Property Tax Rebate",
        description="5% discount on municipal tax",
        credit_cost=100.0,
        reward_type="tax_discount",
        is_available=True,
    )
    assert cat.reward_id == "reward_tax_5pct"

    red_id = str(uuid.uuid4())
    red = RewardRedemptionDocument(
        _id=red_id,
        user_id="user_123",
        reward_id="reward_tax_5pct",
        reward_title="Property Tax Rebate",
        credit_cost=100.0,
        redemption_code="SWACHH-TAX-1234",
    )
    assert red.redemption_id == red_id
    assert red.redemption_code == "SWACHH-TAX-1234"


def test_analytics_summary_document():
    """Tests AnalyticsSummaryDocument validation."""
    summary = AnalyticsSummaryDocument(
        total_disposal_attempts=10,
        verified_disposals=8,
        correct_segregation_rate=80.0,
        incorrect_segregation_count=1,
        uncertain_classification_count=1,
        total_credits_issued=80.0,
        total_reward_redemptions=2,
        total_active_users=5,
    )
    assert summary.verified_disposals == 8
    assert summary.correct_segregation_rate == 80.0
