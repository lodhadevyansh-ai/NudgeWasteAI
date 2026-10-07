"""
Unit Tests for NudgeWasteAI Preprocessing and Data Pipeline
===========================================================

Covers:
1. Canonical class mapping and label verification
2. Image validation (valid, missing, empty, corrupt)
3. Image format handling (RGB, RGBA alpha compositing, Grayscale, Palette)
4. Image resizing and dimension guarantees
5. ImageNet normalization and denormalization
6. Safe preprocessing error handling
7. DatasetManifest and NudgeWasteDataset loading
8. Phase 4 Data Pipeline Tests:
   - Split correctness and zero data leakage
   - All 4 canonical classes represented across train/val/test
   - Configurable batch sizes and seed determinism
   - PyTorch DataLoader tensor shapes [B, 3, 224, 224] and label dtypes
   - Smoothed class weight computation
"""

import io
from pathlib import Path
import tempfile
import numpy as np
import pytest
from PIL import Image

from configs.config import (
    CANONICAL_CLASSES,
    CLASS_TO_IDX,
    DEFAULT_IMAGE_SIZE,
    IMAGENET_MEAN,
    IMAGENET_STD,
    NUM_CLASSES,
    DataConfig,
    default_config,
)
from preprocessing.class_mapper import (
    IDX_TO_CLASS,
    is_included,
    map_label,
    map_label_or_raise,
)
from preprocessing.preprocessing import (
    ImagePreprocessor,
    denormalize_image,
    handle_image_format,
    normalize_image,
    resize_image,
    validate_image,
)
from preprocessing.dataset_loader import (
    DatasetManifest,
    DatasetScanner,
    NudgeWasteDataset,
    SampleItem,
    collate_nudge_batch,
    get_dataloaders,
)

# Optional PyTorch support
try:
    import torch
    HAS_TORCH = True
except ImportError:
    HAS_TORCH = False


# =============================================================================
# 1. CANONICAL CLASS MAPPING TESTS
# =============================================================================

def test_canonical_classes_exact():
    """Verify target classes are strictly Wet, Dry, Sanitary, Special Care."""
    assert sorted(CANONICAL_CLASSES) == ["Dry", "Sanitary", "Special Care", "Wet"]
    assert len(CANONICAL_CLASSES) == 4
    for i, c in enumerate(["Wet", "Dry", "Sanitary", "Special Care"]):
        assert CLASS_TO_IDX[c] == i
        assert IDX_TO_CLASS[i] == c


def test_class_mapping_valid_labels():
    """Verify representative valid labels from all datasets map to correct canonical classes."""
    # Wet
    assert map_label("Garbage_Dataset_(GD)", "biological") == "Wet"
    assert map_label("Waste_Classification_Dataset", "O") == "Wet"
    assert map_label("TACO", "Food waste") == "Wet"

    # Dry
    assert map_label("Garbage_Classification", "cardboard") == "Dry"
    assert map_label("Garbage_Classification", "glass") == "Dry"
    assert map_label("Garbage_Classification", "metal") == "Dry"
    assert map_label("Garbage_Classification", "paper") == "Dry"
    assert map_label("Garbage_Classification", "plastic") == "Dry"
    assert map_label("Garbage_Dataset_(GD)", "plastic") == "Dry"
    assert map_label("Waste_Classification_Dataset", "R") == "Dry"
    assert map_label("TACO", "Clear plastic bottle") == "Dry"
    assert map_label("TACO", "Drink can") == "Dry"

    # Sanitary
    assert map_label("Medical_Waste_Dataset", "gauze") == "Sanitary"
    assert map_label("Medical_Waste_Dataset", "medical_cap") == "Sanitary"
    assert map_label("Medical_Waste_Dataset", "shoe_cover_pair") == "Sanitary"
    assert map_label("TACO", "Tissues") == "Sanitary"
    assert map_label("TACO", "Plastic glooves") == "Sanitary"

    # Special Care
    assert map_label("Garbage_Dataset_(GD)", "battery") == "Special Care"
    assert map_label("Medical_Waste_Dataset", "test_tube") == "Special Care"
    assert map_label("Medical_Waste_Dataset", "urine_bag") == "Special Care"
    assert map_label("Medical_Waste_Dataset", "glove_pair_surgery") == "Special Care"
    assert map_label("TACO", "Battery") == "Special Care"
    assert map_label("TACO", "Aerosol") == "Special Care"
    assert map_label("TACO", "Broken glass") == "Special Care"


