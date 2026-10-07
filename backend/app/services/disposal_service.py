"""
Disposal Service and Real ML Bin Verification Engine.
Manages 2-step waste disposal verification, statutory segregation checks, real ML bin verification,
and database event persistence.
"""

from datetime import datetime, timezone
import uuid
from typing import Dict, Any, List, Optional

from app.core.constants import (  # pyrefly: ignore [missing-import]
    DISPOSAL_STATUS_VERIFIED,
    DISPOSAL_STATUS_INCORRECT,
    DISPOSAL_STATUS_UNCERTAIN,
    DISPOSAL_STATUS_REJECTED,
    DISPOSAL_STATUS_UNCLEAR,
    CATEGORY_BIN_MAPPING,
)
from app.schemas.disposal import DisposalCreate, DisposalResponse  # pyrefly: ignore [missing-import]
from app.utils.validators import validate_waste_category  # pyrefly: ignore [missing-import]
from app.utils.logger import logger  # pyrefly: ignore [missing-import]

from database.collections.disposals import disposals_collection  # pyrefly: ignore [missing-import]
from database.schemas.disposal_schema import DisposalDocument  # pyrefly: ignore [missing-import]

# Import Machine_Learning Bin Verifier
import sys
from pathlib import Path
_ml_path = str(Path(__file__).resolve().parent.parent.parent.parent / "Machine_Learning")
if _ml_path not in sys.path:
    sys.path.insert(0, _ml_path)

from inference.bin_verifier import bin_verifier  # pyrefly: ignore [missing-import]


class DisposalVerificationError(Exception):
    """Custom exception for structured disposal verification failures."""
    def __init__(
        self,
        message: str,
        error_code: str,
        expected_category: str,
        expected_bin: str,
        detected_category: Optional[str] = None,
        detected_bin: Optional[str] = None,
        confidence: float = 0.0,
    ):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.expected_category = expected_category
        self.expected_bin = expected_bin
        self.detected_category = detected_category
        self.detected_bin = detected_bin
        self.confidence = confidence


