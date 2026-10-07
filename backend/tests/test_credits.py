"""
Tests for Swachh Credits Endpoints and Service Logic.
"""

import uuid
from fastapi.testclient import TestClient
from app.main import app
from app.core.constants import WasteCategory
from app.services.credits_service import credits_service

client = TestClient(app)


def get_authenticated_headers():
    """Helper to register and log in a test user, returning auth Bearer headers."""
    uid = uuid.uuid4().hex[:8]
    email = f"credit_user_{uid}@example.com"
    password = "CreditPassword123"

    reg = client.post("/users/register", json={
        "name": "Credit Tester",
        "email": email,
        "password": password
    })
    user_id = reg.json()["id"]

    login_res = client.post("/users/login", json={"email": email, "password": password})
    token = login_res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}, user_id


def test_earning_credits_on_verified_disposal():
    """Test recording a verified disposal automatically awards Swachh Credits."""
    headers, user_id = get_authenticated_headers()
    prediction_id = str(uuid.uuid4())

    disposal_payload = {
        "prediction_id": prediction_id,
        "predicted_category": WasteCategory.SPECIAL_CARE.value,
        "confirmed_category": WasteCategory.SPECIAL_CARE.value,
        "confidence": 0.95
    }

    response = client.post("/disposal", json=disposal_payload, headers=headers)
    assert response.status_code == 201
    disp_data = response.json()
    assert disp_data["credits_awarded"] == 20.0  # Special Care earns 20.0 credits

    # Check GET /credits balance
    bal_res = client.get("/credits", headers=headers)
    assert bal_res.status_code == 200
    bal_data = bal_res.json()
    assert bal_data["swachh_credits"] == 520.0
    assert bal_data["total_earned"] == 520.0


def test_duplicate_credit_award_prevention():
    """Test that calling award_disposal_credits twice on the same disposal_id prevents double crediting."""
    headers, user_id = get_authenticated_headers()
    disposal_id = str(uuid.uuid4())

    # First award (Success)
    tx1 = credits_service.award_disposal_credits(
        user_id=user_id,
        disposal_id=disposal_id,
        confirmed_category=WasteCategory.DRY.value,
        verification_status="verified",
        is_correctly_segregated=True
    )
    assert tx1 is not None
    assert tx1.amount == 10.0

    # Second award attempt on same disposal_id (Blocked)
    tx2 = credits_service.award_disposal_credits(
        user_id=user_id,
        disposal_id=disposal_id,
        confirmed_category=WasteCategory.DRY.value,
        verification_status="verified",
        is_correctly_segregated=True
    )
    assert tx2 is None


def test_get_credit_transaction_history():
    """Test retrieving auditable credit transaction history."""
    headers, user_id = get_authenticated_headers()

    # Create 2 disposals
    client.post("/disposal", json={
        "prediction_id": str(uuid.uuid4()),
        "predicted_category": WasteCategory.WET.value,
        "confirmed_category": WasteCategory.WET.value,
        "confidence": 0.90
    }, headers=headers)

    client.post("/disposal", json={
        "prediction_id": str(uuid.uuid4()),
        "predicted_category": WasteCategory.DRY.value,
        "confirmed_category": WasteCategory.DRY.value,
        "confidence": 0.90
    }, headers=headers)

    history_res = client.get("/credits/history", headers=headers)
    assert history_res.status_code == 200
    history = history_res.json()
    assert len(history) >= 2
    assert history[0]["transaction_type"] == "earn"
    assert "Verified" in history[0]["reason"]