def test_class_mapping_excluded_labels():
    """Verify ambiguous, noisy, or out-of-scope labels are strictly excluded."""
    # Unsegregated trash
    assert map_label("Garbage_Classification", "trash") is None
    assert is_included("Garbage_Classification", "trash") is False

    assert map_label("Garbage_Dataset_(GD)", "trash") is None
    assert is_included("Garbage_Dataset_(GD)", "trash") is False

    # Out-of-scope wearables
    assert map_label("Garbage_Dataset_(GD)", "clothes") is None
    assert map_label("Garbage_Dataset_(GD)", "shoes") is None
    assert map_label("TACO", "Shoe") is None

    # Ambiguous / non-waste items
    assert map_label("Medical_Waste_Dataset", "medical_glasses") is None
    assert map_label("TACO", "Unlabeled litter") is None
    assert map_label("TACO", "Cigarette") is None
    assert map_label("TACO", "Rope & strings") is None

    # Non-vision tabular
    assert map_label("india_waste_metrics", "__all__") is None


def test_map_label_or_raise():
    """Verify map_label_or_raise raises ValueError on excluded or unknown labels."""
    assert map_label_or_raise("Garbage_Classification", "paper") == "Dry"
    with pytest.raises(ValueError, match="EXCLUDED"):
        map_label_or_raise("Garbage_Classification", "trash")
    with pytest.raises(ValueError, match="not recognized"):
        map_label_or_raise("Garbage_Classification", "unknown_xyz")


# =============================================================================
# 2. IMAGE VALIDATION TESTS
# =============================================================================

def test_validate_valid_pil_image():
    """Verify valid PIL images pass validation."""
    img = Image.new("RGB", (100, 100), color=(128, 64, 32))
    is_valid, err = validate_image(img)
    assert is_valid is True
    assert err is None


def test_validate_valid_file(tmp_path):
    """Verify valid image files on disk pass validation."""
    img_file = tmp_path / "test_valid.jpg"
    img = Image.new("RGB", (64, 64), color="blue")
    img.save(img_file, format="JPEG")

    is_valid, err = validate_image(img_file)
    assert is_valid is True
    assert err is None


def test_validate_missing_file(tmp_path):
    """Verify non-existent files are detected."""
    missing = tmp_path / "does_not_exist.jpg"
    is_valid, err = validate_image(missing)
    assert is_valid is False
    assert err is not None
    assert "does not exist" in err


def test_validate_empty_file(tmp_path):
    """Verify 0-byte files fail validation."""
    empty = tmp_path / "empty.jpg"
    empty.write_bytes(b"")
    is_valid, err = validate_image(empty)
    assert is_valid is False
    assert err is not None
    assert "empty" in err


def test_validate_corrupt_file(tmp_path):
    """Verify files with random garbage bytes fail validation."""
    corrupt = tmp_path / "corrupt.jpg"
    corrupt.write_bytes(b"This is not a valid JPEG header or image stream.")
    is_valid, err = validate_image(corrupt)
    assert is_valid is False
    assert err is not None
    assert "Corrupted" in err or "cannot identify" in err


def test_validate_none_input():
    """Verify None input is safely rejected."""
    is_valid, err = validate_image(None)  # type: ignore[arg-type]
    assert is_valid is False
    assert err is not None
    assert "None" in err


