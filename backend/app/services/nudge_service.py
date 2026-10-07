"""
Nudge Engine Business Logic and Rule Generator.
Provides educational, non-punitive behavioural micro-nudges to encourage civic waste segregation.
"""

from datetime import datetime, timezone
import uuid
from typing import Dict, Any, Optional

from app.core.constants import (  # pyrefly: ignore [missing-import]
    WasteCategory,
    NUDGE_SEVERITY_INFO,
    NUDGE_SEVERITY_GUIDANCE,
    NUDGE_SEVERITY_WARNING,
)
from app.schemas.nudge import NudgeRequest, NudgeResponse  # pyrefly: ignore [missing-import]
from app.utils.logger import logger  # pyrefly: ignore [missing-import]

from database.collections.nudges import nudges_collection  # pyrefly: ignore [missing-import]
from database.schemas.nudge_schema import NudgeDocument  # pyrefly: ignore [missing-import]

CONFIDENCE_NUDGE_THRESHOLD = 0.60


class NudgeService:
    """Nudge Engine Service generating deterministic educational guidance rules."""

    def __init__(self):
        self._in_memory_store: Dict[str, Dict[str, Any]] = {}

    def generate_nudge(self, request: NudgeRequest) -> NudgeResponse:
        """
        Generates a deterministic, educational behavioural micro-nudge.

        Args:
            request: Validated NudgeRequest payload.

        Returns:
            NudgeResponse: Structured nudge model for frontend rendering.
        """
        predicted_cat = request.predicted_category.strip()
        confirmed_cat = (request.confirmed_category or predicted_cat).strip()
        confidence = request.confidence if request.confidence is not None else 0.85
        lang = request.language or "en"
        nudge_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc)

        # Rule Engine Logic
        if confidence < CONFIDENCE_NUDGE_THRESHOLD:
            severity = NUDGE_SEVERITY_GUIDANCE
            title = "Unclear Capture - Let's Try Again!"
            message = "We couldn't clearly recognize the waste item category due to low confidence."
            explanation = "Accurate waste segregation relies on clear visual identification to prevent bin contamination."
            action = "Hold your device steady under bright lighting and recapture the item clearly."
            target_cat = predicted_cat

        elif confirmed_cat == predicted_cat:
            severity = NUDGE_SEVERITY_INFO
            title = "Great Segregation Job!"
            message = f"Thank you for placing this item into the {confirmed_cat} stream."
            explanation = "Segregating waste at the household source prevents bin contamination and ensures efficient municipal recycling."
            action = f"Deposit item into the designated {confirmed_cat} Bin."
            target_cat = confirmed_cat

        elif predicted_cat == WasteCategory.WET.value and confirmed_cat == WasteCategory.DRY.value:
            severity = NUDGE_SEVERITY_WARNING
            title = "Keep Recyclables Dry!"
            message = "Wet organic food waste appears to be entering the Dry Recyclables stream."
            explanation = "Food scraps and liquids soil clean paper, cardboard, and plastics, causing entire recycling batches to be rejected."
            action = "Scrape off all food remnants into the Green Wet Waste Bin before putting packaging in the Blue Bin."
            target_cat = WasteCategory.WET.value

        elif predicted_cat == WasteCategory.DRY.value and confirmed_cat == WasteCategory.WET.value:
            severity = NUDGE_SEVERITY_GUIDANCE
            title = "Compost Stream Care"
            message = "Non-compostable dry packaging should be kept out of the Wet Waste Bin."
            explanation = "Plastics and non-biodegradable materials do not decompose in compost pits and degrade organic fertilizer quality."
            action = "Sort non-biodegradable packaging into the Blue Dry Waste Bin."
            target_cat = WasteCategory.DRY.value

        elif predicted_cat == WasteCategory.SANITARY.value or confirmed_cat == WasteCategory.SANITARY.value:
            severity = NUDGE_SEVERITY_WARNING
            title = "Sanitary Waste Handling Alert"
            message = "Sanitary waste must always be placed into the dedicated Red/Sanitary stream."
            explanation = "Mixing sanitary items with recyclables or compost creates biohazard risks for sanitation workers and waste collectors."
            action = "Wrap securely in newspaper or a marked pouch and place in the Red Sanitary Bin."
            target_cat = WasteCategory.SANITARY.value

        elif predicted_cat == WasteCategory.SPECIAL_CARE.value or confirmed_cat == WasteCategory.SPECIAL_CARE.value:
            severity = NUDGE_SEVERITY_WARNING
            title = "Special Care Waste Safety"
            message = "Batteries, electronics, and hazardous chemicals require special disposal."
            explanation = "Heavy metals in e-waste and batteries leach into soil and groundwater if dumped with ordinary household waste."
            action = "Deposit in designated Black Special Care collection points or hand over to e-waste collectors."
            target_cat = WasteCategory.SPECIAL_CARE.value

        else:
            severity = NUDGE_SEVERITY_GUIDANCE
            title = "Statutory Segregation Reminder"
            message = f"Item was predicted as '{predicted_cat}' but selected for '{confirmed_cat}'."
            explanation = "Proper statutory segregation ensures maximum municipal resource recovery and worker safety."
            action = f"Verify stream rules and deposit into the recommended {predicted_cat} Bin."
            target_cat = predicted_cat

        nudge_doc_dict = {
            "_id": nudge_id,
            "nudge_id": nudge_id,
            "waste_category": predicted_cat,
            "target_category": target_cat,
            "title": title,
            "message": message,
            "explanation": explanation,
            "action": action,
            "severity": severity,
            "language": lang,
            "timestamp": now,
            "disposal_id": request.disposal_id,
            "prediction_id": request.prediction_id,
        }

        # Store via database collection wrapper
        try:
            doc = NudgeDocument(**nudge_doc_dict)
            nudges_collection.create_nudge(doc)
        except Exception as exc:
            logger.warning(f"MongoDB nudge insert fallback warning: {exc}")

        # In-memory store fallback
        self._in_memory_store[nudge_id] = nudge_doc_dict
        logger.info(f"Generated nudge {nudge_id}: severity='{severity}', target='{target_cat}'")

        return NudgeResponse(**nudge_doc_dict)

    def get_nudge_by_id(self, nudge_id: str) -> Optional[NudgeResponse]:
        """Retrieves a generated nudge record by ID."""
        try:
            doc = nudges_collection.get_nudge_by_id(nudge_id)
            if doc:
                return NudgeResponse(**doc.to_mongo_dict())
        except Exception as exc:
            logger.warning(f"MongoDB nudge query error: {exc}")

        # In-memory fallback
        doc_dict = self._in_memory_store.get(nudge_id)
        if doc_dict:
            return NudgeResponse(**doc_dict)
        return None


# Singleton instance
nudge_service = NudgeService()
