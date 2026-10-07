"""
Municipal Rewards API Routes.
Endpoints for viewing available municipal rewards, redeeming incentives, and tracking redemptions.
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status

from app.schemas.user import UserResponse  # pyrefly: ignore [missing-import]
from app.schemas.reward import RewardResponse, RewardRedemptionResponse  # pyrefly: ignore [missing-import]
from app.services.reward_service import reward_service  # pyrefly: ignore [missing-import]
from app.api.dependencies import get_current_user  # pyrefly: ignore [missing-import]

router = APIRouter(prefix="/rewards", tags=["Municipal Rewards"])


@router.get(
    "",
    response_model=List[RewardResponse],
    status_code=status.HTTP_200_OK,
    summary="Get Available Municipal Rewards",
    description="Returns list of available municipal incentive rewards.",
)
async def get_rewards_catalog():
    """Retrieves active municipal reward incentives catalog."""
    return reward_service.get_available_rewards()


@router.post(
    "/redeem/{reward_id}",
    response_model=RewardRedemptionResponse,
    status_code=status.HTTP_200_OK,
    summary="Redeem Municipal Reward",
    description="Redeems a municipal reward voucher using available Swachh Credits.",
)
async def redeem_municipal_reward(
    reward_id: str,
    current_user: UserResponse = Depends(get_current_user),
):
    """Redeems a reward for authenticated user."""
    try:
        return reward_service.redeem_reward(current_user.id, reward_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )


@router.get(
    "/my-redemptions",
    response_model=List[RewardRedemptionResponse],
    status_code=status.HTTP_200_OK,
    summary="Get User Reward Redemptions",
    description="Returns redemption history and claim voucher codes for the authenticated user.",
)
async def get_my_redemptions(
    current_user: UserResponse = Depends(get_current_user),
):
    """Retrieves redemption history for authenticated user."""
    return reward_service.get_user_redemptions(current_user.id)