# =============================================================================
# 3. FORMAT HANDLING TESTS
# =============================================================================

def test_handle_rgba_with_alpha_compositing():
    """Verify RGBA images are composited onto white background to 3-channel RGB."""
    img_rgba = Image.new("RGBA", (50, 50), color=(255, 0, 0, 128))
    img_rgb = handle_image_format(img_rgba)
    assert img_rgb.mode == "RGB"
    assert img_rgb.size == (50, 50)
    px = img_rgb.getpixel((25, 25))
    assert isinstance(px, tuple)
    r, g, b = px[:3]
    assert r > 200
    assert g > 100
    assert b > 100


def test_handle_grayscale_to_rgb():
    """Verify 1-channel Grayscale images are converted to 3-channel RGB."""
    img_gray = Image.new("L", (80, 80), color=150)
    img_rgb = handle_image_format(img_gray)
    assert img_rgb.mode == "RGB"
    px = img_rgb.getpixel((40, 40))
    assert isinstance(px, tuple)
    r, g, b = px[:3]
    assert r == 150 and g == 150 and b == 150


def test_handle_palette_to_rgb():
    """Verify Palette mode images convert to RGB."""
    img_p = Image.new("P", (60, 60))
    img_rgb = handle_image_format(img_p)
    assert img_rgb.mode == "RGB"


# =============================================================================
# 4. RESIZING & DIMENSION TESTS
# =============================================================================

def test_resize_direct():
    """Verify direct resize achieves exact target dimensions."""
    img = Image.new("RGB", (512, 384), color="green")
    resized = resize_image(img, target_size=(224, 224), keep_aspect_ratio=False)
    assert resized.size == (224, 224)


def test_resize_letterbox_landscape():
    """Verify aspect-ratio preserving letterboxing on wide landscape image."""
    img = Image.new("RGB", (400, 200), color=(255, 0, 0))
    letterboxed = resize_image(img, target_size=(224, 224), keep_aspect_ratio=True)
    assert letterboxed.size == (224, 224)
    assert letterboxed.getpixel((112, 5)) == (0, 0, 0)
    px_center = letterboxed.getpixel((112, 112))
    assert isinstance(px_center, tuple)
    assert px_center[0] > 200


def test_resize_letterbox_portrait():
    """Verify aspect-ratio preserving letterboxing on tall portrait image."""
    img = Image.new("RGB", (150, 450), color=(0, 255, 0))
    letterboxed = resize_image(img, target_size=(224, 224), keep_aspect_ratio=True)
    assert letterboxed.size == (224, 224)
    assert letterboxed.getpixel((5, 112)) == (0, 0, 0)
    px_center = letterboxed.getpixel((112, 112))
    assert isinstance(px_center, tuple)
    assert px_center[1] > 200


# =============================================================================
# 5. NORMALIZATION TESTS
# =============================================================================

def test_normalize_and_denormalize():
    """Verify ImageNet normalization produces correct float32 range and inverts cleanly."""
    img = Image.new("RGB", (224, 224), color=(100, 150, 200))
    norm_arr = normalize_image(img, return_tensor=False)

    assert norm_arr.shape == (3, 224, 224)
    assert norm_arr.dtype == np.float32

    expected_ch0 = (100.0 / 255.0 - IMAGENET_MEAN[0]) / IMAGENET_STD[0]
    assert np.isclose(norm_arr[0, 50, 50], expected_ch0, atol=1e-3)

    recon_img = denormalize_image(norm_arr)
    assert recon_img.size == (224, 224)
    assert recon_img.mode == "RGB"
    px_recon = recon_img.getpixel((50, 50))
    assert isinstance(px_recon, tuple)
    r, g, b = px_recon[:3]
    assert abs(r - 100) <= 2
    assert abs(g - 150) <= 2
    assert abs(b - 200) <= 2


# =============================================================================
# 6. IMAGE PREPROCESSOR END-TO-END & SAFE HANDLING TESTS
# =============================================================================

