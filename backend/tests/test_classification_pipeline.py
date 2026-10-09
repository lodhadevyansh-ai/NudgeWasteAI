"""
Comprehensive Classification Pipeline and Taxonomy Acceptance Tests.
Validates:
1. Pure unit tests for the taxonomy resolution and material-to-stream mapping.
2. Model loading and checkpoint verification.
3. Genuine PyTorch inference on REAL representative images (Plastic, Battery, Sanitary/Gauze, Banana/Organic, Cardboard, Metal, Glass).
4. API response format, uncertainty handling, and low-confidence behavior.
"""

from pathlib import Path
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.core.constants import WasteCategory, WasteMaterial
from app.services.taxonomy_service import resolve_taxonomy, match_hint_to_taxonomy, clean_text_hint
from app.services.classification_service import classification_service, MLClassificationModel
from Machine_Learning.inference.predictor import NudgeWastePredictor, get_health

client = TestClient(app)

# Helper to find real image files in datasets
DATASETS_DIR = Path(__file__).resolve().parents[2] / "Machine_Learning" / "datasets"


def _find_real_dataset_image(pattern: str) -> Path:
    """Finds the first existing image file matching pattern in datasets."""
    matches = list(DATASETS_DIR.rglob(pattern))
    for m in matches:
        if m.is_file() and m.suffix.lower() in [".jpg", ".jpeg", ".png"]:
            return m
    raise FileNotFoundError(f"No image matching '{pattern}' found in {DATASETS_DIR}")


# ==============================================================================
# 1. PURE UNIT TESTS: TAXONOMY & KEYWORD MAPPING (ZERO MOCKS, PURE LOGIC)
# ==============================================================================
class TestTaxonomyUnit:
    """Validates material-to-stream taxonomy and item hint resolution."""

    def test_clean_text_hint_rejects_generic_filenames(self):
        assert clean_text_hint("image.jpg") is None
        assert clean_text_hint("IMG_1234.png") is None
        assert clean_text_hint("photo.jpeg") is None
        assert clean_text_hint("upload.webp") is None
        assert clean_text_hint("plastic_bottle.jpg") == "plastic bottle"
        assert clean_text_hint("banana peel") == "banana peel"

    def test_plastic_bottle_maps_to_plastic_and_dry(self):
        tax = resolve_taxonomy(predicted_stream=None, confidence=0.0, item_hint="Plastic Water Bottle")
        assert tax["statutory_category"] == WasteCategory.DRY.value
        assert tax["material_category"] == WasteMaterial.PLASTIC.value
        assert tax["bin_name"] == "Blue Bin"
        assert tax["is_uncertain"] is False

    def test_lithium_battery_maps_to_ewaste_and_special_care(self):
        tax = resolve_taxonomy(predicted_stream=None, confidence=0.0, item_hint="Lithium battery")
        assert tax["statutory_category"] == WasteCategory.SPECIAL_CARE.value
        assert tax["material_category"] == WasteMaterial.E_WASTE_BATTERIES.value
        assert tax["bin_name"] == "Black Bin"
        assert tax["is_uncertain"] is False

    def test_sanitary_pad_maps_to_hygiene_and_sanitary(self):
        tax = resolve_taxonomy(predicted_stream=None, confidence=0.0, item_hint="Sanitary pad")
        assert tax["statutory_category"] == WasteCategory.SANITARY.value
        assert tax["material_category"] == WasteMaterial.SANITARY_HYGIENE.value
        assert tax["bin_name"] == "Red / Sanitary Bin"
        assert tax["is_uncertain"] is False

    def test_banana_peel_maps_to_organic_and_wet(self):
        tax = resolve_taxonomy(predicted_stream=None, confidence=0.0, item_hint="Banana peel")
        assert tax["statutory_category"] == WasteCategory.WET.value
        assert tax["material_category"] == WasteMaterial.WET_ORGANIC.value
        assert tax["bin_name"] == "Green Bin"
        assert tax["is_uncertain"] is False

    def test_paper_cardboard_maps_to_dry_recyclable(self):
        tax = resolve_taxonomy(predicted_stream=None, confidence=0.0, item_hint="Cardboard box")
        assert tax["statutory_category"] == WasteCategory.DRY.value
        assert tax["material_category"] == WasteMaterial.DRY_RECYCLABLE.value
        assert tax["bin_name"] == "Blue Bin"

    def test_metal_can_maps_to_metal_and_dry(self):
        tax = resolve_taxonomy(predicted_stream=None, confidence=0.0, item_hint="Aluminium soda can")
        assert tax["statutory_category"] == WasteCategory.DRY.value
        assert tax["material_category"] == WasteMaterial.METAL.value
        assert tax["bin_name"] == "Blue Bin"

    def test_glass_bottle_maps_to_glass_and_dry(self):
        tax = resolve_taxonomy(predicted_stream=None, confidence=0.0, item_hint="Glass jar bottle")
        assert tax["statutory_category"] == WasteCategory.DRY.value
        assert tax["material_category"] == WasteMaterial.GLASS.value
        assert tax["bin_name"] == "Blue Bin"

    def test_electronic_waste_maps_to_special_care(self):
        tax = resolve_taxonomy(predicted_stream=None, confidence=0.0, item_hint="Old phone e-waste charger")
        assert tax["statutory_category"] == WasteCategory.SPECIAL_CARE.value
        assert tax["material_category"] == WasteMaterial.E_WASTE_BATTERIES.value

    def test_unfamiliar_ambiguous_waste_maps_to_unknown_needs_review(self):
        tax = resolve_taxonomy(predicted_stream=None, confidence=0.40, item_hint="blurry object")
        assert tax["statutory_category"] is None
        assert tax["material_category"] == WasteMaterial.UNKNOWN.value
        assert tax["is_uncertain"] is True
        assert tax["bin_name"] == "Manual Review Bin"

    def test_high_confidence_vision_with_plastic_hint_combines_correctly(self):
        tax = resolve_taxonomy(predicted_stream="Dry", confidence=0.95, item_hint="Plastic bottle")
        assert tax["statutory_category"] == "Dry"
        assert tax["material_category"] == "Plastic"
        assert tax["is_uncertain"] is False


