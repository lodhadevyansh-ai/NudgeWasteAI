"""
Comprehensive Real Bin Verification Test Suite for NudgeWasteAI.
Verifies real ML bin verification for the 2-step disposal flow across all statutory waste streams,
wrong-bin rejections, evidence ambiguity, zero-credit protections, and idempotency.
"""

import base64
import io
import uuid
import pytest
from PIL import Image, ImageDraw
from fastapi.testclient import TestClient
from app.main import app
from app.core.constants import WasteCategory

client = TestClient(app)


def get_auth_headers():
    """Helper to register and login a test user, returning JWT bearer headers."""
    uid = uuid.uuid4().hex[:8]
    email = f"bin_verifier_test_{uid}@nudgewaste.ai"
    password = "TestPassword123!"

    reg_res = client.post("/users/register", json={
        "name": "Bin Verification Tester",
        "email": email,
        "password": password
    })
    assert reg_res.status_code == 201

    login_res = client.post("/users/login", json={"email": email, "password": password})
    assert login_res.status_code == 200
    token = login_res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}, reg_res.json()["id"]


def create_synthetic_bin_image_bytes(color_name: str) -> bytes:
    """Creates a PNG image byte payload representing a real bin container of specified color."""
    img = Image.new("RGB", (300, 300), color=(240, 240, 240))
    draw = ImageDraw.Draw(img)

    color_map = {
        "green": ((30, 220, 30), (20, 180, 20)),
        "blue": ((30, 100, 230), (20, 80, 190)),
        "red": ((220, 30, 30), (180, 20, 20)),
        "black": ((40, 40, 45), (25, 25, 30)),
    }
    fill, fill_rim = color_map.get(color_name.lower(), ((30, 220, 30), (20, 180, 20)))

    # Container body & rim contour
    draw.rectangle([50, 50, 250, 250], fill=fill, outline=(50, 50, 50), width=4)
    draw.ellipse([50, 40, 250, 70], fill=fill_rim, outline=(50, 50, 50), width=3)

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


# ==============================================================================
# 1. REAL WRONG-BIN TEST CASE (Sanitary Pad + Green Bin -> REJECTED)
# ==============================================================================
def test_sanitary_waste_with_green_bin_rejected():
    """
    CRITICAL TEST:
    Waste: Sanitary Pad
    ML classification: Sanitary
    Required bin: Red / Sanitary
    Uploaded proof: Green / Wet bin image
    Result: HTTP 400, verification=false, error_code=WRONG_DUSTBIN, 0 credits awarded.
    """
    headers, user_id = get_auth_headers()

    # Step 1: Scan Sanitary Waste item
    pred_res = client.post("/prediction", json={
        "item_label": "Sanitary Pad",
    })
    assert pred_res.status_code == 200
    pred_data = pred_res.json()
    assert pred_data["category"] == WasteCategory.SANITARY.value
    prediction_id = pred_data["prediction_id"]

    # Step 2: Upload Green bin evidence proof (Wrong bin for Sanitary waste)
    green_bin_img_bytes = create_synthetic_bin_image_bytes("green")
    green_bin_b64 = "data:image/png;base64," + base64.b64encode(green_bin_img_bytes).decode("utf-8")

    disp_res = client.post("/disposal", json={
        "prediction_id": prediction_id,
        "confirmation_proof": green_bin_b64,
    }, headers=headers)

    assert disp_res.status_code == 400
    err_data = disp_res.json()
    assert err_data["verified"] is False
    assert err_data["error_code"] == "WRONG_DUSTBIN"
    assert "Red / Sanitary" in err_data["message"] or "Red" in err_data["message"]
    assert err_data["expected_category"] == "Sanitary"
    assert err_data["credits_awarded"] == 0.0

    # Verify user credit balance remains unchanged (500 initial bonus)
    profile_res = client.get("/users/me", headers=headers)
    assert profile_res.json()["swachh_credits"] == 500.0


# ==============================================================================
# 2. SANITARY WASTE + RED BIN -> VERIFIED
# ==============================================================================
def test_sanitary_waste_with_red_bin_verified():
    """
    Waste: Sanitary Pad
    ML classification: Sanitary
    Uploaded proof: Red / Sanitary bin image
    Result: HTTP 201, verified=true, credits_awarded > 0.
    """
    headers, user_id = get_auth_headers()

    # Step 1: Scan Sanitary Waste item
    pred_res = client.post("/prediction", json={
        "item_label": "Sanitary Pad",
    })
    assert pred_res.status_code == 200
    pred_data = pred_res.json()
    prediction_id = pred_data["prediction_id"]

    # Step 2: Upload Red bin evidence proof
    red_bin_img_bytes = create_synthetic_bin_image_bytes("red")
    red_bin_b64 = "data:image/png;base64," + base64.b64encode(red_bin_img_bytes).decode("utf-8")

    disp_res = client.post("/disposal", json={
        "prediction_id": prediction_id,
        "confirmation_proof": red_bin_b64,
    }, headers=headers)

    assert disp_res.status_code == 201
    disp_data = disp_res.json()
    assert disp_data["verified"] is True
    assert disp_data["verification_status"] == "verified"
    assert disp_data["credits_awarded"] == 15.0

    # Verify user credit balance increased (+15.0 => 515.0)
    profile_res = client.get("/users/me", headers=headers)
    assert profile_res.json()["swachh_credits"] == 515.0


