"""
Real-Image Classification Acceptance Test Battery for NudgeWasteAI
==================================================================

Evaluates actual representative images for all four statutory waste streams:
1. Battery -> Special Care (Index 3)
2. Sanitary Pad / Gauze -> Sanitary (Index 2)
3. Banana / Food Scraps -> Wet (Index 0)
4. Plastic Bottle -> Dry (Index 1)
"""

import os
from pathlib import Path
import pytest
import pandas as pd

try:
    import torch
    HAS_TORCH = True
except ImportError:
    HAS_TORCH = False

try:
    from Machine_Learning.inference.predictor import NudgeWastePredictor, get_predictor
except ImportError:
    from inference.predictor import NudgeWastePredictor, get_predictor

pytestmark = pytest.mark.skipif(not HAS_TORCH, reason="PyTorch is required for real-image acceptance tests.")


@pytest.fixture(scope="module")
def predictor():
    return get_predictor()


@pytest.fixture(scope="module")
def manifest_df():
    manifest_path = Path(__file__).resolve().parent.parent / "datasets" / "processed" / "manifests" / "dataset_manifest.csv"
    assert manifest_path.exists(), f"Dataset manifest not found at {manifest_path}"
    return pd.read_csv(manifest_path)


def test_battery_classification_acceptance(predictor, manifest_df):
    """Test battery image classification yields Special Care (Index 3)."""
    battery_samples = manifest_df[
        (manifest_df["canonical_class"] == "Special Care") & 
        (manifest_df["original_label"].str.lower().str.contains("battery"))
    ]
    assert len(battery_samples) > 0, "No battery samples found in dataset manifest"

    pass_count = 0
    tested = 0
    for _, row in battery_samples.head(10).iterrows():
        img_path = row["image_path"]
        if not os.path.exists(img_path):
            continue
        tested += 1
        res = predictor.predict(img_path)
        assert res["status"] in ["SUCCESS", "LOW_CONFIDENCE"]
        if res["canonical_class"] == "Special Care":
            pass_count += 1

    assert tested > 0, "No readable battery image files found"
    accuracy = pass_count / tested
    assert accuracy >= 0.70, f"Battery accuracy low: {pass_count}/{tested} ({accuracy:.2%})"


def test_sanitary_pad_classification_acceptance(predictor, manifest_df):
    """Test sanitary pad / medical waste classification yields Sanitary or Special Care."""
    sanitary_samples = manifest_df[
        (manifest_df["canonical_class"] == "Sanitary")
    ]
    assert len(sanitary_samples) > 0, "No sanitary samples found in dataset manifest"

    pass_count = 0
    tested = 0
    for _, row in sanitary_samples.head(10).iterrows():
        img_path = row["image_path"]
        if not os.path.exists(img_path):
            continue
        tested += 1
        res = predictor.predict(img_path)
        assert res["status"] in ["SUCCESS", "LOW_CONFIDENCE"]
        if res["canonical_class"] in ["Sanitary", "Special Care"]:
            pass_count += 1

    assert tested > 0, "No readable sanitary pad image files found"
    accuracy = pass_count / tested
    assert accuracy >= 0.40, f"Sanitary pad accuracy low: {pass_count}/{tested} ({accuracy:.2%})"


def test_banana_wet_classification_acceptance(predictor, manifest_df):
    """Test organic food / biological waste yields Wet (Index 0)."""
    wet_samples = manifest_df[
        (manifest_df["canonical_class"] == "Wet") & 
        (manifest_df["original_label"].str.lower().str.contains("biological|food|o"))
    ]
    assert len(wet_samples) > 0, "No wet waste samples found in dataset manifest"

    pass_count = 0
    tested = 0
    for _, row in wet_samples.head(10).iterrows():
        img_path = row["image_path"]
        if not os.path.exists(img_path):
            continue
        tested += 1
        res = predictor.predict(img_path)
        assert res["status"] in ["SUCCESS", "LOW_CONFIDENCE"]
        if res["canonical_class"] == "Wet":
            pass_count += 1

    assert tested > 0, "No readable wet waste image files found"
    accuracy = pass_count / tested
    assert accuracy >= 0.60, f"Wet waste accuracy low: {pass_count}/{tested} ({accuracy:.2%})"


def test_plastic_bottle_dry_classification_acceptance(predictor, manifest_df):
    """Test plastic container / bottle yields Dry (Index 1)."""
    dry_samples = manifest_df[
        (manifest_df["canonical_class"] == "Dry") & 
        (manifest_df["dataset_name"] == "Garbage_Classification")
    ]
    assert len(dry_samples) > 0, "No dry waste samples found in dataset manifest"

    pass_count = 0
    tested = 0
    for _, row in dry_samples.head(10).iterrows():
        img_path = row["image_path"]
        if not os.path.exists(img_path):
            continue
        tested += 1
        res = predictor.predict(img_path)
        assert res["status"] in ["SUCCESS", "LOW_CONFIDENCE"]
        if res["canonical_class"] == "Dry":
            pass_count += 1

    assert tested > 0, "No readable dry waste image files found"
    accuracy = pass_count / tested
    assert accuracy >= 0.70, f"Dry waste accuracy low: {pass_count}/{tested} ({accuracy:.2%})"
