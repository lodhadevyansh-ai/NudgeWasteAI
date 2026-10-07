"""
User Management and Authentication API Routes.
Endpoints for user registration, login authentication, and profile retrieval.
"""

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.security import create_access_token  # pyrefly: ignore [missing-import]
from app.schemas.user import UserRegister, UserLogin, UserResponse, Token  # pyrefly: ignore [missing-import]
from app.services.user_service import user_service  # pyrefly: ignore [missing-import]
from app.api.dependencies import get_current_user  # pyrefly: ignore [missing-import]

router = APIRouter(prefix="/users", tags=["Users"])


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="User Registration",
    description="Register a new civic user on the NudgeWasteAI platform.",
)
async def register_user(user_data: UserRegister):
    """Registers a new user account."""
    try:
        user_response = user_service.create_user(user_data)
        return user_response
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )


@router.post(
    "/login",
    response_model=Token,
    status_code=status.HTTP_200_OK,
    summary="User Login",
    description="Authenticate user credentials and receive a JWT Bearer access token.",
)
async def login_user(credentials: UserLogin):
    """Authenticates user credentials and issues JWT token."""
    user = user_service.authenticate_user(credentials.email, credentials.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(
        data={"sub": user.id, "email": user.email}
    )
    return Token(access_token=access_token, token_type="bearer")


@router.get(
    "/me",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Current User Profile",
    description="Retrieve profile information for the currently authenticated user.",
)
async def get_my_profile(current_user: UserResponse = Depends(get_current_user)):
    """Returns profile for currently authenticated user."""
    return current_user


@router.delete(
    "/me",
    status_code=status.HTTP_200_OK,
    summary="Delete Current User Account",
    description="Permanently deletes the currently authenticated user's account and associated data from MongoDB.",
)
async def delete_my_account(current_user: UserResponse = Depends(get_current_user)):
    """Permanently deletes current authenticated user account and data."""
    try:
        user_service.delete_user_account(current_user.id)
        return {
            "success": True,
            "message": "Account deleted successfully",
        }
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found",
        )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to delete your account. Please try again.",
        )

