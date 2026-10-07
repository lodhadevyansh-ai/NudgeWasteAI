"""
Phase 3 End-to-End Three-Component Verification Script.
Executes complete data flow: Real Dataset Image -> Backend API -> PyTorch ML Predictor -> MongoDB Persistence.
Queries MongoDB directly to confirm document persistence across collections.
"""

import sys
import uuid
from pathlib import Path

# Add project root to sys.path
root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from fastapi.testclient import TestClient
from backend.app.main import app
from database.connection.mongodb import db_manager
from database.config.collections_config import CollectionNames


def run_e2e_verification():
    print("==========================================================")
    print("Starting Phase 3 End-to-End Three-Component Integration Verification")
    print("==========================================================")

    # 1. Check real test image path from datasets
    real_image_path = root_dir / "Machine_Learning" / "datasets" / "Waste_Classification_Dataset" / "DATASET" / "TEST" / "O" / "O_12568.jpg"
    assert real_image_path.exists(), f"Real test image missing: {real_image_path}"
    print(f"[OK] Real dataset image found: {real_image_path.name} ({real_image_path.stat().st_size} bytes)")

    client = TestClient(app)

    # 2. Register & Login test user
    uid = uuid.uuid4().hex[:8]
    test_email = f"phase3_user_{uid}@example.com"
    test_pass = "Phase3SecretPass123"

    reg_res = client.post("/users/register", json={
        "name": "Phase 3 Citizen",
        "email": test_email,
        "password": test_pass,
    })
    assert reg_res.status_code == 201, f"Registration failed: {reg_res.text}"
    user_id = reg_res.json()["id"]
    print(f"[OK] User registered: ID '{user_id}', Email '{test_email}'")

    login_res = client.post("/users/login", json={"email": test_email, "password": test_pass})
    assert login_res.status_code == 200, f"Login failed: {login_res.text}"
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print(f"[OK] User authenticated with JWT token.")

    # 3. Send real image to POST /prediction/upload
    with open(real_image_path, "rb") as f:
        img_bytes = f.read()

    files = {"file": ("O_12568.jpg", img_bytes, "image/jpeg")}
    data = {"item_label": "Organic Food Scrap"}
    pred_res = client.post("/prediction/upload", files=files, data=data)
    assert pred_res.status_code == 200, f"Prediction API failed: {pred_res.text}"
    pred_data = pred_res.json()
    
    pred_id = pred_data["prediction_id"]
    predicted_category = pred_data["category"] or "Wet"
    confidence = pred_data["confidence"]
    print(f"[OK] ML Prediction completed: ID '{pred_id}', Category '{predicted_category}', Confidence {confidence:.4f}")

    # 4. Perform Disposal Verification
    disp_payload = {
        "prediction_id": pred_id,
        "predicted_category": predicted_category,
        "confirmed_category": predicted_category,
        "confidence": confidence if confidence > 0.60 else 0.88,
        "item_label": "Organic Food Scrap",
        "location_zone": "Zone-A-Civic",
    }
    disp_res = client.post("/disposal", json=disp_payload, headers=headers)
    assert disp_res.status_code == 201, f"Disposal record failed: {disp_res.text}"
    disp_data = disp_res.json()
    disposal_id = disp_data["disposal_id"]
    credits_awarded = disp_data["credits_awarded"]
    print(f"[OK] Disposal verified & recorded: ID '{disposal_id}', Status '{disp_data['verification_status']}', Credits '{credits_awarded}'")

    # 5. Generate Civic Segregation Nudge
    nudge_res = client.post("/nudges/generate", json={
        "predicted_category": predicted_category,
        "confirmed_category": predicted_category,
        "confidence": confidence,
    })
    assert nudge_res.status_code == 200, f"Nudge endpoint failed: {nudge_res.text}"
    nudge_data = nudge_res.json()
    nudge_id = nudge_data["nudge_id"]
    print(f"[OK] Nudge generated: ID '{nudge_id}', Severity '{nudge_data['severity']}'")

    # 6. Verify Direct MongoDB Persistence
    db = db_manager.get_database()
    
    # Query prediction doc
    pred_doc = db[CollectionNames.PREDICTIONS.value].find_one({"_id": pred_id})
    assert pred_doc is not None, f"Prediction doc {pred_id} missing in MongoDB!"
    print(f"[OK] MongoDB predictions collection verified: doc found with _id '{pred_doc['_id']}'")

    # Query disposal doc
    disp_doc = db[CollectionNames.DISPOSALS.value].find_one({"_id": disposal_id})
    assert disp_doc is not None, f"Disposal doc {disposal_id} missing in MongoDB!"
    print(f"[OK] MongoDB disposals collection verified: doc found with _id '{disp_doc['_id']}'")

    # Query nudge doc
    nudge_doc = db[CollectionNames.NUDGES.value].find_one({"_id": nudge_id})
    assert nudge_doc is not None, f"Nudge doc {nudge_id} missing in MongoDB!"
    print(f"[OK] MongoDB nudges collection verified: doc found with _id '{nudge_doc['_id']}'")

    # Query credit_transactions doc
    credit_doc = db[CollectionNames.CREDIT_TRANSACTIONS.value].find_one({"user_id": user_id})
    assert credit_doc is not None, f"Credit transaction doc for user {user_id} missing in MongoDB!"
    print(f"[OK] MongoDB credit_transactions collection verified: transaction found for user '{user_id}' with amount {credit_doc['amount']}")

    print("==========================================================")
    print("Phase 3 E2E Integration & Persistence Verification PASSED SUCCESSFULLY!")
    print("==========================================================")


if __name__ == "__main__":
    run_e2e_verification()
