"""
Tests for Waste Classification and Prediction API Endpoints.
"""

from fastapi.testclient import TestClient
from app.main import app
from app.services.classification_service import (
    classification_service,
    BaseClassificationModel,
)
from app.core.constants import WasteCategory

client = TestClient(app)


def test_predict_valid_category_high_confidence():
    """Test classification with valid statutory category and high confidence."""
    payload = {
        "item_label": "Plastic Water Bottle",
        "image_base64": "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==",
    }
    response = client.post("/prediction", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "prediction_id" in data
    assert data["category"] == WasteCategory.DRY.value
    assert data["confidence"] >= 0.60
    assert data["is_uncertain"] is False
    assert "model_version" in data
    assert "processing_time_ms" in data
    assert "feedback_nudge" in data
    assert "Place in Blue Bin" in data["feedback_nudge"]


def test_predict_low_confidence_uncertainty():
    """Test classification with low confidence (< threshold) marks prediction uncertain."""
    payload = {
        "item_label": "blurry dark image object",
        "min_confidence": 0.60,
    }
    response = client.post("/prediction", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["is_uncertain"] is True
    # Ensure category is None rather than silently assigning incorrect category
    assert data["category"] is None
    assert "Low confidence classification" in data["feedback_nudge"]


def test_predict_malformed_request():
    """Test malformed prediction request with empty input payload returns 400 Bad Request."""
    payload = {}  # Missing image_base64, image_url, and item_label
    response = client.post("/prediction", json=payload)
    assert response.status_code == 400
    data = response.json()
    assert data["success"] is False
    assert data["error"]["code"] == 400
    assert "must contain at least one input source" in data["error"]["message"]


def test_predict_invalid_category_handled():
    """Test classification service returning an invalid category gets normalized/flagged."""

    class InvalidCategoryModel(BaseClassificationModel):
        def predict(self, image_base64=None, image_url=None, item_hint=None):
            return {
                "category": "Invalid_Custom_Category",
                "confidence": 0.95,
                "model_version": "v_invalid",
                "item_label": "Unknown",
                "probabilities": {},
            }

    original_provider = classification_service._provider
    try:
        classification_service.set_model_provider(InvalidCategoryModel())
        payload = {"item_label": "test item"}
        response = client.post("/prediction", json=payload)
        assert response.status_code == 200
        data = response.json()
        # Invalid category is rejected and marked uncertain
        assert data["is_uncertain"] is True
        assert data["category"] is None
    finally:
        classification_service.set_model_provider(original_provider)


def test_predict_classification_service_failure():
    """Test classification service runtime failure returns clean 500 Internal Server Error."""
    payload = {"item_label": "fail_inference trigger"}
    response = client.post("/prediction", json=payload)
    assert response.status_code == 500
    data = response.json()
    assert data["success"] is False
    assert data["error"]["code"] == 500
    assert "Classification model execution failed" in data["error"]["message"]


def test_predict_upload_file():
    """Test POST /prediction/upload endpoint with binary image upload."""
    import io
    from PIL import Image
    img = Image.new("RGB", (224, 224), color=(120, 180, 240))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    valid_png = buf.getvalue()

    files = {"file": ("test_frame.png", valid_png, "image/png")}
    data = {"item_label": "Organic Banana Peel"}
    response = client.post("/prediction/upload", files=files, data=data)
    assert response.status_code == 200
    res_data = response.json()
    assert res_data["category"] in [c.value for c in WasteCategory]
    assert res_data["is_uncertain"] is False
