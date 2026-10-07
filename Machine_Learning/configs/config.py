"""
Configuration Module for NudgeWasteAI Machine Learning Pipeline
===============================================================

Defines lean, required configuration parameters for dataset loading,
preprocessing, splitting, DataLoader instantiation, Model Architecture,
and Training Execution.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple


# Root project paths
ML_ROOT = Path(__file__).resolve().parent.parent
DATASETS_DIR = ML_ROOT / "datasets"
PROCESSED_DIR = DATASETS_DIR / "processed"
MANIFEST_PATH = PROCESSED_DIR / "manifests" / "dataset_manifest.csv"
TRAINED_MODELS_DIR = ML_ROOT / "models" / "trained"

# Target canonical classes
CANONICAL_CLASSES: List[str] = ["Wet", "Dry", "Sanitary", "Special Care"]
NUM_CLASSES: int = len(CANONICAL_CLASSES)
CLASS_TO_IDX: Dict[str, int] = {c: i for i, c in enumerate(CANONICAL_CLASSES)}
IDX_TO_CLASS: Dict[int, str] = {i: c for i, c in enumerate(CANONICAL_CLASSES)}

# Image normalization parameters (standard ImageNet statistics)
DEFAULT_IMAGE_SIZE: Tuple[int, int] = (224, 224)
IMAGENET_MEAN: Tuple[float, float, float] = (0.485, 0.456, 0.406)
IMAGENET_STD: Tuple[float, float, float] = (0.229, 0.224, 0.225)


@dataclass
class DataConfig:
    """
    Data pipeline configuration with configurable hyperparameters.
    """
    datasets_root: Path = field(default_factory=lambda: DATASETS_DIR)
    manifest_path: Path = field(default_factory=lambda: MANIFEST_PATH)

    image_size: Tuple[int, int] = DEFAULT_IMAGE_SIZE
    mean: Tuple[float, float, float] = IMAGENET_MEAN
    std: Tuple[float, float, float] = IMAGENET_STD
    keep_aspect_ratio: bool = True

    train_ratio: float = 0.80
    val_ratio: float = 0.10
    test_ratio: float = 0.10
    seed: int = 42

    batch_size: int = 32
    num_workers: int = 0
    pin_memory: bool = False
    drop_last: bool = False

    class_weight_smoothing: float = 0.5
    canonical_classes: List[str] = field(default_factory=lambda: list(CANONICAL_CLASSES))
    num_classes: int = NUM_CLASSES


@dataclass
class ModelConfig:
    """
    Model architecture configuration for NudgeWasteAI four-class classifier.
    """
    architecture: str = "mobilenet_v3_small"
    num_classes: int = NUM_CLASSES
    pretrained: bool = True
    dropout_rate: float = 0.20
    save_dir: Path = field(default_factory=lambda: TRAINED_MODELS_DIR)


@dataclass
class TrainingConfig:
    """
    Hyperparameter and training execution configuration.
    """
    # Training duration and batching
    epochs: int = 4
    batch_size: int = 32
    learning_rate: float = 1e-3
    weight_decay: float = 1e-4

    # Sample balancing for fast, reliable convergence on CPU
    max_samples_per_class: Optional[int] = 350

    # Progressive transfer learning (freeze backbone for initial epochs)
    freeze_backbone_epochs: int = 1

    # Optimization
    optimizer_name: str = "AdamW"
    use_class_weights: bool = True
    early_stopping_patience: int = 3

    # Seed and destination
    seed: int = 42
    save_dir: Path = field(default_factory=lambda: TRAINED_MODELS_DIR)
    model_filename: str = "nudgewaste_mobilenetv3_small_best.pt"
    metrics_filename: str = "training_metrics.json"
    config_filename: str = "training_config.json"


# Default configuration instances
default_data_config = DataConfig()
default_model_config = ModelConfig()
default_training_config = TrainingConfig()

# Backward-compatibility alias
default_config = default_data_config