# ==============================================================================
# 3. OTHER STATUTORY STREAM MISMATCHES
# ==============================================================================
def test_dry_waste_with_green_bin_rejected():
    """Dry waste + Green bin -> REJECTED."""
    headers, _ = get_auth_headers()
    pred_res = client.post("/prediction", json={"item_label": "Plastic Water Bottle"})
    pred_id = pred_res.json()["prediction_id"]

    green_b64 = "data:image/png;base64," + base64.b64encode(create_synthetic_bin_image_bytes("green")).decode("utf-8")
    disp_res = client.post("/disposal", json={"prediction_id": pred_id, "confirmation_proof": green_b64}, headers=headers)
    assert disp_res.status_code == 400
    assert disp_res.json()["error_code"] == "WRONG_DUSTBIN"


def test_wet_waste_with_blue_bin_rejected():
    """Wet waste + Blue bin -> REJECTED."""
    headers, _ = get_auth_headers()
    pred_res = client.post("/prediction", json={"item_label": "Apple Peel Organic Food"})
    pred_id = pred_res.json()["prediction_id"]

    blue_b64 = "data:image/png;base64," + base64.b64encode(create_synthetic_bin_image_bytes("blue")).decode("utf-8")
    disp_res = client.post("/disposal", json={"prediction_id": pred_id, "confirmation_proof": blue_b64}, headers=headers)
    assert disp_res.status_code == 400
    assert disp_res.json()["error_code"] == "WRONG_DUSTBIN"


def test_special_care_with_green_bin_rejected():
    """Special Care + Green bin -> REJECTED."""
    headers, _ = get_auth_headers()
    pred_res = client.post("/prediction", json={"item_label": "Lithium Battery E-Waste"})
    pred_id = pred_res.json()["prediction_id"]

    green_b64 = "data:image/png;base64," + base64.b64encode(create_synthetic_bin_image_bytes("green")).decode("utf-8")
    disp_res = client.post("/disposal", json={"prediction_id": pred_id, "confirmation_proof": green_b64}, headers=headers)
    assert disp_res.status_code == 400
    assert disp_res.json()["error_code"] == "WRONG_DUSTBIN"


# ==============================================================================
# 4. AMBIGUOUS / FEATURELESS IMAGE TEST
# ==============================================================================
def test_no_bin_visible_image_unclear():
    """Solid dark or featureless canvas -> VERIFICATION_UNCLEAR, 0 credits."""
    headers, _ = get_auth_headers()
    pred_res = client.post("/prediction", json={"item_label": "Plastic Bottle"})
    pred_id = pred_res.json()["prediction_id"]

    # Solid featureless gray canvas
    dark_img = Image.new("RGB", (100, 100), color=(10, 10, 10))
    buf = io.BytesIO()
    dark_img.save(buf, format="PNG")
    dark_b64 = "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode("utf-8")

    disp_res = client.post("/disposal", json={"prediction_id": pred_id, "confirmation_proof": dark_b64}, headers=headers)
    assert disp_res.status_code == 400
    err_data = disp_res.json()
    assert err_data["error_code"] in ["BIN_NOT_CLEAR", "VERIFICATION_UNCLEAR"]
    assert err_data["credits_awarded"] == 0.0


# ==============================================================================
# 5. IDEMPOTENCY / DOUBLE CREDIT PREVENTION
# ==============================================================================
def test_repeated_disposal_verification_idempotency():
    """Submitting the same verified prediction twice awards credits ONLY ONCE."""
    headers, _ = get_auth_headers()
    pred_res = client.post("/prediction", json={"item_label": "Plastic Water Bottle"})
    pred_id = pred_res.json()["prediction_id"]

    blue_b64 = "data:image/png;base64," + base64.b64encode(create_synthetic_bin_image_bytes("blue")).decode("utf-8")

    # First request: awards +10 credits
    res1 = client.post("/disposal", json={"prediction_id": pred_id, "confirmation_proof": blue_b64}, headers=headers)
    assert res1.status_code == 201
    assert res1.json()["credits_awarded"] == 10.0

    # Second request with same prediction_id: should return existing verified record without adding credits
    res2 = client.post("/disposal", json={"prediction_id": pred_id, "confirmation_proof": blue_b64}, headers=headers)
    assert res2.status_code in [200, 201]
    assert res2.json()["prediction_id"] == pred_id

    # Verify balance increased only once (+10 => 510)
    profile_res = client.get("/users/me", headers=headers)
    assert profile_res.json()["swachh_credits"] == 510.0
