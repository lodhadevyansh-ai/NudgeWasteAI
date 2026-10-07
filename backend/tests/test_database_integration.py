"""
Integration Tests for Backend-to-Database Package Integration.
Tests application lifespan hooks, end-to-end API read/write flows, and database health status.
"""

import uuid
import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    """FastAPI TestClient fixture."""
    with TestClient(app) as test_client:
        yield test_client


def test_health_endpoint_with_database_status(client):
    """Tests GET /health returns application status and database diagnostics."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "NudgeWasteAI Backend"
    assert "database" in data
    assert "status" in data["database"]


def test_end_to_end_user_registration_login_profile_flow(client):
    """Tests end-to-end flow: user registration -> login authentication -> profile retrieval."""
    unique_email = f"integration_{uuid.uuid4().hex[:8]}@example.com"
    reg_payload = {
        "name": "Integration User",
        "email": unique_email,
        "mobile": "+919999988888",
        "password": "SecurePassword123",
    }

    # 1. Register User
    reg_res = client.post("/api/v1/users/register", json=reg_payload)
    assert reg_res.status_code == 201
    user_data = reg_res.json()
    assert user_data["email"] == unique_email
    assert "id" in user_data
    assert "hashed_password" not in user_data

    # 2. Login User
    login_res = client.post(
        "/api/v1/users/login",
        json={"email": unique_email, "password": "SecurePassword123"},
    )
    assert login_res.status_code == 200
    token_data = login_res.json()
    assert "access_token" in token_data
    token = token_data["access_token"]

    # 3. Retrieve Profile via Auth Header
    headers = {"Authorization": f"Bearer {token}"}
    me_res = client.get("/api/v1/users/me", headers=headers)
    assert me_res.status_code == 200
    me_data = me_res.json()
    assert me_data["email"] == unique_email


def test_end_to_end_prediction_disposal_credits_flow(client):
    """Tests end-to-end flow: waste classification -> verified disposal -> credit award -> balance check."""
    unique_email = f"disposal_{uuid.uuid4().hex[:8]}@example.com"
    client.post(
        "/api/v1/users/register",
        json={"name": "Disposal Citizen", "email": unique_email, "password": "Password123"},
    )
    login_res = client.post(
        "/api/v1/users/login",
        json={"email": unique_email, "password": "Password123"},
    )
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Waste Prediction
    pred_res = client.post("/api/v1/prediction", json={"item_label": "apple peel kitchen food"})
    assert pred_res.status_code == 200
    pred_data = pred_res.json()
    assert pred_data["category"] == "Wet"
    pred_id = pred_data["prediction_id"]

    # 2. Record Disposal
    disp_res = client.post(
        "/api/v1/disposal",
        headers=headers,
        json={
            "prediction_id": pred_id,
            "predicted_category": "Wet",
            "confirmed_category": "Wet",
            "confidence": 0.95,
        },
    )
    assert disp_res.status_code == 201
    disp_data = disp_res.json()
    assert disp_data["verification_status"] == "verified"
    assert disp_data["credits_awarded"] == 10.0

    # 3. Check Swachh Credits Balance
    credits_res = client.get("/api/v1/credits", headers=headers)
    assert credits_res.status_code == 200
    credits_data = credits_res.json()
    assert credits_data["swachh_credits"] >= 10.0


def test_end_to_end_reward_redemption_flow(client):
    """Tests end-to-end flow: earning credits -> redeeming reward voucher -> checking redemptions."""
    unique_email = f"reward_{uuid.uuid4().hex[:8]}@example.com"
    client.post(
        "/api/v1/users/register",
        json={"name": "Reward Citizen", "email": unique_email, "password": "Password123"},
    )
    login_res = client.post(
        "/api/v1/users/login",
        json={"email": unique_email, "password": "Password123"},
    )
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Earn credits via 5 verified disposals (5 * 10 = 50 credits)
    for i in range(5):
        client.post(
            "/api/v1/disposal",
            headers=headers,
            json={
                "prediction_id": f"pred_reward_{uuid.uuid4().hex[:6]}",
                "predicted_category": "Wet",
                "confirmed_category": "Wet",
                "confidence": 0.95,
            },
        )

    # Check available rewards catalog
    catalog_res = client.get("/api/v1/rewards")
    assert catalog_res.status_code == 200
    catalog = catalog_res.json()
    assert len(catalog) >= 1

    # Redeem 50-credit Transit Pass reward
    red_res = client.post("/api/v1/rewards/redeem/reward_transit_pass", headers=headers)
    assert red_res.status_code == 200
    red_data = red_res.json()
    assert red_data["reward_id"] == "reward_transit_pass"
    assert "redemption_code" in red_data

    # Check user redemptions history
    my_reds_res = client.get("/api/v1/rewards/my-redemptions", headers=headers)
    assert my_reds_res.status_code == 200
    assert len(my_reds_res.json()) >= 1


def test_analytics_summary_endpoint(client):
    """Tests GET /analytics/summary endpoint."""
    res = client.get("/api/v1/analytics/summary")
    assert res.status_code == 200
    data = res.json()
    assert "total_disposal_attempts" in data
    assert "correct_segregation_rate" in data