def test_preprocessor_end_to_end():
    """Verify ImagePreprocessor correctly executes all pipeline steps."""
    prep = ImagePreprocessor(target_size=(224, 224), return_tensor=False)
    img = Image.new("RGB", (320, 240), color="purple")
    out = prep.preprocess(img)

    assert out.shape == (3, 224, 224)
    assert out.dtype == np.float32


def test_preprocessor_bbox_crop():
    """Verify bounding box cropping in ImagePreprocessor works accurately."""
    prep = ImagePreprocessor(target_size=(100, 100), return_tensor=False)
    img = Image.new("RGB", (300, 300), color=(0, 0, 0))
    for x in range(50, 150):
        for y in range(50, 150):
            img.putpixel((x, y), (255, 0, 0))

    out = prep.preprocess(img, bbox=(50, 50, 100, 100))
    assert out.shape == (3, 100, 100)
    recon = denormalize_image(out)
    px_crop = recon.getpixel((50, 50))
    assert isinstance(px_crop, tuple)
    assert px_crop[0] > 200


def test_preprocessor_safe_on_corrupt():
    """Verify preprocess_safe captures corrupt files gracefully without raising."""
    prep = ImagePreprocessor()
    result, error = prep.preprocess_safe("non_existent_image_path.jpg")
    assert result is None
    assert error is not None
    assert "does not exist" in error


# =============================================================================
# 7. PHASE 4: DATA PIPELINE, SPLITTING & DATALOADER TESTS
# =============================================================================

def test_dataset_manifest_summary():
    """Verify DatasetManifest aggregates counts and distributions accurately."""
    samples = [
        SampleItem("p1.jpg", "ds1", "cardboard", "Dry", 1, split="train"),
        SampleItem("p2.jpg", "ds1", "paper", "Dry", 1, split="val"),
        SampleItem("p3.jpg", "ds2", "biological", "Wet", 0, split="test"),
        SampleItem("p4.jpg", "ds3", "gauze", "Sanitary", 2, split="train"),
        SampleItem("p5.jpg", "ds4", "battery", "Special Care", 3, split="test"),
    ]
    manifest = DatasetManifest(samples)
    assert len(manifest) == 5

    dist = manifest.get_class_distribution()
    assert dist["Dry"] == 2
    assert dist["Wet"] == 1
    assert dist["Sanitary"] == 1
    assert dist["Special Care"] == 1

    split_dist = manifest.get_split_distribution()
    assert split_dist["train"] == 2
    assert split_dist["val"] == 1
    assert split_dist["test"] == 2


def test_dataset_manifest_csv_roundtrip(tmp_path):
    """Verify exporting and reloading a DatasetManifest to CSV preserves all fields."""
    csv_file = tmp_path / "manifest_test.csv"
    samples = [
        SampleItem("img1.jpg", "TACO", "Drink can", "Dry", 1, bbox=(10.0, 20.0, 50.0, 60.0), split="train"),
        SampleItem("img2.jpg", "Medical", "gauze", "Sanitary", 2, split="val"),
    ]
    manifest = DatasetManifest(samples)
    manifest.export_to_csv(csv_file)
    assert csv_file.exists()

    reloaded = DatasetManifest.load_from_csv(csv_file)
    assert len(reloaded) == 2
    assert reloaded.samples[0].image_path == "img1.jpg"
    assert reloaded.samples[0].bbox == (10.0, 20.0, 50.0, 60.0)
    assert reloaded.samples[0].split == "train"
    assert reloaded.samples[1].canonical_class == "Sanitary"
    assert reloaded.samples[1].split == "val"


