"""
Tests for Analytics and Reporting Endpoints.
"""

import uuid
from fastapi.testclient import TestClient
from app.main import app
from app.core.constants import WasteCategory

client = TestClient(app)


def get_authenticated_headers():
    """Helper to register and log in a test user, returning auth Bearer headers."""
    uid = uuid.uuid4().hex[:8]
    email = f"analytics_user_{uid}@example.com"
    password = "AnalyticsPassword123"

    client.post("/users/register", json={
        "name": "Analytics Tester",
        "email": email,
        "password": password
    })
    login_res = client.post("/users/login", json={"email": email, "password": password})
    token = login_res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_get_platform_analytics_summary():
    """Test GET /analytics/summary returns aggregated platform metrics."""
    response = client.get("/analytics/summary")
    assert response.status_code == 200
    data = response.json()
    assert "total_disposal_attempts" in data
    assert "verified_disposals" in data
    assert "correct_segregation_rate" in data
    assert "total_credits_issued" in data
    assert "timestamp" in data


def test_get_user_personal_analytics():
    """Test GET /analytics/user returns user-specific analytics."""
    headers = get_authenticated_headers()

    # Create 1 disposal
    client.post("/disposal", json={
        "prediction_id": str(uuid.uuid4()),
        "predicted_category": WasteCategory.DRY.value,
        "confirmed_category": WasteCategory.DRY.value,
        "confidence": 0.90
    }, headers=headers)

    response = client.get("/analytics/user", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["total_disposal_attempts"] >= 1
    assert data["verified_disposals"] >= 1
    assert data["correct_segregation_rate"] == 100.0


def test_get_waste_distribution():
    """Test GET /analytics/waste-distribution returns statutory stream counts and percentages."""
    response = client.get("/analytics/waste-distribution")
    assert response.status_code == 200
    data = response.json()
    assert "waste_counts_by_stream" in data
    assert "stream_percentages" in data
    assert "Wet" in data["waste_counts_by_stream"]
    assert "Dry" in data["waste_counts_by_stream"]
    assert "Sanitary" in data["waste_counts_by_stream"]
    assert "Special Care" in data["waste_counts_by_stream"]


def test_get_segregation_trends():
    """Test GET /analytics/trends returns time-series trend data."""
    response = client.get("/analytics/trends?days=30")
    assert response.status_code == 200
    data = response.json()
    assert "daily_trends" in data
    assert data["period_days"] == 30


def test_get_credits_analytics():
    """Test GET /analytics/credits returns platform credit issuance metrics."""
    response = client.get("/analytics/credits")
    assert response.status_code == 200
    data = response.json()
    assert "total_credits_issued" in data
    assert "total_credits_redeemed" in data
    assert "net_circulating_credits" in data
    assert "credits_by_category" in data
