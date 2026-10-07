"""
Swachh Credits API Routes.
Endpoints for user credit balance retrieval and auditable transaction log history.
"""

from typing import List
from fastapi import APIRouter, Depends, Query, status

from app.schemas.user import UserResponse  # pyrefly: ignore [missing-import]
from app.schemas.credits import CreditBalanceResponse, CreditTransactionResponse  # pyrefly: ignore [missing-import]
from app.services.credits_service import credits_service  # pyrefly: ignore [missing-import]
from app.api.dependencies import get_current_user  # pyrefly: ignore [missing-import]

router = APIRouter(prefix="/credits", tags=["Swachh Credits"])


@router.get(
    "",
    response_model=CreditBalanceResponse,
    status_code=status.HTTP_200_OK,
    summary="Get User Credit Balance",
    description="Retrieves current Swachh Credits balance and lifetime statistics for the authenticated user.",
)
async def get_my_credit_balance(
    current_user: UserResponse = Depends(get_current_user),
):
    """Returns current user's Swachh Credits balance."""
    return credits_service.get_user_balance(current_user.id)


@router.get(
    "/history",
    response_model=List[CreditTransactionResponse],
    status_code=status.HTTP_200_OK,
    summary="Get Credit Transaction History",
    description="Returns auditable credit transaction history for the authenticated user.",
)
async def get_my_credit_history(
    limit: int = Query(default=50, ge=1, le=100, description="Maximum number of records to return"),
    skip: int = Query(default=0, ge=0, description="Number of records to skip"),
    current_user: UserResponse = Depends(get_current_user),
):
    """Retrieves paginated credit transaction history for authenticated user."""
    return credits_service.get_user_credit_history(current_user.id, limit=limit, skip=skip)