def test_split_correctness_and_no_leakage():
    """Verify train, val, and test splits are mutually exclusive and leak-free."""
    manifest_path = Path("datasets/processed/manifests/dataset_manifest.csv")
    if not manifest_path.exists():
        manifest_path = Path("Machine_Learning/datasets/processed/manifests/dataset_manifest.csv")
    if not manifest_path.exists():
        pytest.skip("dataset_manifest.csv not found")

    manifest = DatasetManifest.load_from_csv(manifest_path)
    train_samples = manifest.get_samples_by_split("train")
    val_samples = manifest.get_samples_by_split("val")
    test_samples = manifest.get_samples_by_split("test")

    assert len(train_samples) > 0, "Train split is empty"
    assert len(val_samples) > 0, "Val split is empty"
    assert len(test_samples) > 0, "Test split is empty"

    train_paths = set(s.image_path for s in train_samples)
    val_paths = set(s.image_path for s in val_samples)
    test_paths = set(s.image_path for s in test_samples)

    # Zero image path overlap between any splits!
    assert len(train_paths.intersection(val_paths)) == 0, "Data leakage between train and val!"
    assert len(train_paths.intersection(test_paths)) == 0, "Data leakage between train and test!"
    assert len(val_paths.intersection(test_paths)) == 0, "Data leakage between val and test!"


def test_taco_multi_crop_leak_free():
    """Verify that multiple bounding-box crops from the same TACO image never cross splits."""
    manifest_path = Path("datasets/processed/manifests/dataset_manifest.csv")
    if not manifest_path.exists():
        manifest_path = Path("Machine_Learning/datasets/processed/manifests/dataset_manifest.csv")
    if not manifest_path.exists():
        pytest.skip("dataset_manifest.csv not found")

    manifest = DatasetManifest.load_from_csv(manifest_path)
    taco_samples = [s for s in manifest.samples if s.dataset_name == "TACO"]

    # Map each image_path to the set of splits assigned to its crops
    image_to_splits = {}
    for s in taco_samples:
        image_to_splits.setdefault(s.image_path, set()).add(s.split)

    # Every image MUST have exactly one split across all its crops!
    for img_p, splits in image_to_splits.items():
        assert len(splits) == 1, f"Data leakage: Image {img_p} has crops in multiple splits: {splits}"


def test_all_four_classes_present_in_all_splits():
    """Verify that all four canonical classes are represented in train, val, and test splits."""
    manifest_path = Path("datasets/processed/manifests/dataset_manifest.csv")
    if not manifest_path.exists():
        manifest_path = Path("Machine_Learning/datasets/processed/manifests/dataset_manifest.csv")
    if not manifest_path.exists():
        pytest.skip("dataset_manifest.csv not found")

    manifest = DatasetManifest.load_from_csv(manifest_path)
    for split_name in ("train", "val", "test"):
        dist = manifest.get_class_distribution(split=split_name)
        for c in CANONICAL_CLASSES:
            assert dist[c] > 0, f"Class '{c}' has 0 samples in {split_name} split!"


def test_smoothed_class_weights_calculation():
    """Verify that smoothed inverse frequency produces balanced weights without explosion."""
    # Mock imbalanced sample distribution
    # Class 0 (Wet): 10,000; Class 1 (Dry): 20,000; Class 2 (Sanitary): 500; Class 3 (Special Care): 1,500
    mock_samples = []
    counts = [10000, 20000, 500, 1500]
    for c_idx, count in enumerate(counts):
        c_name = IDX_TO_CLASS[c_idx]
        for _ in range(count):
            mock_samples.append(SampleItem("mock.jpg", "ds", c_name, c_name, c_idx))

    ds = NudgeWasteDataset(mock_samples)

    # 1. Without smoothing (smoothing=1.0)
    raw_weights = ds.compute_class_weights(smoothing=1.0)
    # Ratio between Sanitary (500) and Dry (20000) would be 40x
    raw_ratio = raw_weights[2] / raw_weights[1]
    assert np.isclose(raw_ratio, 40.0, atol=0.1)

    # 2. With square-root smoothing (smoothing=0.5)
    smoothed_weights = ds.compute_class_weights(smoothing=0.5)
    # Ratio between Sanitary and Dry is square root of 40 ≈ 6.32x (much safer for gradients!)
    smoothed_ratio = smoothed_weights[2] / smoothed_weights[1]
    assert np.isclose(smoothed_ratio, np.sqrt(40.0), atol=0.2)
    # Weights should be normalized with mean = 1.0
    assert np.isclose(np.mean(smoothed_weights), 1.0, atol=1e-3)
    # Minority classes have higher weights than majority classes
    assert smoothed_weights[2] > smoothed_weights[3] > smoothed_weights[0] > smoothed_weights[1]