class DisposalService:
    """Service layer for verifying and recording civic waste disposals with real ML bin verification."""

    def __init__(self):
        self._in_memory_store: Dict[str, Dict[str, Any]] = {}

    def verify_and_record_disposal(self, user_id: str, payload: DisposalCreate) -> DisposalResponse:
        """
        Verifies and persists a waste disposal event against stored ML prediction & bin proof.

        Args:
            user_id: ID of the authenticated user performing the disposal.
            payload: Validated DisposalCreate payload.

        Returns:
            DisposalResponse: Record of verified disposal event.

        Raises:
            DisposalVerificationError: If bin verification fails (wrong dustbin or unclear image).
            ValueError: If prediction is missing/uncertain.
        """
        if not payload.prediction_id or not payload.prediction_id.strip():
            raise ValueError("Disposal record requires a valid prediction_id reference")

        # 1. Lookup stored authoritative prediction (Step 1 requirement)
        from app.services.prediction_service import prediction_service
        stored_pred = prediction_service.get_prediction_by_id(payload.prediction_id)

        if stored_pred:
            if stored_pred.is_uncertain or not stored_pred.category:
                raise ValueError("Classification is uncertain. Please recapture the waste item under better lighting.")
            expected_category = stored_pred.category.strip()
            confidence = stored_pred.confidence
        else:
            expected_category = (payload.predicted_category or "").strip()
            confidence = payload.confidence if payload.confidence is not None else 0.85

        if not expected_category or not validate_waste_category(expected_category):
            raise ValueError(f"Invalid statutory waste category '{expected_category}' for prediction '{payload.prediction_id}'")

        # Category mismatch check (Strict 400 rejection for mismatched stream)
        claimed_cat = (payload.confirmed_category or payload.selected_bin_category or expected_category).strip()
        if claimed_cat != expected_category:
            raise ValueError(f"Incorrect waste stream. This item was classified as {expected_category} Waste.")

        # Low confidence rejection check
        if confidence < 0.60:
            raise ValueError(f"Disposal rejected due to low classification confidence ({confidence * 100:.1f}%). Please re-scan item.")

        bin_info = CATEGORY_BIN_MAPPING.get(expected_category, {"color": "green", "name": "Green Bin", "category": expected_category})
        expected_bin_name = bin_info["name"]
        expected_bin_color = bin_info["color"]

        # 2. Check Idempotency / Prevent Double Credit (Step 10 requirement)
        existing_doc = disposals_collection.get_disposal_by_prediction_id(payload.prediction_id, user_id=user_id)
        if not existing_doc:
            # Check in-memory store
            for record in self._in_memory_store.values():
                if record.get("prediction_id") == payload.prediction_id and record.get("user_id") == user_id:
                    if record.get("verification_status") == DISPOSAL_STATUS_VERIFIED:
                        logger.info(f"Idempotent disposal request for prediction '{payload.prediction_id}'. Returning existing record.")
                        return DisposalResponse(**record)

        if existing_doc and existing_doc.verification_status == DISPOSAL_STATUS_VERIFIED:
            logger.info(f"Idempotent disposal request for prediction '{payload.prediction_id}'. Returning existing DB record.")
            return DisposalResponse(**existing_doc.to_mongo_dict())

        # 3. Real ML Bin Verification (Step 2, 4, 5, 6, 7 requirement)
        import hashlib
        proof_payload = payload.confirmation_proof or f"disposal_proof_{expected_category.lower()}"

        proof_hash = hashlib.sha256(proof_payload.encode('utf-8')).hexdigest()
        logger.info(
            f"DIAGNOSTIC VERIFICATION LOG | prediction_id='{payload.prediction_id}' | "
            f"required_category='{expected_category}' | required_bin='{expected_bin_name}' | "
            f"proof_hash='{proof_hash[:16]}...' | proof_len={len(proof_payload)}"
        )

        ver_result = bin_verifier.verify(proof_payload, expected_category=expected_category)

        logger.info(
            f"DIAGNOSTIC VERIFICATION RESULT | prediction_id='{payload.prediction_id}' | "
            f"status='{ver_result.get('verification', {}).get('status')}' | "
            f"required_bin='{expected_bin_name}' | detected_bin='{ver_result.get('verification', {}).get('detected_bin')}' | "
            f"confidence={ver_result.get('confidence')} | method='BinVerificationEngine' | "
            f"reason='{ver_result.get('message')}'"
        )

        disposal_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc)

        detected_color = ver_result.get("detected_bin_color")
        detected_category = ver_result.get("detected_category")
        ver_confidence = ver_result.get("confidence", 0.0)
        error_code = ver_result.get("error_code")
        ver_message = ver_result.get("message") or ""

        detected_bin_name = CATEGORY_BIN_MAPPING.get(detected_category, {}).get("name", f"{detected_color.title() if detected_color else 'Unknown'} Bin")

        # 4. Handle Rejected / Unclear Bin Verification (Step 7 & Step 8)
        if not ver_result.get("verified"):
            ver_status = DISPOSAL_STATUS_REJECTED if error_code == "WRONG_DUSTBIN" else DISPOSAL_STATUS_UNCLEAR
            rejected_doc_dict = {
                "_id": disposal_id,
                "disposal_id": disposal_id,
                "user_id": user_id,
                "prediction_id": payload.prediction_id,
                "predicted_category": expected_category,
                "confirmed_category": expected_category,
                "confidence": confidence,
                "verification_status": ver_status,
                "is_correctly_segregated": False,
                "feedback_nudge": ver_message,
                "item_label": payload.item_label or (stored_pred.item_label if stored_pred else "Scanned Item"),
                "location_zone": payload.location_zone,
                "device_metadata": payload.device_metadata,
                "timestamp": now,
                "credits_awarded": 0.0,
                "expected_category": expected_category,
                "expected_bin": expected_bin_name,
                "detected_bin": detected_bin_name if ver_result.get("bin_detected") else None,
                "detected_category": detected_category if ver_result.get("bin_detected") else None,
                "verification_confidence": ver_confidence,
                "evidence_type": ver_result.get("evidence_type", "image"),
                "rejection_reason": error_code,
            }

            # Save rejected record to MongoDB for audit
            try:
                doc = DisposalDocument(
                    disposal_id=disposal_id,
                    user_id=user_id,
                    prediction_id=payload.prediction_id,
                    predicted_category=expected_category,
                    confirmed_category=expected_category,
                    confidence=confidence,
                    verification_status=ver_status,
                    is_correctly_segregated=False,
                    feedback_nudge=ver_message,
                    item_label=payload.item_label or (stored_pred.item_label if stored_pred else "Scanned Item"),
                    location_zone=payload.location_zone,
                    device_metadata=payload.device_metadata,
                    timestamp=now,
                    credits_awarded=0.0,
                    expected_category=expected_category,
                    expected_bin=expected_bin_name,
                    detected_bin=detected_bin_name if ver_result.get("bin_detected") else None,
                    detected_category=detected_category if ver_result.get("bin_detected") else None,
                    verification_confidence=ver_confidence,
                    evidence_type=ver_result.get("evidence_type", "image"),
                    rejection_reason=error_code,
                )
                disposals_collection.create_disposal(doc)
            except Exception as exc:
                logger.warning(f"MongoDB rejected disposal insert warning: {exc}")

            self._in_memory_store[disposal_id] = rejected_doc_dict

            raise DisposalVerificationError(
                message=ver_message,
                error_code=error_code or "VERIFICATION_UNCLEAR",
                expected_category=expected_category,
                expected_bin=expected_bin_name,
                detected_category=detected_category,
                detected_bin=detected_bin_name,
                confidence=ver_confidence,
            )

        # 5. Successful Verification & Credit Transaction (Step 9 requirement)
        nudge = f"Disposal verified! Item correctly segregated into the {expected_bin_name} ({expected_category})."
        disposal_doc_dict = {
            "_id": disposal_id,
            "disposal_id": disposal_id,
            "user_id": user_id,
            "prediction_id": payload.prediction_id,
            "predicted_category": expected_category,
            "confirmed_category": expected_category,
            "confidence": confidence,
            "verification_status": DISPOSAL_STATUS_VERIFIED,
            "is_correctly_segregated": True,
            "feedback_nudge": nudge,
            "item_label": payload.item_label or (stored_pred.item_label if stored_pred else "Scanned Item"),
            "location_zone": payload.location_zone,
            "device_metadata": payload.device_metadata,
            "timestamp": now,
            "credits_awarded": 0.0,
            "expected_category": expected_category,
            "expected_bin": expected_bin_name,
            "detected_bin": detected_bin_name,
            "detected_category": detected_category,
            "verification_confidence": ver_confidence,
            "evidence_type": ver_result.get("evidence_type", "image"),
        }

        # Transactionally award Swachh Credits ONLY for verified disposals
        from app.services.credits_service import credits_service  # pyrefly: ignore [missing-import]
        tx = credits_service.award_disposal_credits(
            user_id=user_id,
            disposal_id=disposal_id,
            confirmed_category=expected_category,
            verification_status=DISPOSAL_STATUS_VERIFIED,
            is_correctly_segregated=True,
        )
        credits_awarded_val: float = float(tx.amount) if tx else 0.0
        disposal_doc_dict["credits_awarded"] = credits_awarded_val

        # Store via database collection
        try:
            doc = DisposalDocument(
                disposal_id=disposal_id,
                user_id=user_id,
                prediction_id=payload.prediction_id,
                predicted_category=expected_category,
                confirmed_category=expected_category,
                confidence=confidence,
                verification_status=DISPOSAL_STATUS_VERIFIED,
                is_correctly_segregated=True,
                feedback_nudge=nudge,
                item_label=payload.item_label or (stored_pred.item_label if stored_pred else "Scanned Item"),
                location_zone=payload.location_zone,
                device_metadata=payload.device_metadata,
                timestamp=now,
                credits_awarded=credits_awarded_val,
                expected_category=expected_category,
                expected_bin=expected_bin_name,
                detected_bin=detected_bin_name,
                detected_category=detected_category,
                verification_confidence=ver_confidence,
                evidence_type=ver_result.get("evidence_type", "image"),
            )
            disposals_collection.create_disposal(doc)
        except Exception as exc:
            logger.warning(f"MongoDB disposal insert fallback warning: {exc}")

        self._in_memory_store[disposal_id] = disposal_doc_dict
        logger.info(f"Recorded verified disposal {disposal_id} for user {user_id}: credits={disposal_doc_dict['credits_awarded']}")

        resp = DisposalResponse(
            disposal_id=disposal_id,
            user_id=user_id,
            prediction_id=payload.prediction_id,
            predicted_category=expected_category,
            confirmed_category=expected_category,
            confidence=confidence,
            verification_status=DISPOSAL_STATUS_VERIFIED,
            verified=True,
            is_correctly_segregated=True,
            feedback_nudge=nudge,
            item_label=payload.item_label or (stored_pred.item_label if stored_pred else "Scanned Item"),
            location_zone=payload.location_zone,
            timestamp=now,
            credits_awarded=credits_awarded_val,
            expected_category=expected_category,
            expected_bin=expected_bin_name,
            detected_category=detected_category,
            detected_bin=detected_bin_name,
            message=nudge,
        )
        return resp

    def get_disposal_by_id(self, user_id: str, disposal_id: str) -> Optional[DisposalResponse]:
        """Retrieves a single disposal record by ID for the authorized user."""
        try:
            doc = disposals_collection.get_disposal_by_id(disposal_id, user_id=user_id)
            if doc:
                return DisposalResponse(**doc.to_mongo_dict())
        except Exception as exc:
            logger.warning(f"MongoDB disposal search error: {exc}")

        doc_dict = self._in_memory_store.get(disposal_id)
        if doc_dict and doc_dict["user_id"] == user_id:
            return DisposalResponse(**doc_dict)
        return None

    def get_user_disposal_history(self, user_id: str, limit: int = 50, skip: int = 0) -> List[DisposalResponse]:
        """Retrieves disposal history records exclusively for the authorized user."""
        try:
            db_docs = disposals_collection.get_user_disposal_history(user_id, limit=limit, skip=skip)
            if db_docs:
                return [DisposalResponse(**d.to_mongo_dict()) for d in db_docs]
        except Exception as exc:
            logger.warning(f"MongoDB history query error: {exc}")

        user_docs = [doc for doc in self._in_memory_store.values() if doc["user_id"] == user_id]
        user_docs.sort(key=lambda x: x["timestamp"], reverse=True)
        paginated = user_docs[skip : skip + limit]
        return [DisposalResponse(**d) for d in paginated]


# Singleton instance
disposal_service = DisposalService()