# ==============================================================================
# 2. MODEL LOADING AND HEALTH ENDPOINT VERIFICATION
# ==============================================================================
class TestMLModelLoading:
    """Validates that the PyTorch model checkpoint is loaded into memory."""

    def test_predictor_loads_checkpoint_and_classes(self):
        predictor = NudgeWastePredictor()
        assert predictor.is_loaded is True
        assert predictor.model is not None
        assert predictor.num_classes == 4
        assert set(predictor.canonical_classes) == {"Wet", "Dry", "Sanitary", "Special Care"}

    def test_health_ml_endpoint(self):
        response = client.get("/health/ml")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["model_loaded"] is True
        assert "classes" in data
        assert len(data["classes"]) == 4


# ==============================================================================
# 3. GENUINE INFERENCE ON REAL REPRESENTATIVE IMAGES (NO PREDICTION MOCKS)
# ==============================================================================
class TestRealImageInference:
    """Executes REAL forward-pass inference on representative dataset images."""

    @pytest.fixture(autouse=True)
    def setup_predictor(self):
        self.predictor = NudgeWastePredictor()
        assert self.predictor.is_loaded

    def test_real_plastic_bottle_inference(self):
        img_path = _find_real_dataset_image("*plastic/plastic_1.jpg")
        res = self.predictor.predict(img_path)
        assert res["status"] == "SUCCESS"
        assert res["predicted_class"] == "Dry"
        assert res["confidence"] >= 0.70

    def test_real_lithium_battery_inference(self):
        img_path = _find_real_dataset_image("*battery/battery_1*.jpg")
        res = self.predictor.predict(img_path)
        assert res["status"] in ["SUCCESS", "LOW_CONFIDENCE"]
        assert res["predicted_class"] == "Special Care"
        assert res["confidence"] >= 0.70

    def test_real_banana_organic_inference(self):
        img_path = _find_real_dataset_image("*biological/biological_1.jpg")
        res = self.predictor.predict(img_path)
        assert res["status"] == "SUCCESS"
        assert res["predicted_class"] == "Wet"
        assert res["confidence"] >= 0.70

    def test_real_cardboard_paper_inference(self):
        img_path = _find_real_dataset_image("*cardboard/cardboard_1.jpg")
        res = self.predictor.predict(img_path)
        assert res["status"] == "SUCCESS"
        assert res["predicted_class"] == "Dry"
        assert res["confidence"] >= 0.70

    def test_real_metal_can_inference(self):
        img_path = _find_real_dataset_image("*metal/metal_1.jpg")
        res = self.predictor.predict(img_path)
        assert res["status"] == "SUCCESS"
        assert res["predicted_class"] == "Dry"
        assert res["confidence"] >= 0.70

    def test_real_glass_bottle_inference(self):
        img_path = _find_real_dataset_image("*glass/glass_1.jpg")
        res = self.predictor.predict(img_path)
        assert res["status"] == "SUCCESS"
        assert res["predicted_class"] == "Dry"
        assert res["confidence"] >= 0.70

    def test_real_medical_gauze_inference(self):
        img_path = _find_real_dataset_image("*gauze/*.jpeg")
        res = self.predictor.predict(img_path)
        # Medical gauze in SWM is Sanitary, and clinical items are Special Care.
        assert res["predicted_class"] in ["Sanitary", "Special Care"]


