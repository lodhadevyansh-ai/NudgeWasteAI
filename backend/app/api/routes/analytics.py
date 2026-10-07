"""
Analytics and Reporting API Routes.
Endpoints for municipal waste dashboards, citizen statistics, statutory stream distributions, and trend analysis.
"""

from fastapi import APIRouter, Depends, Query, status

from app.schemas.user import UserResponse  # pyrefly: ignore [missing-import]
from app.schemas.analytics import (  # pyrefly: ignore [missing-import]
    AnalyticsSummaryResponse,
    WasteDistributionResponse,
    TrendsResponse,
    CreditsAnalyticsResponse,
)
from app.services.analytics_service import analytics_service  # pyrefly: ignore [missing-import]
from app.api.dependencies import get_current_user  # pyrefly: ignore [missing-import]

router = APIRouter(prefix="/analytics", tags=["Analytics & Municipal Reporting"])


@router.get(
    "/summary",
    response_model=AnalyticsSummaryResponse,
    status_code=status.HTTP_200_OK,
    summary="Platform Municipal Analytics Summary",
    description="[Access Model: Public / Municipal Overview] Returns platform-wide civic waste segregation metrics.",
)
async def get_platform_analytics_summary():
    """Retrieves platform-wide aggregated waste segregation metrics."""
    return analytics_service.get_summary(user_id=None)


@router.get(
    "/user",
    response_model=AnalyticsSummaryResponse,
    status_code=status.HTTP_200_OK,
    summary="User Personal Analytics Summary",
    description="[Access Model: Authenticated Citizen] Returns personal civic waste segregation metrics for the current user.",
)
async def get_user_analytics_summary(
    current_user: UserResponse = Depends(get_current_user),
):
    """Retrieves personal waste segregation statistics for authenticated user."""
    return analytics_service.get_summary(user_id=current_user.id)


@router.get(
    "/waste-distribution",
    response_model=WasteDistributionResponse,
    status_code=status.HTTP_200_OK,
    summary="Waste Stream Volume Distribution",
    description="Returns volume distribution counts and percentages across the 4 statutory waste streams (Wet, Dry, Sanitary, Special Care).",
)
async def get_waste_stream_distribution():
    """Retrieves volume counts for statutory waste categories."""
    return analytics_service.get_waste_distribution(user_id=None)


@router.get(
    "/trends",
    response_model=TrendsResponse,
    status_code=status.HTTP_200_OK,
    summary="Daily Segregation Trends",
    description="Returns daily time-series disposal counts and segregation success rates.",
)
async def get_segregation_trends(
    days: int = Query(default=30, ge=1, le=365, description="Time window in days"),
):
    """Retrieves daily time-series segregation trend data."""
    return analytics_service.get_disposal_trends(days=days, user_id=None)


@router.get(
    "/credits",
    response_model=CreditsAnalyticsResponse,
    status_code=status.HTTP_200_OK,
    summary="Swachh Credits Economics Analytics",
    description="Returns platform-wide Swachh Credits issuance, redemptions, and statutory category credit breakdown.",
)
async def get_credits_platform_analytics():
    """Retrieves platform Swachh Credits economics metrics."""
    return analytics_service.get_credits_analytics()