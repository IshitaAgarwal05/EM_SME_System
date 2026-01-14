"""
Authentication API endpoints for registration, login, and token management.
"""

from typing import Annotated

import structlog
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AuthenticationError, ConflictError, ValidationError
from app.db.session import get_db
from app.dependencies import CurrentUser
from app.schemas.common import MessageResponse
from app.schemas.user import (
    PasswordResetConfirm,
    PasswordResetRequest,
    TokenRefreshRequest,
    TokenResponse,
    UserCreate,
    UserLogin,
    UserResponse,
)
from app.services.auth_service import AuthService

logger = structlog.get_logger()

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> UserResponse:
    """
    Register a new user and create an organization.

    - **email**: Valid email address (must be unique)
    - **password**: Strong password (min 8 chars, uppercase, lowercase, digit)
    - **full_name**: User's full name
    - **organization_name**: Organization name (required for first user)
    """
    auth_service = AuthService(db)

    try:
        user, organization = await auth_service.register_user(user_data)
        return UserResponse.model_validate(user)
    except ConflictError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))


@router.post("/login", response_model=TokenResponse)
async def login(
    credentials: UserLogin,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> TokenResponse:
    """
    Login with email and password to get JWT tokens.

    Returns access token (15 min expiry) and refresh token (7 day expiry).
    """
    auth_service = AuthService(db)

    try:
        user = await auth_service.authenticate_user(credentials.email, credentials.password)
        tokens = await auth_service.create_tokens(user)
        return tokens
    except AuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    request: TokenRefreshRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> TokenResponse:
    """
    Refresh access token using refresh token.

    The old refresh token will be revoked and a new one issued (token rotation).
    """
    auth_service = AuthService(db)

    try:
        tokens = await auth_service.refresh_access_token(request.refresh_token)
        return tokens
    except AuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )


@router.post("/logout", response_model=MessageResponse)
async def logout(
    request: TokenRefreshRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: CurrentUser,
) -> MessageResponse:
    """
    Logout by revoking refresh token.

    Requires authentication. The refresh token will be invalidated.
    """
    auth_service = AuthService(db)
    await auth_service.revoke_refresh_token(request.refresh_token)

    logger.info("user_logged_out", user_id=str(current_user.id))

    return MessageResponse(message="Successfully logged out")


@router.post("/forgot-password", response_model=MessageResponse)
async def forgot_password(
    request: PasswordResetRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> MessageResponse:
    """
    Request password reset email.

    Sends a password reset link to the user's email if it exists.
    Always returns success to prevent email enumeration.
    """
    # TODO: Implement email sending with password reset token
    # For now, just log the request

    logger.info("password_reset_requested", email=request.email)

    return MessageResponse(
        message="If the email exists, a password reset link has been sent"
    )


@router.post("/reset-password", response_model=MessageResponse)
async def reset_password(
    request: PasswordResetConfirm,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> MessageResponse:
    """
    Reset password using reset token.

    The token is sent via email in the forgot-password flow.
    """
    # TODO: Implement password reset with token validation
    # For now, return not implemented

    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Password reset not yet implemented",
    )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: CurrentUser) -> UserResponse:
    """
    Get current authenticated user's profile.

    Requires authentication.
    """
    return UserResponse.model_validate(current_user)
