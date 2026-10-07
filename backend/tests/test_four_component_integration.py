"""
Four-Component End-to-End Integration Test Suite.
Verifies explicit integration across:
Frontend Request Layer -> Backend Application (FastAPI) -> Machine_Learning Predictor -> Database & MongoDB
"""

import io
import uuid
import pytest
from PIL import Image
from fastapi.testclient import TestClient

from app.main import app
from database.collections.predictions import predictions_collection
from database.collections.disposals import disposals_collection
from database.collections.credits import credits_collection
from database.collections.rewards import rewards_collection
from database.collections.users import users_collection

client = TestClient(app)


def create_sample_image_bytes() -> bytes:
    """Generates a raw JPEG image byte buffer."""
    img = Image.new("RGB", (224, 224), color=(34, 139, 34))
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()


def test_four_component_full_lifecycle():
    """
    Executes an end-to-end integration scenario connecting:
    1. User Registration & Initial 500 Swachh Credit Grant
    2. ML Prediction execution & persistence in MongoDB
    3. Wrong-bin rejection check
    4. Two-step verified disposal & credit transaction log
    5. Reward redemption & balance deduction
    6. User data isolation & complete account deletion workflow
    """
    uid = uuid.uuid4().hex[:8]
    email = f"e2e_citizen_{uid}@nudgewaste.ai"
    password = "SecurePassword123!"

    # -------------------------------------------------------------
    # 1. USER REGISTRATION & INITIAL BALANCE
    # -------------------------------------------------------------
    reg_res = client.post("/users/register", json={
        "name": "Civic Integration User",
        "email": email,
        "password": password,
        "city": "Indore Municipal Corporation"
    })
    assert reg_res.status_code == 201
    user_id = reg_res.json()["id"]
    assert reg_res.json()["swachh_credits"] == 500.0

    # Authenticate to obtain Bearer JWT token
    login_res = client.post("/users/login", json={"email": email, "password": password})
    assert login_res.status_code == 200
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Verify profile endpoint returns authoritative initial state
    profile_res = client.get("/users/me", headers=headers)
    assert profile_res.status_code == 200
    assert profile_res.json()["swachh_credits"] == 500.0

    # -------------------------------------------------------------
    # 2. ML CLASSIFICATION & PREDICTION PERSISTENCE
    # -------------------------------------------------------------
    img_bytes = create_sample_image_bytes()
    files = {"file": ("test_waste_item.jpg", img_bytes, "image/jpeg")}

    pred_res = client.post("/prediction/upload", files=files, headers=headers)
    assert pred_res.status_code == 200
    pred_data = pred_res.json()

    prediction_id = pred_data["prediction_id"]
    predicted_category = pred_data["category"]
    assert prediction_id is not None
    assert predicted_category in ["Wet", "Dry", "Sanitary", "Special Care"]
    assert pred_data["is_uncertain"] is False
    assert "model_version" in pred_data
    assert "all_probabilities" in pred_data

    # Verify prediction document is persisted in MongoDB predictions collection
    db_pred = predictions_collection.get_prediction_by_id(prediction_id)
    assert db_pred is not None
    assert db_pred.category == predicted_category

    # -------------------------------------------------------------
    # 3. WRONG BIN REJECTION VALIDATION (SERVER-SIDE 400 REJECTION)
    # -------------------------------------------------------------
    wrong_category = "Wet" if predicted_category != "Wet" else "Dry"
    wrong_disposal_payload = {
        "prediction_id": prediction_id,
        "predicted_category": predicted_category,
        "confirmed_category": wrong_category,
        "selected_bin_category": wrong_category,
        "confirmation_proof": "sample_proof_base64_data",
    }
    wrong_res = client.post("/disposal/verify", json=wrong_disposal_payload, headers=headers)
    assert wrong_res.status_code == 400
    assert "Incorrect waste stream" in (wrong_res.json().get("error", {}).get("message") or wrong_res.json().get("detail") or "")

    # -------------------------------------------------------------
    # 4. VERIFIED DISPOSAL & CREDIT AWARD (+10 CREDITS)
    # -------------------------------------------------------------
    valid_disposal_payload = {
        "prediction_id": prediction_id,
        "predicted_category": predicted_category,
        "confirmed_category": predicted_category,
        "selected_bin_category": predicted_category,
        "confirmation_proof": "valid_photo_disposal_proof_data",
        "item_label": "Sorted Waste Packaging",
    }
    disp_res = client.post("/disposal/verify", json=valid_disposal_payload, headers=headers)
    assert disp_res.status_code == 201
    disp_data = disp_res.json()

    assert disp_data["verification_status"] == "verified"
    assert disp_data["is_correctly_segregated"] is True
    assert disp_data["credits_awarded"] > 0.0
    disposal_id = disp_data["disposal_id"]

    # Verify credit balance updated on server
    bal_res = client.get("/credits", headers=headers)
    assert bal_res.status_code == 200
    new_balance = bal_res.json()["swachh_credits"]
    assert new_balance == 500.0 + disp_data["credits_awarded"]

    # -------------------------------------------------------------
    # 5. REWARD REDEMPTION & ATOMIC BALANCE DEDUCTION
    # -------------------------------------------------------------
    catalog_res = client.get("/rewards", headers=headers)
    assert catalog_res.status_code == 200
    rewards = catalog_res.json()
    assert len(rewards) > 0

    target_reward = rewards[0]
    reward_id = target_reward["reward_id"]
    cost = target_reward["credit_cost"]

    red_res = client.post(f"/rewards/redeem/{reward_id}", headers=headers)
    assert red_res.status_code == 200
    red_data = red_res.json()
    assert red_data["reward_id"] == reward_id
    assert "redemption_code" in red_data

    # Verify balance deducted
    post_red_bal = client.get("/credits", headers=headers)
    assert post_red_bal.json()["swachh_credits"] == new_balance - cost

    # -------------------------------------------------------------
    # 6. ACCOUNT DELETION & DATA PURGE
    # -------------------------------------------------------------
    del_res = client.delete("/users/me", headers=headers)
    assert del_res.status_code == 200
    assert del_res.json()["success"] is True

    # Verify deleted user cannot log in again
    relogin_res = client.post("/users/login", json={"email": email, "password": password})
    assert relogin_res.status_code == 401

    # Verify token invalidation on protected endpoints
    invalid_profile = client.get("/users/me", headers=headers)
    assert invalid_profile.status_code == 401
