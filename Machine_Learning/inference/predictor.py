"""
Production-Style ML Inference Pipeline for NudgeWasteAI
======================================================

Provides a clean, fast, and thread-safe programmatic interface for running
4-class waste classification inference on single images.

Target Output Classes:
----------------------
1. Wet
2. Dry
3. Sanitary
4. Special Care

Features:
---------
- Efficient Single-Load Model Management: Model weights are loaded ONCE into memory
  during instantiation and reused for all subsequent predictions.
- Robust Input Handling: Accepts file paths (str/Path), raw byte buffers, or PIL Images.
- Safe Error Handling: Captures corrupt, missing, or invalid images gracefully without
  crashing or throwing unhandled exceptions.
- Zero Backend / Database Dependencies: Operates purely within Machine_Learning/.
"""

import argparse
import json
import logging
from pathlib import Path
import sys
from typing import Any, Dict, Optional, Union

# Ensure Machine_Learning root is on sys.path
_ml_root = str(Path(__file__).resolve().parent.parent)
if _ml_root not in sys.path:
    sys.path.insert(0, _ml_root)

import numpy as np
from PIL import Image

try:
    import torch
    HAS_TORCH = True
except ImportError:
    HAS_TORCH = False

from configs.config import (
    CANONICAL_CLASSES,
    IDX_TO_CLASS,
    NUM_CLASSES,
    TRAINED_MODELS_DIR,
    DataConfig,
    ModelConfig,
    default_data_config,
    default_model_config,
)
from models.model import NudgeWasteClassifier, build_model
from preprocessing.preprocessing import (
    DEFAULT_IMAGE_SIZE,
    IMAGENET_MEAN,
    IMAGENET_STD,
    ImagePreprocessor,
    validate_image,
)

logger = logging.getLogger(__name__)

# Global singleton predictor instance
_GLOBAL_PREDICTOR_INSTANCE: Optional["NudgeWastePredictor"] = None


class NudgeWastePredictor:
    """
    Production-style inference engine for NudgeWasteAI classification.
    """

    def __init__(
        self,
        checkpoint_path: Optional[Union[str, Path]] = None,
        device: Optional[str] = None,
        preprocessor: Optional[ImagePreprocessor] = None,
    ):
        if not HAS_TORCH:
            raise ImportError("PyTorch is required for NudgeWastePredictor. Please run inside the project environment.")

        # Determine checkpoint path
        if checkpoint_path is None:
            checkpoint_path = TRAINED_MODELS_DIR / "nudgewaste_mobilenetv3_small_best.pt"

        self.checkpoint_path = Path(checkpoint_path).resolve()
        self.device = torch.device(device or ("cuda" if torch.cuda.is_available() else "cpu"))

        # Preprocessor instance
        self.preprocessor = preprocessor or ImagePreprocessor(
            target_size=DEFAULT_IMAGE_SIZE,
            mean=IMAGENET_MEAN,
            std=IMAGENET_STD,
            keep_aspect_ratio=True,
            return_tensor=True,
        )

        self.model: Optional[NudgeWasteClassifier] = None
        self.is_loaded: bool = False
        self.canonical_classes: List[str] = list(CANONICAL_CLASSES)
        self.idx_to_class: Dict[int, str] = dict(IDX_TO_CLASS)
        self.num_classes: int = NUM_CLASSES
        self._load_model()

    def _load_model(self) -> None:
        """Load model weights or compiled TorchScript ONCE into memory."""
        if not self.checkpoint_path.exists():
            logger.error(f"Model checkpoint file not found: {self.checkpoint_path}")
            self.is_loaded = False
            return

        try:
            if str(self.checkpoint_path).endswith(".torchscript.pt"):
                self.model = torch.jit.load(str(self.checkpoint_path), map_location=self.device)
                self.model.eval()
                self.is_loaded = True
                logger.info(f"TorchScript model successfully loaded from '{self.checkpoint_path.name}' onto {self.device}.")
            else:
                checkpoint = torch.load(self.checkpoint_path, map_location=self.device)
                architecture = checkpoint.get("architecture", "mobilenet_v3_small")
                num_classes = checkpoint.get("num_classes", NUM_CLASSES)

                if "canonical_classes" in checkpoint and checkpoint["canonical_classes"]:
                    self.canonical_classes = list(checkpoint["canonical_classes"])
                    self.idx_to_class = {i: c for i, c in enumerate(self.canonical_classes)}
                    self.num_classes = len(self.canonical_classes)

                self.model = build_model(
                    architecture=architecture,
                    num_classes=num_classes,
                    pretrained=False,
                ).to(self.device)

                self.model.load_state_dict(checkpoint["model_state_dict"])
                self.model.eval()
                self.is_loaded = True
                logger.info(f"PyTorch model successfully loaded from '{self.checkpoint_path.name}' onto {self.device}.")
        except Exception as e:
            logger.error(f"Failed to load model checkpoint '{self.checkpoint_path}': {e}")
            self.model = None
            self.is_loaded = False

    def predict(
        self,
        image_input: Union[str, Path, bytes, Image.Image],
    ) -> Dict[str, Any]:
        """
        Run inference on a single waste image.

        Args:
            image_input: File path (str/Path), raw bytes, or PIL Image.

        Returns:
            Dictionary containing:
                - 'status': 'SUCCESS' or 'ERROR'
                - 'predicted_class': Canonical class name ('Wet', 'Dry', 'Sanitary', 'Special Care')
                - 'confidence': Confidence score float [0.0, 1.0]
                - 'canonical_idx': Integer class index [0, 1, 2, 3]
                - 'probabilities': Dict of class names to probability floats
                - 'error': Error description string if status is 'ERROR'
        """
        if not self.is_loaded or self.model is None:
            return {
                "status": "ERROR",
                "predicted_class": None,
                "confidence": 0.0,
                "canonical_idx": None,
                "probabilities": {},
                "error": f"Model is not loaded. Checkpoint missing at '{self.checkpoint_path}'.",
            }

        # Validate image
        is_valid, validation_err = validate_image(image_input)
        if not is_valid:
            return {
                "status": "ERROR",
                "predicted_class": None,
                "confidence": 0.0,
                "canonical_idx": None,
                "probabilities": {},
                "error": f"Invalid image input: {validation_err}",
            }

        # Preprocess image
        try:
            tensor, prep_err = self.preprocessor.preprocess_safe(image_input)
            if tensor is None:
                return {
                    "status": "ERROR",
                    "predicted_class": None,
                    "confidence": 0.0,
                    "canonical_idx": None,
                    "probabilities": {},
                    "error": f"Preprocessing failed: {prep_err}",
                }

            if isinstance(tensor, np.ndarray):
                tensor = torch.from_numpy(tensor)

            # Add batch dimension: (1, 3, 224, 224)
            batch_tensor = tensor.unsqueeze(0).to(self.device)

            # Perform forward pass in evaluation mode with zero tracking overhead
            with torch.inference_mode():
                logits = self.model(batch_tensor)
                probs = torch.softmax(logits, dim=-1)[0]
                conf, pred_idx = torch.max(probs, dim=-1)

            pred_idx_val = int(pred_idx.item())
            confidence_val = float(conf.item())
            predicted_class = self.idx_to_class.get(pred_idx_val, "Unknown")

            prob_dict = {
                self.idx_to_class[i]: float(probs[i].item())
                for i in range(self.num_classes)
            }

            status_str = "SUCCESS" if confidence_val >= 0.60 else "LOW_CONFIDENCE"

            return {
                "status": status_str,
                "canonical_class": predicted_class,
                "predicted_class": predicted_class,
                "confidence": confidence_val,
                "canonical_idx": pred_idx_val,
                "model_version": self.checkpoint_path.stem,
                "probabilities": prob_dict,
                "error": None,
            }

        except Exception as e:
            return {
                "status": "ERROR",
                "canonical_class": None,
                "predicted_class": None,
                "confidence": 0.0,
                "canonical_idx": None,
                "model_version": self.checkpoint_path.stem if self.checkpoint_path else "unknown",
                "probabilities": {},
                "error": f"Inference execution error: {str(e)}",
            }


