"""
Unified Dataset Loader and Data Pipeline for NudgeWasteAI
=========================================================

This module provides end-to-end dataset discovery, official split preservation,
leak-free group/stratified splitting, and PyTorch DataLoader integration for the
six NudgeWasteAI datasets:
    1. Garbage_Classification (Preserves official train/val/test splits)
    2. Garbage_Dataset_(GD) (Stratified 80/10/10 split)
    3. Medical_Waste_Dataset (Preserves official COCO train/val/test splits, RGB-only)
    4. TACO (Grouped by image to prevent multi-crop data leakage across splits)
    5. Waste_Classification_Dataset (Preserves official TEST split, splits TRAIN)
    6. india_waste_metrics (Handled safely as non-vision tabular)

Key Phase 4 Pipeline Features:
------------------------------
- Official Test Split Preservation: Official benchmark splits are honored.
- Zero Data Leakage: All crops originating from the same physical image/scene
  (e.g. TACO bounding boxes) are strictly partitioned into the same split.
- Class Imbalance Management: Computes smoothed inverse-frequency class weights
  without premature or aggressive oversampling/undersampling.
- Fully Configurable: Batch size, random seed, image dimensions, and worker counts
  are parameterized via configs/config.py.
- Standardized PyTorch Integration: Returns train, val, and test DataLoaders
  with consistent float32 [B, 3, 224, 224] tensor outputs and int64 target labels.
"""

import sys
from pathlib import Path

# Ensure Machine_Learning root is on sys.path
_ml_root = str(Path(__file__).resolve().parent.parent)
if _ml_root not in sys.path:
    sys.path.insert(0, _ml_root)

from dataclasses import dataclass, asdict
import csv
import json
import logging
import os
import random
from typing import Any, Callable, Dict, Iterator, List, Optional, Sequence, Tuple, Union, TYPE_CHECKING

import numpy as np
from PIL import Image

try:
    from configs.config import (  # pyrefly: ignore [missing-import]
        CANONICAL_CLASSES,
        DEFAULT_IMAGE_SIZE,
        IMAGENET_MEAN,
        IMAGENET_STD,
        NUM_CLASSES,
        DataConfig,
        default_config,
    )
    from preprocessing.class_mapper import (  # pyrefly: ignore [missing-import]
        CLASS_TO_IDX,
        IDX_TO_CLASS,
        is_included,
        map_label,
    )
    from preprocessing.preprocessing import (  # pyrefly: ignore [missing-import]
        ImagePreprocessor,
        default_preprocessor,
        validate_image,
    )
except ImportError:
    from ..configs.config import (  # type: ignore
        CANONICAL_CLASSES,
        DEFAULT_IMAGE_SIZE,
        IMAGENET_MEAN,
        IMAGENET_STD,
        NUM_CLASSES,
        DataConfig,
        default_config,
    )
    from .class_mapper import (  # type: ignore
        CLASS_TO_IDX,
        IDX_TO_CLASS,
        is_included,
        map_label,
    )
    from .preprocessing import (  # type: ignore
        ImagePreprocessor,
        default_preprocessor,
        validate_image,
    )

logger = logging.getLogger(__name__)

# Optional PyTorch support
if TYPE_CHECKING:
    import torch
    from torch.utils.data import DataLoader, Dataset as TorchDataset
    HAS_TORCH = True
else:
    try:
        import torch
        from torch.utils.data import DataLoader, Dataset as TorchDataset
        HAS_TORCH = True
    except ImportError:
        HAS_TORCH = False
        TorchDataset = object
        DataLoader = None


@dataclass(frozen=True)
class SampleItem:
    """
    Standard metadata record for a single image/object sample.
    """
    image_path: str
    dataset_name: str
    original_label: str
    canonical_class: str
    canonical_idx: int
    bbox: Optional[Tuple[float, float, float, float]] = None  # (x, y, w, h) for bounding-box crops
    split: Optional[str] = None  # 'train', 'val', 'test'

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        if self.bbox is not None:
            d["bbox"] = list(self.bbox)
        return d

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SampleItem":
        bbox_val = data.get("bbox")
        if bbox_val:
            bbox_val = tuple(bbox_val)
        return cls(
            image_path=data["image_path"],
            dataset_name=data["dataset_name"],
            original_label=data["original_label"],
            canonical_class=data["canonical_class"],
            canonical_idx=int(data["canonical_idx"]),
            bbox=bbox_val,
            split=data.get("split"),
        )


