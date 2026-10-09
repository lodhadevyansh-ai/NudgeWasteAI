"""
Prediction Service Business Logic.
Validates input payloads, executes classification via abstraction layer, handles confidence thresholds,
formats normalized prediction responses, and persists prediction events in database.
"""

from datetime import datetime, timezone
import time
import uuid
from typing import Dict, Optional

from app.core.constants import WasteCategory  # pyrefly: ignore [missing-import]
from app.schemas.prediction import PredictionRequest, PredictionResponse  # pyrefly: ignore [missing-import]
from app.services.classification_service import classification_service  # pyrefly: ignore [missing-import]
from app.utils.validators import validate_prediction_input, validate_waste_category  # pyrefly: ignore [missing-import]
from app.utils.logger import logger  # pyrefly: ignore [missing-import]

from database.collections.predictions import predictions_collection  # pyrefly: ignore [missing-import]
from database.schemas.prediction_schema import PredictionDocument  # pyrefly: ignore [missing-import]

DEFAULT_CONFIDENCE_THRESHOLD = 0.60


def get_category_disposal_nudge(category: str) -> str:
    """Returns civic disposal guidance for statutory waste category."""
    nudges = {
        WasteCategory.WET.value: "Place in Green Bin for composting and organic recycling.",
        WasteCategory.DRY.value: "Place in Blue Bin for material recycling (ensure items are clean and dry).",
        WasteCategory.SANITARY.value: "Wrap securely in newspaper/marked pouch and place in Red/Sanitary Bin.",
        WasteCategory.SPECIAL_CARE.value: "Hand over to E-Waste / Hazardous Waste collector or place in Black Bin.",
    }
    return nudges.get(category, "Segregate into statutory waste bins.")


class PredictionService:
    """Main Prediction Service coordinating validation, classification, confidence checks, and response generation."""

    def __init__(self):
        self._in_memory_predictions: Dict[str, PredictionResponse] = {}

    def predict_waste(self, request: PredictionRequest, user_id: Optional[str] = None) -> PredictionResponse:
        """
        Executes waste classification for a request payload.

        Args:
            request: Validated PredictionRequest object.
            user_id: Optional authenticated user ID string.

        Returns:
            PredictionResponse: Formatted response containing category or uncertainty flag.

        Raises:
            ValueError: If input payload contains no image data or text hint.
            RuntimeError: If underlying classification service fails.
        """
        start_time = time.perf_counter()
        logger.info("Received prediction request")

        # 1. Validate input payload
        if not validate_prediction_input(
            image_base64=request.image_base64,
            image_url=request.image_url,
            item_label=request.item_label,
        ):
            logger.warning("Prediction request failed validation: missing image_base64, image_url, or item_label")
            raise ValueError("Prediction request must contain at least one input source: image_base64, image_url, or item_label")

        # 2. Invoke classification abstraction layer
        try:
            raw_result = classification_service.classify(
                image_base64=request.image_base64,
                image_url=request.image_url,
                item_hint=request.item_label,
            )
        except ValueError:
            raise
        except Exception as exc:
            logger.error(f"Classification service failure: {exc}", exc_info=True)
            raise RuntimeError(f"Classification model execution failed: {exc}") from exc

        raw_category = raw_result.get("category")
        confidence = float(raw_result.get("confidence", 0.0))
        model_version = raw_result.get("model_version", "v1.0.0-statutory-classifier")
        recognized_label = raw_result.get("item_label") or request.item_label
        probabilities = raw_result.get("probabilities")
        material_category = raw_result.get("material_category")
        disposal_bin = raw_result.get("disposal_bin")
        disposal_guide = raw_result.get("disposal_guide")
        is_raw_uncertain = raw_result.get("is_uncertain", False)

        # 3. Category Validation & Normalization
        if not validate_waste_category(raw_category):
            logger.warning(f"Classification engine returned non-statutory category '{raw_category}'. Marking prediction uncertain.")
            raw_category = None

        # 4. Confidence Threshold Handling
        min_threshold = request.min_confidence if request.min_confidence is not None else DEFAULT_CONFIDENCE_THRESHOLD

        if raw_category is not None and confidence >= min_threshold and not is_raw_uncertain:
            is_uncertain = False
            final_category = raw_category
            nudge = disposal_guide or get_category_disposal_nudge(final_category)
            logger.info(f"Prediction success: category='{final_category}', material='{material_category}', confidence={confidence:.2f}, model='{model_version}'")
        else:
            is_uncertain = True
            final_category = None
            nudge = (
                f"Low confidence classification ({confidence * 100:.1f}% < threshold {min_threshold * 100:.0f}%). "
                "Please recapture the waste item clearly under good lighting or from a better angle."
            )
            logger.warning(f"Uncertain prediction: candidate='{raw_category}', confidence={confidence:.2f} < threshold={min_threshold}")

        # 5. Elapsed processing time
        elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)
        prediction_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc)

        # 6. Persist prediction document to database collection if database is available
        try:
            pred_doc = PredictionDocument(
                _id=prediction_id,
                prediction_id=prediction_id,
                user_id=user_id,
                category=final_category,
                confidence=round(confidence, 4),
                is_uncertain=is_uncertain,
                timestamp=now,
                model_version=model_version,
                item_label=recognized_label,
                processing_time_ms=elapsed_ms,
                feedback_nudge=nudge,
                all_probabilities=probabilities,
            )
            predictions_collection.create_prediction(pred_doc)
        except Exception as exc:
            logger.warning(f"MongoDB prediction insert warning: {exc}")

        response = PredictionResponse(
            prediction_id=prediction_id,
            category=final_category,
            confidence=round(confidence, 4),
            is_uncertain=is_uncertain,
            timestamp=now,
            model_version=model_version,
            item_label=recognized_label,
            material_category=material_category,
            disposal_bin=disposal_bin,
            disposal_guide=disposal_guide or nudge,
            processing_time_ms=elapsed_ms,
            feedback_nudge=nudge,
            all_probabilities=probabilities,
        )

        self._in_memory_predictions[prediction_id] = response
        return response

    def get_prediction_by_id(self, prediction_id: str) -> Optional[PredictionResponse]:
        """Retrieves prediction record by ID from database collection or memory fallback."""
        try:
            doc = predictions_collection.get_prediction_by_id(prediction_id)
            if doc:
                return PredictionResponse(
                    prediction_id=doc.prediction_id,
                    category=doc.category,
                    confidence=doc.confidence,
                    is_uncertain=doc.is_uncertain,
                    timestamp=doc.timestamp,
                    model_version=doc.model_version,
                    item_label=doc.item_label,
                    processing_time_ms=doc.processing_time_ms,
                    feedback_nudge=doc.feedback_nudge,
                    all_probabilities=doc.all_probabilities,
                )
        except Exception as exc:
            logger.warning(f"MongoDB prediction lookup warning: {exc}")

        return self._in_memory_predictions.get(prediction_id)


# Singleton prediction service instance
prediction_service = PredictionService()
