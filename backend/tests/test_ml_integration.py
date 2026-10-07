"""
Dedicated Runtime Integration Tests for Machine_Learning -> Backend -> Database.
Verifies real PyTorch NudgeWastePredictor execution, input decoding, error handling,
canonical class validation, and API schema outputs.
"""

import io
from PIL import Image
from fastapi.testclient import TestClient
from app.main import app
from app.services.classification_service import (
    classification_service,
    MLClassificationModel,
)
from app.core.constants import WasteCategory

client = TestClient(app)


def _create_valid_test_png_bytes() -> bytes:
    """Helper to generate a valid 224x224 RGB PNG image byte stream."""
    img = Image.new("RGB", (224, 224), color=(100, 150, 200))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def test_ml_integration_valid_image_prediction():
    """1. Valid image input produces successful ML prediction with canonical class and probabilities."""
    png_bytes = _create_valid_test_png_bytes()
    files = {"file": ("test_waste.png", png_bytes, "image/png")}
    response = client.post("/prediction/upload", files=files)
    assert response.status_code == 200
    data = response.json()

    assert "prediction_id" in data
    assert data["category"] in [c.value for c in WasteCategory]
    assert 0.0 <= data["confidence"] <= 1.0
    assert isinstance(data["all_probabilities"], dict)
    for cat in ["Wet", "Dry", "Sanitary", "Special Care"]:
        assert cat in data["all_probabilities"]
        assert 0.0 <= data["all_probabilities"][cat] <= 1.0


def test_ml_integration_corrupt_image_controlled_error():
    """2 & 3. Corrupt or unreadable image input produces a controlled HTTP 400 error."""
    corrupt_bytes = b"NOT_AN_IMAGE_STREAM_BINARY_DATA_CORRUPT"
    files = {"file": ("corrupt.jpg", corrupt_bytes, "image/jpeg")}
    response = client.post("/prediction/upload", files=files)
    assert response.status_code == 400
    data = response.json()
    assert data["success"] is False
    assert data["error"]["code"] == 400
    assert "Invalid image input" in data["error"]["message"]


def test_ml_integration_missing_checkpoint_controlled_error():
    """4. Unloaded model or missing checkpoint produces a controlled HTTP 500 error."""
    unloaded_model = MLClassificationModel(checkpoint_path="non_existent_model_checkpoint.pt")
    original_provider = classification_service._provider
    try:
        classification_service.set_model_provider(unloaded_model)
        png_bytes = _create_valid_test_png_bytes()
        files = {"file": ("valid.png", png_bytes, "image/png")}
        response = client.post("/prediction/upload", files=files)
        assert response.status_code == 500
        data = response.json()
        assert data["success"] is False
        assert data["error"]["code"] == 500
        assert "Classification model execution failed" in data["error"]["message"] or "checkpoint not loaded" in data["error"]["message"]
    finally:
        classification_service.set_model_provider(original_provider)


def test_ml_integration_canonical_classes_validation():
    """5 & 6. Validates exact canonical statutory classes and probability structure."""
    png_bytes = _create_valid_test_png_bytes()
    files = {"file": ("waste_item.png", png_bytes, "image/png")}
    response = client.post("/prediction/upload", files=files)
    assert response.status_code == 200
    data = response.json()

    valid_canonical = {"Wet", "Dry", "Sanitary", "Special Care"}
    if data["category"] is not None:
        assert data["category"] in valid_canonical
    prob_keys = set(data["all_probabilities"].keys())
    assert prob_keys == valid_canonical
    assert abs(sum(data["all_probabilities"].values()) - 1.0) < 1e-3