def get_predictor(checkpoint_path: Optional[Union[str, Path]] = None) -> NudgeWastePredictor:
    """
    Module helper returning a cached singleton NudgeWastePredictor instance.
    Prevents repeated model loading overhead across caller invocations.
    """
    global _GLOBAL_PREDICTOR_INSTANCE
    if _GLOBAL_PREDICTOR_INSTANCE is None or checkpoint_path is not None:
        _GLOBAL_PREDICTOR_INSTANCE = NudgeWastePredictor(checkpoint_path=checkpoint_path)
    return _GLOBAL_PREDICTOR_INSTANCE


def get_health(checkpoint_path: Optional[Union[str, Path]] = None) -> Dict[str, Any]:
    """
    Lightweight health and status mechanism for Machine_Learning module.
    Allows Backend to query ML operational state without exposing internals.
    """
    try:
        predictor = get_predictor(checkpoint_path=checkpoint_path)
        return {
            "status": "healthy" if predictor.is_loaded else "unhealthy",
            "model_loaded": predictor.is_loaded,
            "checkpoint_path": str(predictor.checkpoint_path),
            "model_version": predictor.checkpoint_path.stem if predictor.checkpoint_path else "unknown",
            "classes": CANONICAL_CLASSES,
            "num_classes": NUM_CLASSES,
            "device": str(predictor.device),
        }
    except Exception as exc:
        return {
            "status": "unhealthy",
            "model_loaded": False,
            "error": str(exc),
            "classes": CANONICAL_CLASSES,
            "num_classes": NUM_CLASSES,
        }


def predict_image(image_input: Union[str, Path, bytes, Image.Image]) -> Dict[str, Any]:
    """
    Convenience wrapper for single-line predictions.
    Usage:
        result = predict_image("path/to/waste.jpg")
    """
    predictor = get_predictor()
    return predictor.predict(image_input)


def main() -> None:
    parser = argparse.ArgumentParser(description="NudgeWasteAI Image Inference CLI")
    parser.add_argument("--image", type=str, required=True, help="Path to input waste image")
    parser.add_argument("--checkpoint", type=str, default=None, help="Optional checkpoint path")
    args = parser.parse_args()

    predictor = NudgeWastePredictor(checkpoint_path=args.checkpoint)
    result = predictor.predict(args.image)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
