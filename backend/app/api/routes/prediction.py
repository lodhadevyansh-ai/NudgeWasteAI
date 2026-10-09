"""
Prediction and Waste Classification API Routes.
Exposes endpoints for image and metadata based statutory waste classification.
"""

import base64
from typing import Optional
from fastapi import APIRouter, File, Form, HTTPException, UploadFile, status

from app.schemas.prediction import PredictionRequest, PredictionResponse  # pyrefly: ignore [missing-import]
from app.services.prediction_service import prediction_service  # pyrefly: ignore [missing-import]

router = APIRouter(prefix="/prediction", tags=["Prediction & Classification"])


@router.post(
    "",
    response_model=PredictionResponse,
    status_code=status.HTTP_200_OK,
    summary="Classify Waste Item",
    description="Classifies an item into statutory waste categories ('Wet', 'Dry', 'Sanitary', 'Special Care') based on image data or item label.",
)
async def predict_waste_category(payload: PredictionRequest):
    """Classifies waste item from JSON request payload."""
    try:
        response = prediction_service.predict_waste(payload)
        return response
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        )


@router.post(
    "/upload",
    response_model=PredictionResponse,
    status_code=status.HTTP_200_OK,
    summary="Classify Waste Item via File Upload",
    description="Classifies an uploaded camera image file into statutory waste categories.",
)
async def predict_waste_upload(
    file: UploadFile = File(..., description="Captured image file from camera or gallery"),
    item_label: Optional[str] = Form(default=None, description="Optional item name hint"),
    min_confidence: Optional[float] = Form(default=0.60, description="Minimum confidence threshold"),
):
    """Classifies waste item from uploaded image file."""
    try:
        contents = await file.read()
        if not contents:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Uploaded file is empty",
            )
        base64_encoded = base64.b64encode(contents).decode("utf-8")
        clean_hint = item_label.strip() if (item_label and item_label.strip()) else None
        payload = PredictionRequest(
            image_base64=base64_encoded,
            item_label=clean_hint,
            min_confidence=min_confidence,
        )
        return prediction_service.predict_waste(payload)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        )
