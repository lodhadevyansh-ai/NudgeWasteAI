"""
Tests for Waste Disposal Verification and History Endpoints.
"""

import uuid
from fastapi.testclient import TestClient
from app.main import app
from app.core.constants import (
    WasteCategory,
    DISPOSAL_STATUS_VERIFIED,
    DISPOSAL_STATUS_INCORRECT,
    DISPOSAL_STATUS_UNCERTAIN,
)

client = TestClient(app)


def get_authenticated_user_headers():
    """Helper to register and log in a test user, returning auth Bearer headers."""
    uid = uuid.uuid4().hex[:8]
    email = f"disposal_user_{uid}@example.com"
    password = "DisposalPassword123"

    client.post("/users/register", json={
        "name": "Disposal Tester",
        "email": email,
        "password": password
    })
    login_res = client.post("/users/login", json={"email": email, "password": password})
    token = login_res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_record_valid_disposal_success():
    """Test valid disposal recording returns 201 Created and 'verified' status."""
    headers = get_authenticated_user_headers()
    prediction_id = str(uuid.uuid4())

    payload = {
        "prediction_id": prediction_id,
        "predicted_category": WasteCategory.DRY.value,
        "confirmed_category": WasteCategory.DRY.value,
        "confidence": 0.88,
        "item_label": "Plastic Water Bottle",
        "location_zone": "Zone 4 - South Ward"
    }

    response = client.post("/disposal", json=payload, headers=headers)
    assert response.status_code == 201
    data = response.json()
    assert "disposal_id" in data
    assert data["prediction_id"] == prediction_id
    assert data["predicted_category"] == WasteCategory.DRY.value
    assert data["confirmed_category"] == WasteCategory.DRY.value
    assert data["verification_status"] == DISPOSAL_STATUS_VERIFIED
    assert data["is_correctly_segregated"] is True
    assert "Disposal verified!" in data["feedback_nudge"]


def test_record_disposal_category_mismatch():
    """Test prediction mismatch produces HTTP 400 rejection."""
    headers = get_authenticated_user_headers()
    prediction_id = str(uuid.uuid4())

    payload = {
        "prediction_id": prediction_id,
        "predicted_category": WasteCategory.WET.value,
        "confirmed_category": WasteCategory.DRY.value,
        "confidence": 0.85
    }

    response = client.post("/disposal", json=payload, headers=headers)
    assert response.status_code == 400
    data = response.json()
    msg = data.get("error", {}).get("message") or data.get("detail") or ""
    assert "Incorrect waste stream" in msg


def test_record_disposal_low_confidence_uncertain():
    """Test low confidence prediction results in HTTP 400 rejection."""
    headers = get_authenticated_user_headers()
    prediction_id = str(uuid.uuid4())

    payload = {
        "prediction_id": prediction_id,
        "predicted_category": WasteCategory.SANITARY.value,
        "confirmed_category": WasteCategory.SANITARY.value,
        "confidence": 0.45
    }

    response = client.post("/disposal", json=payload, headers=headers)
    assert response.status_code == 400


def test_record_disposal_invalid_category():
    """Test disposal with invalid category returns 422 / 400 Bad Request."""
    headers = get_authenticated_user_headers()
    prediction_id = str(uuid.uuid4())

    payload = {
        "prediction_id": prediction_id,
        "predicted_category": "Invalid_Custom_Category",
        "confidence": 0.90
    }

    response = client.post("/disposal", json=payload, headers=headers)
    assert response.status_code in [400, 422]


def test_record_disposal_missing_prediction():
    """Test disposal request missing prediction_id returns 422 / 400."""
    headers = get_authenticated_user_headers()

    payload = {
        "predicted_category": WasteCategory.WET.value,
        "confidence": 0.80
    }

    response = client.post("/disposal", json=payload, headers=headers)
    assert response.status_code in [400, 422]


def test_disposal_unauthorized_access():
    """Test disposal endpoints without auth header return 401/403."""
    response = client.post("/disposal", json={"prediction_id": "test", "predicted_category": "Wet"})
    assert response.status_code in [401, 403]

    response_history = client.get("/disposal/history")
    assert response_history.status_code in [401, 403]


def test_disposal_user_isolation_and_history():
    """Test user can view their history and cannot access another user's disposal record."""
    user1_headers = get_authenticated_user_headers()
    user2_headers = get_authenticated_user_headers()

    # User 1 creates disposal
    payload1 = {
        "prediction_id": str(uuid.uuid4()),
        "predicted_category": WasteCategory.SPECIAL_CARE.value,
        "confidence": 0.95,
        "item_label": "E-Waste Battery"
    }
    res1 = client.post("/disposal", json=payload1, headers=user1_headers)
    assert res1.status_code == 201
    disposal_id = res1.json()["disposal_id"]

    # User 1 fetches history (should contain the disposal)
    history1 = client.get("/disposal/history", headers=user1_headers)
    assert history1.status_code == 200
    assert len(history1.json()) >= 1
    assert history1.json()[0]["disposal_id"] == disposal_id

    # User 1 accesses single record (success)
    rec1 = client.get(f"/disposal/{disposal_id}", headers=user1_headers)
    assert rec1.status_code == 200

    # User 2 attempts to access User 1's disposal record (should be 404 Not Found / Isolated)
    rec2 = client.get(f"/disposal/{disposal_id}", headers=user2_headers)
    assert rec2.status_code == 404