def test_collate_nudge_batch():
    """Verify collate_nudge_batch stacks images and labels into correct tensor/array shapes."""
    if HAS_TORCH:
        t1 = torch.zeros((3, 224, 224), dtype=torch.float32)
        t2 = torch.ones((3, 224, 224), dtype=torch.float32)
        batch = [(t1, 0), (t2, 1)]
        res = collate_nudge_batch(batch)
        batch_x, batch_y = res[0], res[1]
        assert isinstance(batch_x, torch.Tensor)
        assert batch_x.shape == (2, 3, 224, 224)
        assert batch_x.dtype == torch.float32
        assert isinstance(batch_y, torch.Tensor)
        assert batch_y.shape == (2,)
        assert batch_y.dtype == torch.int64
    else:
        a1 = np.zeros((3, 224, 224), dtype=np.float32)
        a2 = np.ones((3, 224, 224), dtype=np.float32)
        batch = [(a1, 0), (a2, 1)]
        res = collate_nudge_batch(batch)
        batch_x, batch_y = res[0], res[1]
        assert isinstance(batch_x, np.ndarray)
        assert batch_x.shape == (2, 3, 224, 224)
        assert batch_y.shape == (2,)


def test_get_dataloaders_pipeline(tmp_path):
    """Verify get_dataloaders end-to-end functionality, batch shapes, and types."""
    # Create mock images for testing
    img1 = tmp_path / "mock1.jpg"
    img2 = tmp_path / "mock2.jpg"
    Image.new("RGB", (64, 64), color="red").save(img1)
    Image.new("RGB", (64, 64), color="blue").save(img2)

    # 12 samples (4 train, 4 val, 4 test; 1 of each class per split)
    mock_samples = []
    for split_tag in ("train", "val", "test"):
        for c_idx, c_name in enumerate(CANONICAL_CLASSES):
            mock_samples.append(
                SampleItem(
                    image_path=str(img1 if c_idx % 2 == 0 else img2),
                    dataset_name="mock_ds",
                    original_label=c_name,
                    canonical_class=c_name,
                    canonical_idx=c_idx,
                    split=split_tag,
                )
            )

    cfg = DataConfig(
        batch_size=2,
        num_workers=0,
        seed=123,
        image_size=(224, 224),
    )

    pipeline = get_dataloaders(config=cfg, samples=mock_samples)

    assert "train_loader" in pipeline
    assert "val_loader" in pipeline
    assert "test_loader" in pipeline
    assert "class_weights" in pipeline
    assert len(pipeline["class_weights"]) == 4

    train_ds = pipeline["train_dataset"]
    val_ds = pipeline["val_dataset"]
    test_ds = pipeline["test_dataset"]
    assert len(train_ds) == 4
    assert len(val_ds) == 4
    assert len(test_ds) == 4

    if HAS_TORCH:
        train_loader = pipeline["train_loader"]
        batch_x, batch_y = next(iter(train_loader))
        assert isinstance(batch_x, torch.Tensor)
        assert batch_x.shape == (2, 3, 224, 224)
        assert batch_x.dtype == torch.float32
        assert isinstance(batch_y, torch.Tensor)
        assert batch_y.shape == (2,)
        assert batch_y.dtype == torch.int64
        # Labels are valid class indices [0..3]
        for lbl in batch_y:
            assert 0 <= lbl.item() < NUM_CLASSES
