"""
Nudge Engine API Routes.
Endpoints for generating localized behavioural micro-nudges and retrieving nudge records.
"""

from fastapi import APIRouter, HTTPException, status

from app.schemas.nudge import NudgeRequest, NudgeResponse  # pyrefly: ignore [missing-import]
from app.services.nudge_service import nudge_service  # pyrefly: ignore [missing-import]

router = APIRouter(prefix="/nudges", tags=["Behavioural Nudge Engine"])


@router.post(
    "/generate",
    response_model=NudgeResponse,
    status_code=status.HTTP_200_OK,
    summary="Generate Behavioural Nudge",
    description="Generates an encouraging, educational micro-nudge based on predicted/disposed statutory category and contamination risk.",
)
async def generate_nudge(payload: NudgeRequest):
    """Generates a structured behavioural micro-nudge."""
    try:
        response = nudge_service.generate_nudge(payload)
        return response
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )


@router.get(
    "/{nudge_id}",
    response_model=NudgeResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Specific Nudge Record",
    description="Retrieves a generated nudge record by ID.",
)
async def get_nudge_record(nudge_id: str):
    """Retrieves a single nudge record by ID."""
    record = nudge_service.get_nudge_by_id(nudge_id)
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Nudge record '{nudge_id}' not found.",
        )
    return record