# ==============================================================================
# 4. API RESPONSE FORMAT AND CONFIDENCE/UNKNOWN HANDLING
# ==============================================================================
class TestApiPredictionEndpoints:
    """Validates API contract, status codes, and unknown handling."""

    def test_prediction_text_payload_plastic(self):
        response = client.post("/prediction", json={"item_label": "Plastic Bottle"})
        assert response.status_code == 200
        data = response.json()
        assert data["category"] == "Dry"
        assert data["material_category"] == "Plastic"
        assert data["is_uncertain"] is False
        assert data["disposal_bin"] == "Blue Bin"

    def test_prediction_text_payload_battery(self):
        response = client.post("/prediction", json={"item_label": "Lithium Battery"})
        assert response.status_code == 200
        data = response.json()
        assert data["category"] == "Special Care"
        assert data["material_category"] == "E-waste / Batteries"
        assert data["is_uncertain"] is False
        assert data["disposal_bin"] == "Black Bin"

    def test_prediction_text_payload_sanitary_pad(self):
        response = client.post("/prediction", json={"item_label": "Sanitary pad"})
        assert response.status_code == 200
        data = response.json()
        assert data["category"] == "Sanitary"
        assert data["material_category"] == "Sanitary / Hygiene"
        assert data["is_uncertain"] is False
        assert data["disposal_bin"] == "Red / Sanitary Bin"

    def test_prediction_text_payload_banana_peel(self):
        response = client.post("/prediction", json={"item_label": "Banana peel"})
        assert response.status_code == 200
        data = response.json()
        assert data["category"] == "Wet"
        assert data["material_category"] == "Wet / Organic"
        assert data["is_uncertain"] is False
        assert data["disposal_bin"] == "Green Bin"

    def test_prediction_upload_real_image_and_hint(self):
        img_path = _find_real_dataset_image("*plastic/plastic_1.jpg")
        with open(img_path, "rb") as f:
            files = {"file": ("upload.jpg", f.read(), "image/jpeg")}
        data = {"item_label": "Plastic Beverage Bottle"}
        response = client.post("/prediction/upload", files=files, data=data)
        assert response.status_code == 200
        res = response.json()
        assert res["category"] == "Dry"
        assert res["material_category"] == "Plastic"
        assert res["is_uncertain"] is False

    def test_low_confidence_uncertainty_does_not_default_to_dry(self):
        response = client.post(
            "/prediction",
            json={"item_label": "blurry unknown item", "min_confidence": 0.60},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["is_uncertain"] is True
        # Critical test: category MUST NOT be silently coerced to Dry!
        assert data["category"] is None
        assert data["material_category"] == "Unknown / Needs Review"
        assert "Low confidence" in data["feedback_nudge"]

    def test_upload_corrupt_file_returns_400(self):
        files = {"file": ("corrupt.jpg", b"garbage_data_not_an_image", "image/jpeg")}
        response = client.post("/prediction/upload", files=files)
        assert response.status_code == 400
        assert response.json()["success"] is False

    def test_empty_request_returns_400(self):
        response = client.post("/prediction", json={})
        assert response.status_code == 400
        assert response.json()["success"] is False
