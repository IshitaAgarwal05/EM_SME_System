"""
FastAPI dependency injection for authentication and authorization.
"""

from typing import Annotated
from uuid import UUID

import structlog
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AuthenticationError, AuthorizationError
from app.core.security import decode_token, has_permission
from app.db.session import get_db
from app.models.organization import Organization
from app.models.user import User

logger = structlog.get_logger()

# HTTP Bearer token scheme
security = HTTPBearer()


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> User:
    """
    Get current authenticated user from JWT token.

    Args:
        credentials: HTTP Bearer credentials
        db: Database session

    Returns:
        Current user

    Raises:
        HTTPException: If token is invalid or user not found
    """
    token = credentials.credentials

    try:
        payload = decode_token(token)
    except ValueError as e:
        logger.warning("invalid_token", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Check token type
    if payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = UUID(payload.get("sub"))

    # Get user from database
    result = await db.execute(select(User).where(User.id == user_id, User.is_active == True))
    user = result.scalar_one_or_none()

    if not user:
        logger.warning("user_not_found", user_id=str(user_id))
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


async def get_current_organization(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Organization:
    """
    Get current user's organization.

    Args:
        current_user: Current authenticated user
        db: Database session

    Returns:
        User's organization

    Raises:
        HTTPException: If organization not found
    """
    result = await db.execute(
        select(Organization).where(Organization.id == current_user.organization_id)
    )
    organization = result.scalar_one_or_none()

    if not organization:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found",
        )

    return organization


def require_role(required_role: str):
    """
    Dependency factory to require a specific role.

    Args:
        required_role: Minimum required role

    Returns:
        Dependency function that checks user role
    """

    async def role_checker(current_user: Annotated[User, Depends(get_current_user)]) -> User:
        """Check if user has required role."""
        if not has_permission(current_user.role, required_role):
            logger.warning(
                "insufficient_permissions",
                user_id=str(current_user.id),
                user_role=current_user.role,
                required_role=required_role,
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Requires {required_role} role or higher",
            )
        return current_user

    return role_checker


def check_organization_access(resource_org_id: UUID, user: User) -> None:
    """
    Check if user has access to a resource in an organization.

    Args:
        resource_org_id: Organization ID of the resource
        user: Current user

    Raises:
        HTTPException: If user doesn't have access
    """
    if user.organization_id != resource_org_id:
        logger.warning(
            "organization_access_denied",
            user_id=str(user.id),
            user_org_id=str(user.organization_id),
            resource_org_id=str(resource_org_id),
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: Resource belongs to different organization",
        )


# Type aliases for common dependencies
CurrentUser = Annotated[User, Depends(get_current_user)]
CurrentOrganization = Annotated[Organization, Depends(get_current_organization)]
OwnerUser = Annotated[User, Depends(require_role("owner"))]
ManagerUser = Annotated[User, Depends(require_role("manager"))]