class DatasetScanner:
    """
    Scans, filters, and assigns split tags to samples across all six datasets.
    """

    def __init__(self, datasets_root: Optional[Union[str, Path]] = None):
        if datasets_root is None:
            current_dir = Path(__file__).resolve().parent
            datasets_root = current_dir.parent / "datasets"
        self.root = Path(datasets_root).resolve()

    def scan_garbage_classification(self, preserve_official_splits: bool = True) -> List[SampleItem]:
        """
        Scan Garbage_Classification:
        Preserves official one-indexed-files-notrash_{train,val,test}.txt splits.
        """
        dataset_name = "Garbage_Classification"
        target_dir = self.root / dataset_name / "Garbage classification" / "Garbage classification"
        samples: List[SampleItem] = []

        if not target_dir.exists():
            logger.warning(f"Garbage_Classification directory not found: {target_dir}")
            return samples

        # Load official split mappings if requested
        official_splits: Dict[str, str] = {}
        if preserve_official_splits:
            for s in ("train", "val", "test"):
                split_file = self.root / dataset_name / f"one-indexed-files-notrash_{s}.txt"
                if split_file.exists():
                    with open(split_file, "r", encoding="utf-8") as f:
                        for line in f:
                            parts = line.strip().split()
                            if parts:
                                official_splits[parts[0]] = s

        for class_dir in sorted(target_dir.iterdir()):
            if not class_dir.is_dir():
                continue
            orig_label = class_dir.name
            if not is_included(dataset_name, orig_label):
                continue
            canonical_class = map_label(dataset_name, orig_label)
            if canonical_class is None:
                continue
            canonical_idx = CLASS_TO_IDX[canonical_class]

            for img_file in sorted(class_dir.glob("*.jpg")):
                split_tag = official_splits.get(img_file.name)
                samples.append(
                    SampleItem(
                        image_path=str(img_file.resolve()),
                        dataset_name=dataset_name,
                        original_label=orig_label,
                        canonical_class=canonical_class,
                        canonical_idx=canonical_idx,
                        split=split_tag,
                    )
                )

        return samples

    def scan_garbage_dataset_gd(
        self,
        resolution: str = "standardized_256",
        train_ratio: float = 0.8,
        val_ratio: float = 0.1,
        seed: int = 42,
    ) -> List[SampleItem]:
        """
        Scan Garbage_Dataset_(GD):
        Applies deterministic stratified 80/10/10 splitting per class.
        """
        dataset_name = "Garbage_Dataset_(GD)"
        target_dir = self.root / dataset_name / resolution
        samples: List[SampleItem] = []

        if not target_dir.exists():
            logger.warning(f"Garbage_Dataset_(GD) directory not found: {target_dir}")
            return samples

        rng = random.Random(seed)

        for class_dir in sorted(target_dir.iterdir()):
            if not class_dir.is_dir():
                continue
            orig_label = class_dir.name
            if not is_included(dataset_name, orig_label):
                continue
            canonical_class = map_label(dataset_name, orig_label)
            if canonical_class is None:
                continue
            canonical_idx = CLASS_TO_IDX[canonical_class]

            class_files = [
                f for f in sorted(class_dir.iterdir())
                if f.suffix.lower() in (".jpg", ".jpeg", ".png")
            ]
            shuffled_files = list(class_files)
            rng.shuffle(shuffled_files)

            n = len(shuffled_files)
            n_train = round(n * train_ratio)
            n_val = round(n * val_ratio)

            for i, img_file in enumerate(shuffled_files):
                if i < n_train:
                    split_tag = "train"
                elif i < n_train + n_val:
                    split_tag = "val"
                else:
                    split_tag = "test"

                samples.append(
                    SampleItem(
                        image_path=str(img_file.resolve()),
                        dataset_name=dataset_name,
                        original_label=orig_label,
                        canonical_class=canonical_class,
                        canonical_idx=canonical_idx,
                        split=split_tag,
                    )
                )

        return samples

    def scan_medical_waste(
        self,
        rgb_only: bool = True,
        preserve_official_splits: bool = True,
    ) -> List[SampleItem]:
        """
        Scan Medical_Waste_Dataset:
        Filters out auxiliary stereo grayscale PNG images.
        Preserves official COCO {train, val, test}.json partitions.
        """
        dataset_name = "Medical_Waste_Dataset"
        base_dir = self.root / dataset_name / "Medical Waste dataset"
        images_dir = base_dir / "images"
        coco_dir = base_dir / "annotations" / "coco"
        samples: List[SampleItem] = []

        if not images_dir.exists():
            logger.warning(f"Medical_Waste_Dataset images directory not found: {images_dir}")
            return samples

        official_splits: Dict[str, str] = {}
        if preserve_official_splits and coco_dir.exists():
            for s in ("train", "val", "test"):
                json_file = coco_dir / f"{s}.json"
                if json_file.exists():
                    try:
                        with open(json_file, "r", encoding="utf-8") as f:
                            coco_split = json.load(f)
                            for img_entry in coco_split.get("images", []):
                                fname = Path(img_entry["file_name"]).name
                                official_splits[fname] = s
                    except Exception as e:
                        logger.warning(f"Could not read Medical Waste {s}.json: {e}")

        for class_dir in sorted(images_dir.iterdir()):
            if not class_dir.is_dir():
                continue
            orig_label = class_dir.name
            if not is_included(dataset_name, orig_label):
                continue
            canonical_class = map_label(dataset_name, orig_label)
            if canonical_class is None:
                continue
            canonical_idx = CLASS_TO_IDX[canonical_class]

            for img_file in sorted(class_dir.iterdir()):
                # Exclude stereo grayscale PNGs
                if rgb_only and img_file.suffix.lower() not in (".jpg", ".jpeg"):
                    continue

                split_tag = official_splits.get(img_file.name, "train")
                samples.append(
                    SampleItem(
                        image_path=str(img_file.resolve()),
                        dataset_name=dataset_name,
                        original_label=orig_label,
                        canonical_class=canonical_class,
                        canonical_idx=canonical_idx,
                        split=split_tag,
                    )
                )

        return samples

    def scan_waste_classification(
        self,
        val_from_train_ratio: float = 0.10,
        seed: int = 42,
    ) -> List[SampleItem]:
        """
        Scan Waste_Classification_Dataset:
        Preserves official TEST split 100% intact.
        Partitions official TRAIN into train (90%) and val (10%) using stratified sampling.
        Explicitly skips duplicate DATASET/DATASET/ clone.
        """
        dataset_name = "Waste_Classification_Dataset"
        target_dir = self.root / dataset_name / "DATASET"
        samples: List[SampleItem] = []

        if not target_dir.exists():
            logger.warning(f"Waste_Classification_Dataset directory not found: {target_dir}")
            return samples

        rng = random.Random(seed)

        # 1. TEST split: preserved entirely as 'test'
        test_dir = target_dir / "TEST"
        if test_dir.exists():
            for class_dir in sorted(test_dir.iterdir()):
                if not class_dir.is_dir():
                    continue
                orig_label = class_dir.name
                if not is_included(dataset_name, orig_label):
                    continue
                canonical_class = map_label(dataset_name, orig_label)
                if canonical_class is None:
                    continue
                canonical_idx = CLASS_TO_IDX[canonical_class]

                for img_file in sorted(class_dir.glob("*.jpg")):
                    samples.append(
                        SampleItem(
                            image_path=str(img_file.resolve()),
                            dataset_name=dataset_name,
                            original_label=orig_label,
                            canonical_class=canonical_class,
                            canonical_idx=canonical_idx,
                            split="test",
                        )
                    )

        # 2. TRAIN split: partition into 'train' and 'val'
        train_dir = target_dir / "TRAIN"
        if train_dir.exists():
            for class_dir in sorted(train_dir.iterdir()):
                if not class_dir.is_dir():
                    continue
                orig_label = class_dir.name
                if not is_included(dataset_name, orig_label):
                    continue
                canonical_class = map_label(dataset_name, orig_label)
                if canonical_class is None:
                    continue
                canonical_idx = CLASS_TO_IDX[canonical_class]

                train_files = sorted(class_dir.glob("*.jpg"))
                shuffled_files = list(train_files)
                rng.shuffle(shuffled_files)

                n = len(shuffled_files)
                n_val = round(n * val_from_train_ratio)

                for i, img_file in enumerate(shuffled_files):
                    split_tag = "val" if i < n_val else "train"
                    samples.append(
                        SampleItem(
                            image_path=str(img_file.resolve()),
                            dataset_name=dataset_name,
                            original_label=orig_label,
                            canonical_class=canonical_class,
                            canonical_idx=canonical_idx,
                            split=split_tag,
                        )
                    )

        return samples

    def scan_taco(
        self,
        min_bbox_size: int = 16,
        train_ratio: float = 0.8,
        val_ratio: float = 0.1,
        seed: int = 42,
    ) -> List[SampleItem]:
        """
        Scan TACO dataset:
        Uses GROUPED splitting by image_path: All bounding box crops belonging
        to the same physical image are assigned strictly to the SAME split!
        Guarantees ZERO data leakage between train, val, and test.
        """
        dataset_name = "TACO"
        data_dir = self.root / dataset_name / "TACO" / "data"
        ann_file = data_dir / "annotations.json"
        samples: List[SampleItem] = []

        if not ann_file.exists():
            logger.warning(f"TACO annotations.json not found: {ann_file}")
            return samples

        try:
            with open(ann_file, "r", encoding="utf-8") as f:
                coco_data = json.load(f)
        except Exception as e:
            logger.error(f"Failed to read TACO annotations: {e}")
            return samples

        images_by_id = {img["id"]: img["file_name"] for img in coco_data.get("images", [])}
        categories_by_id = {cat["id"]: cat["name"] for cat in coco_data.get("categories", [])}

        # Deterministic Group Splitting at Image Level
        unique_img_ids = sorted(list(images_by_id.keys()))
        rng = random.Random(seed)
        shuffled_img_ids = list(unique_img_ids)
        rng.shuffle(shuffled_img_ids)

        n_images = len(shuffled_img_ids)
        n_train_imgs = round(n_images * train_ratio)
        n_val_imgs = round(n_images * val_ratio)

        image_split_map: Dict[int, str] = {}
        for i, img_id in enumerate(shuffled_img_ids):
            if i < n_train_imgs:
                image_split_map[img_id] = "train"
            elif i < n_train_imgs + n_val_imgs:
                image_split_map[img_id] = "val"
            else:
                image_split_map[img_id] = "test"

        for ann in coco_data.get("annotations", []):
            img_id = ann.get("image_id")
            cat_id = ann.get("category_id")
            bbox = ann.get("bbox")

            if img_id not in images_by_id or cat_id not in categories_by_id or not bbox:
                continue

            if bbox[2] < min_bbox_size or bbox[3] < min_bbox_size:
                continue

            orig_label = categories_by_id[cat_id]
            if not is_included(dataset_name, orig_label):
                continue
            canonical_class = map_label(dataset_name, orig_label)
            if canonical_class is None:
                continue
            canonical_idx = CLASS_TO_IDX[canonical_class]

            rel_file_name = images_by_id[img_id]
            abs_image_path = (data_dir / rel_file_name).resolve()

            if not abs_image_path.exists():
                continue

            split_tag = image_split_map.get(img_id, "train")

            samples.append(
                SampleItem(
                    image_path=str(abs_image_path),
                    dataset_name=dataset_name,
                    original_label=orig_label,
                    canonical_class=canonical_class,
                    canonical_idx=canonical_idx,
                    bbox=tuple(bbox),
                    split=split_tag,
                )
            )

        return samples

    def scan_india_waste_metrics(self) -> List[SampleItem]:
        logger.info("india_waste_metrics contains tabular records with zero images; skipping image ingestion.")
        return []

    def scan_all(
        self,
        include_datasets: Optional[List[str]] = None,
        max_samples_per_class: Optional[int] = None,
        preserve_official_splits: bool = True,
        seed: int = 42,
    ) -> List[SampleItem]:
        """
        Scan all datasets and compile clean, leak-free, split-tagged samples.
        """
        all_samples: List[SampleItem] = []

        dataset_scanners = [
            ("Garbage_Classification", lambda: self.scan_garbage_classification(preserve_official_splits=preserve_official_splits)),
            ("Garbage_Dataset_(GD)", lambda: self.scan_garbage_dataset_gd(seed=seed)),
            ("Medical_Waste_Dataset", lambda: self.scan_medical_waste(rgb_only=True, preserve_official_splits=preserve_official_splits)),
            ("Waste_Classification_Dataset", lambda: self.scan_waste_classification(seed=seed)),
            ("TACO", lambda: self.scan_taco(seed=seed)),
            ("india_waste_metrics", self.scan_india_waste_metrics),
        ]

        for name, func in dataset_scanners:
            if include_datasets is not None and name not in include_datasets:
                continue
            samples = func()
            all_samples.extend(samples)

        if max_samples_per_class is not None:
            rng = random.Random(seed)
            by_class: Dict[str, List[SampleItem]] = {c: [] for c in CANONICAL_CLASSES}
            for s in all_samples:
                by_class[s.canonical_class].append(s)

            balanced_samples: List[SampleItem] = []
            for c in CANONICAL_CLASSES:
                c_samples = by_class[c]
                if len(c_samples) > max_samples_per_class:
                    rng.shuffle(c_samples)
                    balanced_samples.extend(c_samples[:max_samples_per_class])
                else:
                    balanced_samples.extend(c_samples)
            all_samples = balanced_samples

        return all_samples


