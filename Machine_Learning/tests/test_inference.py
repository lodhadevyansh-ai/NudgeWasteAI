"""
Unit Tests for Phase 8: Production-Style ML Inference Pipeline
==============================================================

Tests coverage for NudgeWastePredictor, handling:
- Model loading (valid checkpoint & missing checkpoint)
- Image inputs (PIL Image, file path, raw bytes)
- Invalid / corrupt inputs handling
- Output dictionary schema & probability normalization
- Module helper functions (get_predictor, predict_image)
"""

import io
import os
from pathlib import Path
import sys
import pytest

# Ensure Machine_Learning root is on sys.path
_ml_root = str(Path(__file__).resolve().parent.parent)
if _ml_root not in sys.path:
    sys.path.insert(0, _ml_root)

from PIL import Image

try:
    import torch
    HAS_TORCH = True
except ImportError:
    HAS_TORCH = False

from configs.config import CANONICAL_CLASSES, TRAINED_MODELS_DIR
from inference.predictor import NudgeWastePredictor, get_predictor, predict_image

pytestmark = pytest.mark.skipif(not HAS_TORCH, reason="PyTorch is required for inference tests.")


@pytest.fixture
def dummy_image():
    """Create a temporary 100x100 RGB PIL image."""
    return Image.new("RGB", (100, 100), color=(128, 64, 32))


@pytest.fixture
def dummy_image_bytes(dummy_image):
    """Return raw bytes of a JPEG image."""
    buf = io.BytesIO()
    dummy_image.save(buf, format="JPEG")
    return buf.getvalue()


@pytest.fixture
def dummy_image_file(dummy_image, tmp_path):
    """Save a temporary image file and return Path."""
    file_path = tmp_path / "test_waste.jpg"
    dummy_image.save(file_path, format="JPEG")
    return file_path


@pytest.fixture
def trained_checkpoint():
    """Return path to trained checkpoint if available, or None."""
    ckpt = TRAINED_MODELS_DIR / "nudgewaste_mobilenetv3_small_best.pt"
    if ckpt.exists():
        return ckpt
    return None


def test_predictor_missing_checkpoint(tmp_path):
    """Test predictor behavior when pointing to a non-existent checkpoint path."""
    fake_path = tmp_path / "non_existent_model.pt"
    predictor = NudgeWastePredictor(checkpoint_path=fake_path)
    assert not predictor.is_loaded
    assert predictor.model is None

    res = predictor.predict(Image.new("RGB", (50, 50)))
    assert res["status"] == "ERROR"
    assert "Model is not loaded" in res["error"]


def test_predictor_loaded_prediction(trained_checkpoint, dummy_image):
    """Test predictor with trained checkpoint (or skipped if checkpoint not yet trained)."""
    if trained_checkpoint is None:
        pytest.skip("No trained checkpoint found at models/trained/")

    predictor = NudgeWastePredictor(checkpoint_path=trained_checkpoint)
    assert predictor.is_loaded
    assert predictor.model is not None

    res = predictor.predict(dummy_image)
    assert res["status"] in ["SUCCESS", "LOW_CONFIDENCE"]
    assert res["predicted_class"] in CANONICAL_CLASSES
    assert 0.0 <= res["confidence"] <= 1.0
    assert res["canonical_idx"] in [0, 1, 2, 3]
    assert set(res["probabilities"].keys()) == set(CANONICAL_CLASSES)

    prob_sum = sum(res["probabilities"].values())
    assert pytest.approx(prob_sum, 0.001) == 1.0


def test_predict_image_types(trained_checkpoint, dummy_image, dummy_image_bytes, dummy_image_file):
    """Test prediction across PIL Image, raw bytes, and file path input formats."""
    if trained_checkpoint is None:
        pytest.skip("No trained checkpoint found at models/trained/")

    predictor = NudgeWastePredictor(checkpoint_path=trained_checkpoint)

    # 1. PIL Image
    res_pil = predictor.predict(dummy_image)
    assert res_pil["status"] in ["SUCCESS", "LOW_CONFIDENCE"]

    # 2. Raw Bytes
    res_bytes = predictor.predict(dummy_image_bytes)
    assert res_bytes["status"] in ["SUCCESS", "LOW_CONFIDENCE"]

    # 3. File Path (Path and str)
    res_path = predictor.predict(dummy_image_file)
    assert res_path["status"] in ["SUCCESS", "LOW_CONFIDENCE"]

    res_str = predictor.predict(str(dummy_image_file))
    assert res_str["status"] in ["SUCCESS", "LOW_CONFIDENCE"]


def test_predict_corrupt_inputs(trained_checkpoint):
    """Test error handling for corrupt bytes or non-existent files."""
    if trained_checkpoint is None:
        pytest.skip("No trained checkpoint found at models/trained/")

    predictor = NudgeWastePredictor(checkpoint_path=trained_checkpoint)

    # Corrupt raw bytes
    res_corrupt = predictor.predict(b"this is not image data")
    assert res_corrupt["status"] == "ERROR"
    assert "Invalid image" in res_corrupt["error"] or "Preprocessing failed" in res_corrupt["error"]

    # Non-existent file path
    res_missing = predictor.predict("non_existent_folder/fake_image.jpg")
    assert res_missing["status"] == "ERROR"
    assert "Invalid image" in res_missing["error"]


def test_convenience_wrappers(trained_checkpoint, dummy_image):
    """Test module level singleton get_predictor and predict_image functions."""
    if trained_checkpoint is None:
        pytest.skip("No trained checkpoint found at models/trained/")

    p1 = get_predictor(checkpoint_path=trained_checkpoint)
    p2 = get_predictor()
    assert p1 is p2

    res = predict_image(dummy_image)
    assert res["status"] in ["SUCCESS", "LOW_CONFIDENCE"]
    assert res["predicted_class"] in CANONICAL_CLASSES


def test_torchscript_predictor(dummy_image):
    """Test loading and predicting with exported TorchScript model file."""
    ts_path = TRAINED_MODELS_DIR / "nudgewaste_mobilenetv3_small.torchscript.pt"
    if not ts_path.exists():
        pytest.skip("TorchScript model not found at models/trained/")

    predictor = NudgeWastePredictor(checkpoint_path=ts_path)
    assert predictor.is_loaded

    res = predictor.predict(dummy_image)
    assert res["status"] in ["SUCCESS", "LOW_CONFIDENCE"]
    assert res["predicted_class"] in CANONICAL_CLASSES
    assert 0.0 <= res["confidence"] <= 1.0

