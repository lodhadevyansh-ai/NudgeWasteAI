"""
Tests for Behavioural Nudge Engine Endpoints and Rule Logic.
"""

from fastapi.testclient import TestClient
from app.main import app
from app.core.constants import (
    WasteCategory,
    NUDGE_SEVERITY_INFO,
    NUDGE_SEVERITY_GUIDANCE,
    NUDGE_SEVERITY_WARNING,
)

client = TestClient(app)


def test_nudge_correct_disposal_info_severity():
    """Test nudge generation for correct disposal yields 'information' severity and encouraging title."""
    payload = {
        "predicted_category": WasteCategory.DRY.value,
        "confirmed_category": WasteCategory.DRY.value,
        "confidence": 0.90,
    }
    response = client.post("/nudges/generate", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["severity"] == NUDGE_SEVERITY_INFO
    assert data["target_category"] == WasteCategory.DRY.value
    assert "Great Segregation" in data["title"]
    assert "Thank you" in data["message"]


def test_nudge_low_confidence_guidance_severity():
    """Test low confidence prediction yields 'guidance' severity and recapture action."""
    payload = {
        "predicted_category": WasteCategory.WET.value,
        "confidence": 0.45,  # < 0.60
    }
    response = client.post("/nudges/generate", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["severity"] == NUDGE_SEVERITY_GUIDANCE
    assert "Unclear Capture" in data["title"]
    assert "recapture" in data["action"].lower()


def test_nudge_wet_in_dry_contamination_warning():
    """Test Wet in Dry contamination yields 'warning' severity and recyclables explanation."""
    payload = {
        "predicted_category": WasteCategory.WET.value,
        "confirmed_category": WasteCategory.DRY.value,
        "confidence": 0.85,
    }
    response = client.post("/nudges/generate", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["severity"] == NUDGE_SEVERITY_WARNING
    assert data["target_category"] == WasteCategory.WET.value
    assert "Keep Recyclables Dry" in data["title"]
    assert "soil clean paper" in data["explanation"]


def test_nudge_dry_in_wet_contamination_guidance():
    """Test Dry in Wet contamination yields 'guidance' severity."""
    payload = {
        "predicted_category": WasteCategory.DRY.value,
        "confirmed_category": WasteCategory.WET.value,
        "confidence": 0.88,
    }
    response = client.post("/nudges/generate", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["severity"] == NUDGE_SEVERITY_GUIDANCE
    assert data["target_category"] == WasteCategory.DRY.value
    assert "Compost Stream Care" in data["title"]


def test_nudge_sanitary_stream_alert_warning():
    """Test Sanitary waste stream mismatch yields 'warning' severity and biohazard explanation."""
    payload = {
        "predicted_category": WasteCategory.SANITARY.value,
        "confirmed_category": WasteCategory.WET.value,
        "confidence": 0.92,
    }
    response = client.post("/nudges/generate", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["severity"] == NUDGE_SEVERITY_WARNING
    assert data["target_category"] == WasteCategory.SANITARY.value
    assert "Sanitary Waste Handling Alert" in data["title"]
    assert "biohazard" in data["explanation"]


def test_nudge_special_care_stream_warning():
    """Test Special Care / E-Waste mismatch yields 'warning' severity and toxic chemical explanation."""
    payload = {
        "predicted_category": WasteCategory.SPECIAL_CARE.value,
        "confirmed_category": WasteCategory.DRY.value,
        "confidence": 0.95,
    }
    response = client.post("/nudges/generate", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["severity"] == NUDGE_SEVERITY_WARNING
    assert data["target_category"] == WasteCategory.SPECIAL_CARE.value
    assert "Special Care Waste Safety" in data["title"]
    assert "heavy metals" in data["explanation"].lower()


def test_get_nudge_by_id():
    """Test retrieving a generated nudge record by ID."""
    gen_res = client.post("/nudges/generate", json={
        "predicted_category": WasteCategory.DRY.value,
        "confidence": 0.89
    })
    assert gen_res.status_code == 200
    nudge_id = gen_res.json()["nudge_id"]

    get_res = client.get(f"/nudges/{nudge_id}")
    assert get_res.status_code == 200
    data = get_res.json()
    assert data["nudge_id"] == nudge_id
    assert data["waste_category"] == WasteCategory.DRY.value
