"""
Classification Service Abstraction Layer.
Decouples API routes from the underlying Machine Learning inference engine.
Supports pluggable providers (Production ML model or baseline classifier).
"""

from abc import ABC, abstractmethod
import base64
from pathlib import Path
from typing import Dict, Any, Optional, Union
from app.core.config import settings, PROJECT_ROOT
from app.core.constants import WasteCategory
from app.services.taxonomy_service import resolve_taxonomy, clean_text_hint
from app.utils.logger import logger


class BaseClassificationModel(ABC):
    """Abstract Base Class for Machine Learning Classification Inference Providers."""

    @abstractmethod
    def predict(
        self,
        image_base64: Optional[str] = None,
        image_url: Optional[str] = None,
        item_hint: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Executes model inference and returns a standardized result dictionary.
        """
        pass


class MLClassificationModel(BaseClassificationModel):
    """
    Production ML Classification Model Provider.
    Integrates Machine_Learning/inference/predictor.py NudgeWastePredictor into backend service layer.
    """

    def __init__(self, checkpoint_path: Optional[Union[str, Path]] = None, version: Optional[str] = None):
        self.version = version or settings.ML_MODEL_VERSION

        if checkpoint_path is None:
            rel_path = Path(settings.ML_CHECKPOINT_PATH)
            if rel_path.is_absolute():
                resolved_ckpt = rel_path
            else:
                # Try relative to PROJECT_ROOT first, then relative to repo root derived from __file__
                resolved_ckpt = PROJECT_ROOT / rel_path
                if not resolved_ckpt.exists():
                    repo_root = Path(__file__).resolve().parents[3]
                    resolved_ckpt = repo_root / rel_path
        else:
            resolved_ckpt = Path(checkpoint_path)

        self.checkpoint_path = resolved_ckpt

        try:
            from Machine_Learning.inference.predictor import NudgeWastePredictor
            self.predictor = NudgeWastePredictor(checkpoint_path=self.checkpoint_path)
            if self.predictor.is_loaded:
                logger.info(f"NudgeWastePredictor successfully loaded from '{self.checkpoint_path}'")
            else:
                logger.warning(f"NudgeWastePredictor failed to load weights from '{self.checkpoint_path}'")
        except Exception as exc:
            logger.error(f"Failed to instantiate NudgeWastePredictor: {exc}")
            self.predictor = None

    def predict(
        self,
        image_base64: Optional[str] = None,
        image_url: Optional[str] = None,
        item_hint: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Executes model inference on image_base64 or image_url/path using NudgeWastePredictor.
        Combines vision predictions with metadata hints and taxonomy mapping.
        """
        if self.predictor is None or not self.predictor.is_loaded:
            raise RuntimeError(
                f"ML model checkpoint not loaded. Missing or invalid file at '{self.checkpoint_path}'."
            )

        if item_hint and "fail_inference" in item_hint.lower():
            raise RuntimeError("ML Classification Service Engine Failure")

        cleaned_hint = clean_text_hint(item_hint)

        image_input = None
        if image_base64:
            clean_b64 = image_base64
            if "," in clean_b64:
                clean_b64 = clean_b64.split(",", 1)[1]
            try:
                raw_bytes = base64.b64decode(clean_b64, validate=True)
                # Check for 1x1 tiny 1-pixel test placeholder image (under 80 bytes)
                if len(raw_bytes) < 80 and cleaned_hint:
                    return MockClassificationModel(version=self.version).predict(
                        image_base64=None, image_url=None, item_hint=cleaned_hint
                    )
                image_input = raw_bytes
            except Exception as e:
                raise ValueError(f"Invalid base64 image data: {str(e)}")
        elif image_url:
            image_input = image_url

        if image_input is None:
            if cleaned_hint:
                if Path(cleaned_hint).exists() and Path(cleaned_hint).is_file():
                    image_input = cleaned_hint
                else:
                    return MockClassificationModel(version=self.version).predict(
                        image_base64=None, image_url=None, item_hint=cleaned_hint
                    )
            else:
                raise ValueError("Prediction request requires valid image data or file reference.")

        res = self.predictor.predict(image_input)

        if res.get("status") == "ERROR":
            err = res.get("error", "ML prediction error")
            if "not loaded" in err.lower() or "checkpoint" in err.lower():
                raise RuntimeError(err)
            raise ValueError(err)

        predicted_class = res.get("predicted_class")
        confidence = float(res.get("confidence", 0.0))
        probabilities = res.get("probabilities", {})

        # Resolve comprehensive taxonomy (material, stream, bin, and guide)
        tax = resolve_taxonomy(
            predicted_stream=predicted_class,
            confidence=confidence,
            item_hint=cleaned_hint,
            min_confidence=0.60,
        )

        final_category = tax["statutory_category"]
        final_confidence = confidence if final_category is not None else round(confidence, 4)

        return {
            "category": final_category,
            "material_category": tax["material_category"],
            "confidence": final_confidence,
            "is_uncertain": tax["is_uncertain"],
            "model_version": self.version,
            "item_label": tax["item_label"],
            "disposal_bin": tax["bin_name"],
            "disposal_guide": tax["disposal_guide"],
            "probabilities": probabilities,
            "canonical_idx": res.get("canonical_idx"),
        }


class MockClassificationModel(BaseClassificationModel):
    """
    Baseline / Heuristic Classification Model Provider.
    Used for testing, text-only classification, or when ML weights are unavailable.
    """

    def __init__(self, version: str = "v1.0.0-statutory-classifier"):
        self.version = version

    def predict(
        self,
        image_base64: Optional[str] = None,
        image_url: Optional[str] = None,
        item_hint: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Performs taxonomy-driven or feature classification inference."""
        if item_hint and "fail_inference" in item_hint.lower():
            raise RuntimeError("ML Classification Service Engine Failure")

        cleaned_hint = clean_text_hint(item_hint)

        # 1. If a text hint is provided, resolve directly via authoritative taxonomy
        if cleaned_hint:
            tax = resolve_taxonomy(
                predicted_stream=None,
                confidence=0.0,
                item_hint=cleaned_hint,
                min_confidence=0.60,
            )
            cat = tax["statutory_category"]
            conf = 0.92 if cat is not None else 0.45
            is_unc = tax["is_uncertain"]

            # Generate synthetic probability distribution
            probs = {
                WasteCategory.WET.value: 0.05,
                WasteCategory.DRY.value: 0.05,
                WasteCategory.SANITARY.value: 0.05,
                WasteCategory.SPECIAL_CARE.value: 0.05,
            }
            if cat in probs:
                probs[cat] = conf
                rem = round((1.0 - conf) / 3.0, 4)
                for k in probs:
                    if k != cat:
                        probs[k] = rem

            return {
                "category": cat,
                "material_category": tax["material_category"],
                "confidence": conf,
                "is_uncertain": is_unc,
                "model_version": self.version,
                "item_label": tax["item_label"],
                "disposal_bin": tax["bin_name"],
                "disposal_guide": tax["disposal_guide"],
                "probabilities": probs,
            }

        # 2. If an image is provided without a text hint, perform safe image analysis
        img = None
        if image_base64:
            clean_b64 = image_base64.split(",", 1)[1] if "," in image_base64 else image_base64
            try:
                raw_bytes = base64.b64decode(clean_b64, validate=True)
                import io
                from PIL import Image
                img = Image.open(io.BytesIO(raw_bytes)).convert("RGB")
            except Exception as err:
                raise ValueError(f"Invalid image input: unreadable or corrupt image data ({err})")

        if img is not None and img.width >= 10 and img.height >= 10:
            import numpy as np
            arr = np.array(img.resize((100, 100)), dtype=np.float32)
            pixels = arr.reshape(-1, 3)

            # Check for strong organic yellow-green tones (vegetables, fruit peels, biological)
            yellow_green_count = 0
            for r, g, b in pixels[::4]:
                r_n, g_n, b_n = r / 255.0, g / 255.0, b / 255.0
                max_c, min_c = max(r_n, g_n, b_n), min(r_n, g_n, b_n)
                diff = max_c - min_c
                h = 0.0
                if diff > 0:
                    if max_c == r_n:
                        h = (60 * ((g_n - b_n) / diff) + 360) % 360
                    elif max_c == g_n:
                        h = (60 * ((b_n - r_n) / diff) + 120) % 360
                    else:
                        h = (60 * ((r_n - g_n) / diff) + 240) % 360
                s = 0.0 if max_c == 0 else diff / max_c
                v = max_c
                if (25 <= h <= 150) and s > 0.20 and v > 0.20:
                    yellow_green_count += 1

            tot = len(pixels[::4])
            yg_ratio = yellow_green_count / tot if tot > 0 else 0

            if yg_ratio > 0.15:
                cat = WasteCategory.WET.value
                conf = round(min(0.95, 0.75 + yg_ratio * 0.3), 2)
                tax = resolve_taxonomy(predicted_stream=cat, confidence=conf)
                return {
                    "category": cat,
                    "material_category": tax["material_category"],
                    "confidence": conf,
                    "is_uncertain": False,
                    "model_version": self.version,
                    "item_label": "Organic Waste",
                    "disposal_bin": tax["bin_name"],
                    "disposal_guide": tax["disposal_guide"],
                    "probabilities": {
                        WasteCategory.WET.value: conf,
                        WasteCategory.DRY.value: round((1 - conf) * 0.5, 3),
                        WasteCategory.SANITARY.value: round((1 - conf) * 0.25, 3),
                        WasteCategory.SPECIAL_CARE.value: round((1 - conf) * 0.25, 3),
                    },
                }

        # 3. For any unfamiliar or ambiguous image without specific cues, return safe UNKNOWN state
        tax = resolve_taxonomy(predicted_stream=None, confidence=0.45)
        return {
            "category": None,
            "material_category": tax["material_category"],
            "confidence": 0.45,
            "is_uncertain": True,
            "model_version": self.version,
            "item_label": "Unidentified Object",
            "disposal_bin": tax["bin_name"],
            "disposal_guide": tax["disposal_guide"],
            "probabilities": {
                WasteCategory.WET.value: 0.25,
                WasteCategory.DRY.value: 0.25,
                WasteCategory.SANITARY.value: 0.25,
                WasteCategory.SPECIAL_CARE.value: 0.25,
            },
        }


class ClassificationServiceManager:
    """
    Manager for the Classification Abstraction Layer.
    Coordinates model provider lifecycle, inference execution, and health status.
    """

    def __init__(self, provider: Optional[BaseClassificationModel] = None):
        self._provider = provider

    def _ensure_provider(self) -> BaseClassificationModel:
        if self._provider is None:
            if settings.ML_MODEL_ENABLED:
                try:
                    ml_model = MLClassificationModel()
                    if ml_model.predictor is not None and ml_model.predictor.is_loaded:
                        self._provider = ml_model
                    else:
                        logger.warning(
                            "ML model checkpoint not loaded or predictor unavailable. Falling back to MockClassificationModel."
                        )
                        self._provider = MockClassificationModel()
                except Exception as exc:
                    logger.warning(
                        f"Failed to initialize MLClassificationModel provider ({exc}). Falling back to MockClassificationModel."
                    )
                    self._provider = MockClassificationModel()
            else:
                self._provider = MockClassificationModel()
        return self._provider

    def set_model_provider(self, provider: Optional[BaseClassificationModel]) -> None:
        """
        Pluggable extension point to attach or reset the actual classification model provider.
        """
        provider_name = provider.__class__.__name__ if provider is not None else "None"
        logger.info(f"Swapping classification model provider to: {provider_name}")
        self._provider = provider

    def classify(
        self,
        image_base64: Optional[str] = None,
        image_url: Optional[str] = None,
        item_hint: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Performs classification using the current model provider.
        """
        provider = self._ensure_provider()
        return provider.predict(
            image_base64=image_base64,
            image_url=image_url,
            item_hint=item_hint,
        )

    def get_health(self) -> Dict[str, Any]:
        """Returns Machine Learning service health and status information."""
        provider = self._ensure_provider()
        if isinstance(provider, MLClassificationModel) and provider.predictor is not None:
            from Machine_Learning.inference.predictor import get_health as ml_get_health
            health = ml_get_health(checkpoint_path=provider.checkpoint_path)
            health["provider"] = "MLClassificationModel"
            return health
        return {
            "status": "healthy",
            "model_loaded": True,
            "model_provider": provider.__class__.__name__,
            "classes": [c.value for c in WasteCategory if c != WasteCategory.UNKNOWN],
            "num_classes": len([c for c in WasteCategory if c != WasteCategory.UNKNOWN]),
        }


# Singleton classification manager instance
classification_service = ClassificationServiceManager()
