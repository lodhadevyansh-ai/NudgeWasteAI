"""
Tests for Health Check and API foundation.
"""

from fastapi.testclient import TestClient
from app.main import app
from app.core.constants import STATUS_HEALTHY

client = TestClient(app)


def test_health_check_endpoint():
    """Test GET /health endpoint returns 200 OK and valid status payload."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == STATUS_HEALTHY
    assert "service" in data
    assert "environment" in data
    assert "version" in data


def test_cors_headers():
    """Test CORS headers are returned for preflight requests."""
    response = client.options(
        "/health",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == "http://localhost:3000"


def test_404_error_handler():
    """Test custom exception handler for unknown endpoints."""
    response = client.get("/non-existent-route")
    assert response.status_code == 404
    data = response.json()
    assert data["success"] is False
    assert data["error"]["code"] == 404
    assert "path" in data
