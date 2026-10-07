"""
Tests for Municipal Rewards Catalog and Incentive Redemption Endpoints.
"""

import uuid
from fastapi.testclient import TestClient
from app.main import app
from app.core.constants import WasteCategory
from app.services.credits_service import credits_service

client = TestClient(app)


def get_authenticated_headers_with_credits(amount: float = 100.0):
    """Helper to register user and pre-fund Swachh Credits balance."""
    uid = uuid.uuid4().hex[:8]
    email = f"reward_user_{uid}@example.com"
    password = "RewardPassword123"

    reg = client.post("/users/register", json={
        "name": "Reward Tester",
        "email": email,
        "password": password
    })
    user_id = reg.json()["id"]

    login_res = client.post("/users/login", json={"email": email, "password": password})
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Fund balance by recording verified disposals
    disposals_needed = int(amount // 10.0) + 1
    for _ in range(disposals_needed):
        client.post("/disposal", json={
            "prediction_id": str(uuid.uuid4()),
            "predicted_category": WasteCategory.DRY.value,
            "confirmed_category": WasteCategory.DRY.value,
            "confidence": 0.90
        }, headers=headers)

    return headers, user_id


def test_get_available_rewards_catalog():
    """Test retrieving active municipal reward catalog."""
    response = client.get("/rewards")
    assert response.status_code == 200
    catalog = response.json()
    assert len(catalog) >= 4
    reward_ids = [r["reward_id"] for r in catalog]
    assert "reward_tax_5pct" in reward_ids
    assert "reward_transit_pass" in reward_ids


def test_successful_reward_redemption():
    """Test successful redemption deducts credits and generates voucher code."""
    headers, user_id = get_authenticated_headers_with_credits(amount=100.0)

    bal_before = client.get("/credits", headers=headers).json()["swachh_credits"]
    assert bal_before >= 50.0

    # Redeem 50 credit metro pass reward
    red_res = client.post("/rewards/redeem/reward_transit_pass", headers=headers)
    assert red_res.status_code == 200
    red_data = red_res.json()
    assert "redemption_id" in red_data
    assert red_data["reward_id"] == "reward_transit_pass"
    assert red_data["credit_cost"] == 50.0
    assert red_data["redemption_code"].startswith("SWACHH-TRAN-")

    # Check updated balance
    bal_after = client.get("/credits", headers=headers).json()["swachh_credits"]
    assert bal_after == bal_before - 50.0

    # Check user redemptions history
    my_reds = client.get("/rewards/my-redemptions", headers=headers)
    assert my_reds.status_code == 200
    reds_list = my_reds.json()
    assert len(reds_list) >= 1
    assert reds_list[0]["redemption_id"] == red_data["redemption_id"]


def test_redemption_insufficient_credits():
    """Test redemption fails with 400 Bad Request when user has insufficient credits."""
    uid = uuid.uuid4().hex[:8]
    email = f"poor_user_{uid}@example.com"
    client.post("/users/register", json={"name": "No Credits", "email": email, "password": "Password123"})
    token = client.post("/users/login", json={"email": email, "password": "Password123"}).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Redeem 5 times 100-credit tax reward (using up 500 credits)
    for _ in range(5):
        client.post("/rewards/redeem/reward_tax_5pct", headers=headers)

    # Attempt 6th redemption with 0 balance remaining
    response = client.post("/rewards/redeem/reward_tax_5pct", headers=headers)
    assert response.status_code == 400
    data = response.json()
    assert data["success"] is False
    assert "Insufficient Swachh Credits" in data["error"]["message"]


def test_redemption_invalid_reward_id():
    """Test redemption with non-existent reward_id returns 400 Bad Request."""
    headers, _ = get_authenticated_headers_with_credits(amount=50.0)
    response = client.post("/rewards/redeem/invalid_reward_id_xyz", headers=headers)
    assert response.status_code == 400
    data = response.json()
    assert "invalid or unavailable" in data["error"]["message"]
