"""
Tests for User Management and Authentication Endpoints.
"""

import uuid
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_user_registration_success():
    """Test successful user registration (POST /users/register)."""
    uid = uuid.uuid4().hex[:8]
    payload = {
        "name": "Arjun Sharma",
        "email": f"arjun_{uid}@example.com",
        "password": "SecurePassword123",
        "mobile": "+919876543210"
    }
    response = client.post("/users/register", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert "id" in data
    assert data["name"] == payload["name"]
    assert data["email"] == payload["email"]
    assert data["mobile"] == payload["mobile"]
    assert data["swachh_credits"] == 500.0
    assert data["status"] == "active"
    assert data["is_active"] is True
    # Ensure sensitive password fields are never exposed
    assert "password" not in data
    assert "hashed_password" not in data


def test_user_registration_duplicate_email():
    """Test duplicate user registration returns 400 Bad Request."""
    uid = uuid.uuid4().hex[:8]
    payload = {
        "name": "First User",
        "email": f"duplicate_{uid}@example.com",
        "password": "Password123"
    }
    response1 = client.post("/users/register", json=payload)
    assert response1.status_code == 201

    # Attempt registration again with same email
    response2 = client.post("/users/register", json=payload)
    assert response2.status_code == 400
    data = response2.json()
    assert data["success"] is False
    assert data["error"]["code"] == 400
    assert "already exists" in data["error"]["message"]


def test_user_registration_invalid_email():
    """Test registration with invalid email format returns 422 Unprocessable Entity."""
    payload = {
        "name": "Invalid Email User",
        "email": "not-an-email",
        "password": "Password123"
    }
    response = client.post("/users/register", json=payload)
    assert response.status_code == 422
    data = response.json()
    assert data["success"] is False
    assert data["error"]["code"] == 422


def test_user_login_success():
    """Test successful user login returns JWT token."""
    uid = uuid.uuid4().hex[:8]
    email = f"login_{uid}@example.com"
    reg_payload = {
        "name": "Login User",
        "email": email,
        "password": "MySecretPassword123"
    }
    reg_response = client.post("/users/register", json=reg_payload)
    assert reg_response.status_code == 201

    # Login
    login_payload = {
        "email": email,
        "password": "MySecretPassword123"
    }
    login_response = client.post("/users/login", json=login_payload)
    assert login_response.status_code == 200
    token_data = login_response.json()
    assert "access_token" in token_data
    assert token_data["token_type"] == "bearer"
    assert len(token_data["access_token"]) > 20


def test_user_login_invalid_password():
    """Test login with incorrect password returns 401 Unauthorized."""
    uid = uuid.uuid4().hex[:8]
    email = f"wrongpwd_{uid}@example.com"
    reg_payload = {
        "name": "Wrong Password User",
        "email": email,
        "password": "CorrectPassword123"
    }
    client.post("/users/register", json=reg_payload)

    login_payload = {
        "email": email,
        "password": "WrongPassword999"
    }
    response = client.post("/users/login", json=login_payload)
    assert response.status_code == 401
    data = response.json()
    assert data["success"] is False
    assert data["error"]["code"] == 401


def test_get_current_user_me_authenticated():
    """Test GET /users/me with valid Bearer token returns current user profile."""
    uid = uuid.uuid4().hex[:8]
    email = f"profile_{uid}@example.com"
    reg_payload = {
        "name": "Profile User",
        "email": email,
        "password": "ProfilePassword123"
    }
    reg_res = client.post("/users/register", json=reg_payload)
    assert reg_res.status_code == 201
    user_id = reg_res.json()["id"]

    login_res = client.post("/users/login", json={
        "email": email,
        "password": "ProfilePassword123"
    })
    token = login_res.json()["access_token"]

    # Call GET /users/me with Bearer token
    headers = {"Authorization": f"Bearer {token}"}
    me_res = client.get("/users/me", headers=headers)
    assert me_res.status_code == 200
    me_data = me_res.json()
    assert me_data["id"] == user_id
    assert me_data["name"] == reg_payload["name"]
    assert me_data["email"] == reg_payload["email"]


def test_get_current_user_me_invalid_token():
    """Test GET /users/me with invalid JWT token returns 401 Unauthorized."""
    headers = {"Authorization": "Bearer invalid.jwt.token.string"}
    response = client.get("/users/me", headers=headers)
    assert response.status_code == 401
    data = response.json()
    assert data["success"] is False
    assert data["error"]["code"] == 401


def test_get_current_user_me_missing_token():
    """Test GET /users/me with missing Authorization header returns 401/403."""
    response = client.get("/users/me")
    assert response.status_code in [401, 403]


def test_delete_user_me_unauthenticated():
    """Test DELETE /users/me without token returns 401 Unauthorized."""
    response = client.delete("/users/me")
    assert response.status_code in [401, 403]


def test_delete_user_me_success_and_second_attempt():
    """Test successful account deletion via DELETE /users/me and subsequent access denial."""
    uid = uuid.uuid4().hex[:8]
    email = f"delete_{uid}@example.com"
    reg_res = client.post("/users/register", json={
        "name": "Delete Test User",
        "email": email,
        "password": "Password123"
    })
    assert reg_res.status_code == 201

    login_res = client.post("/users/login", json={"email": email, "password": "Password123"})
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Verify user exists
    me_before = client.get("/users/me", headers=headers)
    assert me_before.status_code == 200

    # Execute DELETE /users/me
    del_res = client.delete("/users/me", headers=headers)
    assert del_res.status_code == 200
    del_data = del_res.json()
    assert del_data.get("success") is True
    assert "deleted successfully" in del_data.get("message", "").lower()

    # GET /users/me must now fail
    me_after = client.get("/users/me", headers=headers)
    assert me_after.status_code == 401

    # Second DELETE attempt with same token must fail
    second_del = client.delete("/users/me", headers=headers)
    assert second_del.status_code in [401, 404]


def test_delete_user_isolation_and_reregistration():
    """Test deletion isolation between User A & User B and re-registration fresh start."""
    uid_a = uuid.uuid4().hex[:8]
    uid_b = uuid.uuid4().hex[:8]
    email_a = f"usera_{uid_a}@example.com"
    email_b = f"userb_{uid_b}@example.com"

    # Create User A
    res_a = client.post("/users/register", json={"name": "User A", "email": email_a, "password": "Password123"})
    token_a = client.post("/users/login", json={"email": email_a, "password": "Password123"}).json()["access_token"]
    headers_a = {"Authorization": f"Bearer {token_a}"}

    # Create User B
    res_b = client.post("/users/register", json={"name": "User B", "email": email_b, "password": "Password123"})
    token_b = client.post("/users/login", json={"email": email_b, "password": "Password123"}).json()["access_token"]
    headers_b = {"Authorization": f"Bearer {token_b}"}

    # Delete User A
    del_a = client.delete("/users/me", headers=headers_a)
    assert del_a.status_code == 200

    # User B profile & credits must remain unaffected
    me_b = client.get("/users/me", headers=headers_b)
    assert me_b.status_code == 200
    assert me_b.json()["email"] == email_b
    assert me_b.json()["swachh_credits"] == 500.0

    # Re-register with User A's email
    re_reg = client.post("/users/register", json={"name": "User A New", "email": email_a, "password": "NewPassword123"})
    assert re_reg.status_code == 201
    new_a_data = re_reg.json()
    assert new_a_data["email"] == email_a
    assert new_a_data["swachh_credits"] == 500.0

