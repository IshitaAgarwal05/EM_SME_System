"""
Security utilities for authentication and authorization.
Includes password hashing, JWT token generation, and RBAC.
"""

from datetime import datetime, timedelta, timezone
from typing import Any

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.config import settings

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password for storage."""
    return pwd_context.hash(password)


def create_access_token(data: dict[str, Any], expires_delta: timedelta | None = None) -> str:
    """
    Create a JWT access token.

    Args:
        data: Payload data to encode in the token
        expires_delta: Optional custom expiration time

    Returns:
        Encoded JWT token string
    """
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.access_token_expire_minutes)

    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)
    return encoded_jwt


def create_refresh_token(data: dict[str, Any]) -> str:
    """
    Create a JWT refresh token.

    Args:
        data: Payload data to encode in the token

    Returns:
        Encoded JWT token string
    """
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(days=settings.refresh_token_expire_days)

    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)
    return encoded_jwt


def decode_token(token: str) -> dict[str, Any]:
    """
    Decode and verify a JWT token.

    Args:
        token: JWT token string

    Returns:
        Decoded token payload

    Raises:
        JWTError: If token is invalid or expired
    """
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        return payload
    except JWTError as e:
        raise ValueError(f"Invalid token: {str(e)}") from e


# Role hierarchy for RBAC
ROLE_HIERARCHY = {
    "owner": 4,
    "manager": 3,
    "contractor": 2,
    "viewer": 1,
}


def has_permission(user_role: str, required_role: str) -> bool:
    """
    Check if a user role has sufficient permissions.

    Args:
        user_role: The user's current role
        required_role: The minimum required role

    Returns:
        True if user has sufficient permissions
    """
    user_level = ROLE_HIERARCHY.get(user_role, 0)
    required_level = ROLE_HIERARCHY.get(required_role, 0)
    return user_level >= required_level


def check_resource_access(
    user_org_id: str,
    resource_org_id: str,
    user_role: str,
    required_role: str = "viewer",
) -> bool:
    """
    Check if user has access to a resource.

    Args:
        user_org_id: User's organization ID
        resource_org_id: Resource's organization ID
        user_role: User's role
        required_role: Minimum required role

    Returns:
        True if user has access

    Raises:
        PermissionError: If user doesn't have access
    """
    # Check organization match
    if user_org_id != resource_org_id:
        raise PermissionError("Access denied: Resource belongs to different organization")

    # Check role permissions
    if not has_permission(user_role, required_role):
        raise PermissionError(
            f"Access denied: Requires {required_role} role, user has {user_role}"
        )

    return True
