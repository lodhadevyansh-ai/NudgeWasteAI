"""
Disposal Management and Verification API Routes.
Endpoints for recording waste disposals, fetching user disposal records, and history audit logs.
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import JSONResponse

from app.schemas.user import UserResponse  # pyrefly: ignore [missing-import]
from app.schemas.disposal import DisposalCreate, DisposalResponse  # pyrefly: ignore [missing-import]
from app.services.disposal_service import disposal_service, DisposalVerificationError  # pyrefly: ignore [missing-import]
from app.api.dependencies import get_current_user  # pyrefly: ignore [missing-import]

router = APIRouter(prefix="/disposal", tags=["Disposal Verification"])


@router.post(
    "",
    response_model=DisposalResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Record and Verify Waste Disposal",
    description="Verifies statutory waste segregation rules and records disposal event for authenticated user.",
)
@router.post(
    "/verify",
    response_model=DisposalResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Verify Waste Disposal",
    description="Verifies statutory waste segregation rules and records disposal event for authenticated user.",
)
async def record_disposal(
    payload: DisposalCreate,
    current_user: UserResponse = Depends(get_current_user),
):
    """Verifies and records a new waste disposal event with real ML bin verification."""
    try:
        response = disposal_service.verify_and_record_disposal(current_user.id, payload)
        return response
    except DisposalVerificationError as exc:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "success": False,
                "verified": False,
                "error_code": exc.error_code,
                "message": exc.message,
                "expected_category": exc.expected_category,
                "expected_bin": exc.expected_bin,
                "detected_category": exc.detected_category,
                "detected_bin": exc.detected_bin,
                "confidence": exc.confidence,
                "credits_awarded": 0.0,
            },
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )


@router.get(
    "/history",
    response_model=List[DisposalResponse],
    status_code=status.HTTP_200_OK,
    summary="Get User Disposal History",
    description="Returns chronological waste disposal history for the currently authenticated user.",
)
async def get_my_disposal_history(
    limit: int = Query(default=50, ge=1, le=100, description="Maximum number of records to return"),
    skip: int = Query(default=0, ge=0, description="Number of records to skip"),
    current_user: UserResponse = Depends(get_current_user),
):
    """Retrieves paginated disposal history for authenticated user."""
    history = disposal_service.get_user_disposal_history(current_user.id, limit=limit, skip=skip)
    return history


@router.get(
    "/{disposal_id}",
    response_model=DisposalResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Specific Disposal Record",
    description="Retrieves a specific disposal event record by ID (restricted to owning user).",
)
async def get_disposal_record(
    disposal_id: str,
    current_user: UserResponse = Depends(get_current_user),
):
    """Retrieves single disposal record by ID."""
    record = disposal_service.get_disposal_by_id(current_user.id, disposal_id)
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Disposal record '{disposal_id}' not found or access unauthorized.",
        )
    return record