class DatasetManifest:
    """
    Manages indexing, summary metrics, and CSV export/import of dataset samples.
    """

    def __init__(self, samples: Optional[List[SampleItem]] = None):
        self.samples = samples if samples is not None else []

    def __len__(self) -> int:
        return len(self.samples)

    def get_class_distribution(self, split: Optional[str] = None) -> Dict[str, int]:
        counts: Dict[str, int] = {c: 0 for c in CANONICAL_CLASSES}
        for s in self.samples:
            if split is None or s.split == split:
                counts[s.canonical_class] = counts.get(s.canonical_class, 0) + 1
        return counts

    def get_split_distribution(self) -> Dict[str, int]:
        counts: Dict[str, int] = {}
        for s in self.samples:
            s_name = s.split or "unassigned"
            counts[s_name] = counts.get(s_name, 0) + 1
        return counts

    def get_dataset_distribution(self, split: Optional[str] = None) -> Dict[str, int]:
        counts: Dict[str, int] = {}
        for s in self.samples:
            if split is None or s.split == split:
                counts[s.dataset_name] = counts.get(s.dataset_name, 0) + 1
        return counts

    def get_samples_by_split(self, split: str) -> List[SampleItem]:
        return [s for s in self.samples if s.split == split]

    def get_summary(self) -> Dict[str, Any]:
        return {
            "total_samples": len(self.samples),
            "split_distribution": self.get_split_distribution(),
            "class_distribution": self.get_class_distribution(),
            "dataset_distribution": self.get_dataset_distribution(),
        }

    def export_to_csv(self, output_path: Union[str, Path]) -> None:
        p = Path(output_path).resolve()
        p.parent.mkdir(parents=True, exist_ok=True)
        fieldnames = [
            "image_path",
            "dataset_name",
            "original_label",
            "canonical_class",
            "canonical_idx",
            "bbox_x",
            "bbox_y",
            "bbox_w",
            "bbox_h",
            "split",
        ]
        with open(p, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for s in self.samples:
                row = {
                    "image_path": s.image_path,
                    "dataset_name": s.dataset_name,
                    "original_label": s.original_label,
                    "canonical_class": s.canonical_class,
                    "canonical_idx": s.canonical_idx,
                    "bbox_x": s.bbox[0] if s.bbox else "",
                    "bbox_y": s.bbox[1] if s.bbox else "",
                    "bbox_w": s.bbox[2] if s.bbox else "",
                    "bbox_h": s.bbox[3] if s.bbox else "",
                    "split": s.split or "",
                }
                writer.writerow(row)

    @classmethod
    def load_from_csv(cls, input_path: Union[str, Path]) -> "DatasetManifest":
        p = Path(input_path).resolve()
        samples: List[SampleItem] = []
        with open(p, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                bbox_val = None
                if row.get("bbox_w") and row.get("bbox_h"):
                    bbox_val = (
                        float(row["bbox_x"]),
                        float(row["bbox_y"]),
                        float(row["bbox_w"]),
                        float(row["bbox_h"]),
                    )
                samples.append(
                    SampleItem(
                        image_path=row["image_path"],
                        dataset_name=row["dataset_name"],
                        original_label=row["original_label"],
                        canonical_class=row["canonical_class"],
                        canonical_idx=int(row["canonical_idx"]),
                        bbox=bbox_val,
                        split=row.get("split") or None,
                    )
                )
        return cls(samples)


class NudgeWasteDataset(TorchDataset):
    """
    PyTorch Dataset providing on-the-fly preprocessing and bounding box extraction.
    """

    def __init__(
        self,
        samples: Sequence[SampleItem],
        preprocessor: Optional[ImagePreprocessor] = None,
        return_metadata: bool = False,
    ):
        self.samples = list(samples)
        self.preprocessor = preprocessor or default_preprocessor
        self.return_metadata = return_metadata

    def __len__(self) -> int:
        return len(self.samples)

    def __getitem__(self, index: int) -> Union[Tuple[Any, int], Tuple[Any, int, Dict[str, Any]]]:
        idx = index
        sample = self.samples[idx]

        image_data, error = self.preprocessor.preprocess_safe(
            image_input=sample.image_path,
            bbox=sample.bbox,
        )

        if image_data is None:
            logger.warning(f"Corrupt or unreadable image at index {idx} ({sample.image_path}): {error}")
            target_h, target_w = self.preprocessor.target_size
            if HAS_TORCH and self.preprocessor.return_tensor:
                image_data = torch.zeros((3, target_h, target_w), dtype=torch.float32)
            else:
                image_data = np.zeros((3, target_h, target_w), dtype=np.float32)

        if self.return_metadata:
            return image_data, sample.canonical_idx, sample.to_dict()

        return image_data, sample.canonical_idx

    def compute_class_weights(self, smoothing: float = 0.5) -> np.ndarray:
        """
        Compute smoothed inverse-frequency class weights for loss functions:
            weight[c] = (total_samples / (num_classes * count[c])) ** smoothing
        """
        counts = np.zeros(len(CANONICAL_CLASSES), dtype=np.float32)
        for s in self.samples:
            counts[s.canonical_idx] += 1.0

        num_classes = len(CANONICAL_CLASSES)
        total = float(len(self.samples))
        weights = np.ones(num_classes, dtype=np.float32)

        for c in range(num_classes):
            if counts[c] > 0:
                raw_w = total / (num_classes * counts[c])
                weights[c] = float(raw_w ** smoothing)

        # Normalize weights so mean is 1.0
        weights = weights / np.mean(weights)
        return weights.astype(np.float32)

    def split(
        self,
        train_ratio: float = 0.8,
        val_ratio: float = 0.1,
        test_ratio: float = 0.1,
        random_seed: int = 42,
    ) -> Tuple["NudgeWasteDataset", "NudgeWasteDataset", "NudgeWasteDataset"]:
        """
        Fallback stratified splitting method if dataset samples do not already have split tags.
        """
        assert abs(train_ratio + val_ratio + test_ratio - 1.0) < 1e-4, "Ratios must sum to 1.0"

        rng = random.Random(random_seed)
        by_class: Dict[int, List[SampleItem]] = {i: [] for i in range(len(CANONICAL_CLASSES))}
        for s in self.samples:
            by_class[s.canonical_idx].append(s)

        train_samples: List[SampleItem] = []
        val_samples: List[SampleItem] = []
        test_samples: List[SampleItem] = []

        for c_idx in sorted(by_class.keys()):
            items = list(by_class[c_idx])
            rng.shuffle(items)
            n = len(items)
            n_train = round(n * train_ratio)
            n_val = round(n * val_ratio)

            train_samples.extend(items[:n_train])
            val_samples.extend(items[n_train : n_train + n_val])
            test_samples.extend(items[n_train + n_val :])

        rng.shuffle(train_samples)
        rng.shuffle(val_samples)
        rng.shuffle(test_samples)

        return (
            NudgeWasteDataset(train_samples, preprocessor=self.preprocessor, return_metadata=self.return_metadata),
            NudgeWasteDataset(val_samples, preprocessor=self.preprocessor, return_metadata=self.return_metadata),
            NudgeWasteDataset(test_samples, preprocessor=self.preprocessor, return_metadata=self.return_metadata),
        )


def collate_nudge_batch(batch: List[Tuple[Any, ...]]) -> Union[Tuple[Any, Any], Tuple[Any, Any, List[Dict]]]:
    """
    Standard collate function for DataLoader batches.
    """
    images = [item[0] for item in batch]
    labels = [item[1] for item in batch]

    if HAS_TORCH and isinstance(images[0], torch.Tensor):
        batch_images = torch.stack(images, dim=0)
        batch_labels = torch.tensor(labels, dtype=torch.int64)
    else:
        batch_images = np.stack(images, axis=0)
        batch_labels = np.array(labels, dtype=np.int64)

    if len(batch[0]) > 2:
        metas = [item[2] for item in batch]
        return batch_images, batch_labels, metas

    return batch_images, batch_labels


def get_dataloaders(
    config: Optional[DataConfig] = None,
    batch_size: Optional[int] = None,
    seed: Optional[int] = None,
    num_workers: Optional[int] = None,
    samples: Optional[List[SampleItem]] = None,
    max_samples_per_class: Optional[int] = None,
    return_metadata: bool = False,
    use_weighted_sampler: bool = True,
) -> Dict[str, Any]:
    """
    Master function to build train, validation, and test DataLoaders.

    Args:
        config: DataConfig configuration object (default: configs.config.default_config).
        batch_size: Optional batch size override.
        seed: Optional random seed override.
        num_workers: Optional worker count override.
        samples: Optional pre-scanned list of SampleItems.
        max_samples_per_class: Optional cap on samples per class to balance dataset.
        return_metadata: If True, batches include sample metadata dictionaries.
        use_weighted_sampler: If True, uses WeightedRandomSampler for class balance.

    Returns:
        Dictionary containing:
            - 'train_loader': DataLoader for training
            - 'val_loader': DataLoader for validation
            - 'test_loader': DataLoader for testing
            - 'train_dataset': NudgeWasteDataset for train
            - 'val_dataset': NudgeWasteDataset for val
            - 'test_dataset': NudgeWasteDataset for test
            - 'class_weights': NumPy array of smoothed inverse-frequency weights
            - 'class_distribution': Split and class sample count summary
    """
    cfg = config or default_config
    eff_batch_size = batch_size if batch_size is not None else cfg.batch_size
    eff_seed = seed if seed is not None else cfg.seed
    eff_workers = num_workers if num_workers is not None else cfg.num_workers

    # 1. Obtain samples
    if samples is None:
        if cfg.manifest_path.exists():
            manifest = DatasetManifest.load_from_csv(cfg.manifest_path)
            all_samples = manifest.samples
        else:
            scanner = DatasetScanner(datasets_root=cfg.datasets_root)
            all_samples = scanner.scan_all(seed=eff_seed)
            manifest = DatasetManifest(all_samples)
            manifest.export_to_csv(cfg.manifest_path)
    else:
        manifest = DatasetManifest(samples)
        all_samples = samples

    # 2. Extract split partitions
    train_samples = manifest.get_samples_by_split("train")
    val_samples = manifest.get_samples_by_split("val")
    test_samples = manifest.get_samples_by_split("test")

    # If samples lack split tags, run deterministic stratified partition
    if not train_samples and not val_samples and not test_samples:
        preprocessor = ImagePreprocessor(
            target_size=cfg.image_size,
            mean=np.array(cfg.mean),
            std=np.array(cfg.std),
            keep_aspect_ratio=cfg.keep_aspect_ratio,
            return_tensor=HAS_TORCH,
        )
        base_ds = NudgeWasteDataset(all_samples, preprocessor=preprocessor)
        train_ds, val_ds, test_ds = base_ds.split(
            train_ratio=cfg.train_ratio,
            val_ratio=cfg.val_ratio,
            test_ratio=cfg.test_ratio,
            random_seed=eff_seed,
        )
    else:
        # Optional sample balancing per class
        if max_samples_per_class is not None:
            rng = random.Random(eff_seed)
            by_class_train: Dict[str, List[SampleItem]] = {c: [] for c in CANONICAL_CLASSES}
            for s in train_samples:
                by_class_train[s.canonical_class].append(s)

            balanced_train: List[SampleItem] = []
            for c in CANONICAL_CLASSES:
                items = list(by_class_train[c])
                if len(items) > max_samples_per_class:
                    rng.shuffle(items)
                    balanced_train.extend(items[:max_samples_per_class])
                else:
                    balanced_train.extend(items)
            train_samples = balanced_train

            val_cap = max(10, round(max_samples_per_class * 0.25))
            by_class_val: Dict[str, List[SampleItem]] = {c: [] for c in CANONICAL_CLASSES}
            for s in val_samples:
                by_class_val[s.canonical_class].append(s)

            balanced_val: List[SampleItem] = []
            for c in CANONICAL_CLASSES:
                items = list(by_class_val[c])
                if len(items) > val_cap:
                    rng.shuffle(items)
                    balanced_val.extend(items[:val_cap])
                else:
                    balanced_val.extend(items)
            val_samples = balanced_val

        preprocessor = ImagePreprocessor(
            target_size=cfg.image_size,
            mean=np.array(cfg.mean),
            std=np.array(cfg.std),
            keep_aspect_ratio=cfg.keep_aspect_ratio,
            return_tensor=HAS_TORCH,
        )
        train_ds = NudgeWasteDataset(train_samples, preprocessor=preprocessor, return_metadata=return_metadata)
        val_ds = NudgeWasteDataset(val_samples, preprocessor=preprocessor, return_metadata=return_metadata)
        test_ds = NudgeWasteDataset(test_samples, preprocessor=preprocessor, return_metadata=return_metadata)

    # 3. Compute smoothed class weights on training set
    class_weights = train_ds.compute_class_weights(smoothing=cfg.class_weight_smoothing)

    # 4. Instantiate PyTorch DataLoaders (or fallback dictionary if PyTorch not available)
    if HAS_TORCH and DataLoader is not None:
        if use_weighted_sampler:
            from torch.utils.data import WeightedRandomSampler
            sample_weights = [float(class_weights[s.canonical_idx]) for s in train_ds.samples]
            sampler = WeightedRandomSampler(
                weights=sample_weights,
                num_samples=len(sample_weights),
                replacement=True,
            )
            train_loader = DataLoader(
                train_ds,
                batch_size=eff_batch_size,
                sampler=sampler,
                num_workers=eff_workers,
                pin_memory=cfg.pin_memory,
                drop_last=cfg.drop_last,
                collate_fn=collate_nudge_batch,
            )
        else:
            train_loader = DataLoader(
                train_ds,
                batch_size=eff_batch_size,
                shuffle=True,
                num_workers=eff_workers,
                pin_memory=cfg.pin_memory,
                drop_last=cfg.drop_last,
                collate_fn=collate_nudge_batch,
            )
        val_loader = DataLoader(
            val_ds,
            batch_size=eff_batch_size,
            shuffle=False,
            num_workers=eff_workers,
            pin_memory=cfg.pin_memory,
            collate_fn=collate_nudge_batch,
        )
        test_loader = DataLoader(
            test_ds,
            batch_size=eff_batch_size,
            shuffle=False,
            num_workers=eff_workers,
            pin_memory=cfg.pin_memory,
            collate_fn=collate_nudge_batch,
        )
    else:
        train_loader = None
        val_loader = None
        test_loader = None

    class_distribution = {
        "train": DatasetManifest(train_ds.samples).get_class_distribution(),
        "val": DatasetManifest(val_ds.samples).get_class_distribution(),
        "test": DatasetManifest(test_ds.samples).get_class_distribution(),
        "total": len(all_samples),
    }

    return {
        "train_loader": train_loader,
        "val_loader": val_loader,
        "test_loader": test_loader,
        "train_dataset": train_ds,
        "val_dataset": val_ds,
        "test_dataset": test_ds,
        "class_weights": class_weights,
        "class_distribution": class_distribution,
    }
