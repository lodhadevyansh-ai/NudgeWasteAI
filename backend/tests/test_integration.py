"""
End-to-End Integration Tests for NudgeWasteAI Backend Workflow.
Verifies the complete flow: Auth -> Prediction -> Disposal -> Nudge -> Credits -> Rewards -> Analytics.
"""

import uuid
from fastapi.testclient import TestClient
from app.main import app
from app.core.constants import WasteCategory

client = TestClient(app)


def test_full_end_to_end_civic_flow():
    """Verifies the complete end-to-end backend workflow."""
    uid = uuid.uuid4().hex[:8]
    email = f"e2e_citizen_{uid}@example.com"
    password = "E2EPassword123"

    # 1. Registration
    reg_res = client.post("/users/register", json={
        "name": "E2E Citizen",
        "email": email,
        "password": password
    })
    assert reg_res.status_code == 201
    user_id = reg_res.json()["id"]

    # 2. Login
    login_res = client.post("/users/login", json={"email": email, "password": password})
    assert login_res.status_code == 200
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 3. User Profile Check
    me_res = client.get("/users/me", headers=headers)
    assert me_res.status_code == 200
    assert me_res.json()["id"] == user_id

    # 4. Waste Prediction (Special Care - Battery)
    pred_res = client.post("/prediction", json={
        "item_label": "Lithium Battery E-Waste",
        "image_base64": "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
    })
    assert pred_res.status_code == 200
    pred_data = pred_res.json()
    assert pred_data["category"] == WasteCategory.SPECIAL_CARE.value
    pred_id = pred_data["prediction_id"]

    # 5. Disposal Verification
    disp_res = client.post("/disposal", json={
        "prediction_id": pred_id,
        "predicted_category": WasteCategory.SPECIAL_CARE.value,
        "confirmed_category": WasteCategory.SPECIAL_CARE.value,
        "confidence": 0.95,
        "item_label": "Lithium Battery E-Waste"
    }, headers=headers)
    assert disp_res.status_code == 201
    disp_data = disp_res.json()
    assert disp_data["verification_status"] == "verified"
    assert disp_data["credits_awarded"] == 20.0  # Special Care awards 20 credits

    # 6. Nudge Generation
    nudge_res = client.post("/nudges/generate", json={
        "predicted_category": WasteCategory.SPECIAL_CARE.value,
        "confirmed_category": WasteCategory.SPECIAL_CARE.value,
        "confidence": 0.95
    })
    assert nudge_res.status_code == 200
    assert nudge_res.json()["severity"] == "information"

    # 7. Swachh Credits Check
    cred_res = client.get("/credits", headers=headers)
    assert cred_res.status_code == 200
    assert cred_res.json()["swachh_credits"] == 520.0

    # 8. Rewards Catalog & Redemption
    client.post("/disposal", json={
        "prediction_id": str(uuid.uuid4()),
        "predicted_category": WasteCategory.SPECIAL_CARE.value,
        "confirmed_category": WasteCategory.SPECIAL_CARE.value,
        "confidence": 0.95
    }, headers=headers)

    client.post("/disposal", json={
        "prediction_id": str(uuid.uuid4()),
        "predicted_category": WasteCategory.SPECIAL_CARE.value,
        "confirmed_category": WasteCategory.SPECIAL_CARE.value,
        "confidence": 0.95
    }, headers=headers)

    bal_before = client.get("/credits", headers=headers).json()["swachh_credits"]
    assert bal_before == 560.0

    # Redeem Transit Pass (50 credits)
    red_res = client.post("/rewards/redeem/reward_transit_pass", headers=headers)
    assert red_res.status_code == 200
    assert red_res.json()["credit_cost"] == 50.0

    bal_after = client.get("/credits", headers=headers).json()["swachh_credits"]
    assert bal_after == 510.0

    # 9. User Analytics Verification
    analytics_res = client.get("/analytics/user", headers=headers)
    assert analytics_res.status_code == 200
    analytics_data = analytics_res.json()
    assert analytics_data["total_disposal_attempts"] == 3
    assert analytics_data["verified_disposals"] == 3
    assert analytics_data["correct_segregation_rate"] == 100.0
