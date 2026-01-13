"""
Authentication service with business logic for user registration, login, and token management.
"""

import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from uuid import UUID

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.exceptions import (
    AuthenticationError,
    ConflictError,
    NotFoundError,
    ValidationError,
)
from app.core.security import (
    create_access_token,
    create_refresh_token,
    get_password_hash,
    verify_password,
)
from app.models.organization import Organization
from app.models.user import RefreshToken, User
from app.schemas.user import TokenResponse, UserCreate

logger = structlog.get_logger()


class AuthService:
    """Service for authentication operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def register_user(self, user_data: UserCreate) -> tuple[User, Organization]:
        """
        Register a new user and optionally create an organization.

        Args:
            user_data: User registration data

        Returns:
            Tuple of (User, Organization)

        Raises:
            ConflictError: If email already exists
            ValidationError: If validation fails
        """
        # Check if email already exists
        result = await self.db.execute(select(User).where(User.email == user_data.email))
        existing_user = result.scalar_one_or_none()

        if existing_user:
            raise ConflictError("Email already registered")

        # Create organization if provided (first user)
        if user_data.organization_name:
            org_slug = self._generate_slug(user_data.organization_name)

            # Check if slug exists
            result = await self.db.execute(
                select(Organization).where(Organization.slug == org_slug)
            )
            if result.scalar_one_or_none():
                # Add random suffix to make unique
                org_slug = f"{org_slug}-{secrets.token_hex(4)}"

            organization = Organization(
                name=user_data.organization_name,
                slug=org_slug,
                subscription_tier="free",
            )
            self.db.add(organization)
            await self.db.flush()  # Get organization ID

            user_role = "owner"
        else:
            raise ValidationError("Organization name is required for registration")

        # Create user
        user = User(
            organization_id=organization.id,
            email=user_data.email,
            phone=user_data.phone,
            password_hash=get_password_hash(user_data.password),
            full_name=user_data.full_name,
            role=user_role,
            is_active=True,
            email_verified=False,
        )

        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        await self.db.refresh(organization)

        logger.info(
            "user_registered",
            user_id=str(user.id),
            email=user.email,
            organization_id=str(organization.id),
        )

        return user, organization

    async def authenticate_user(self, email: str, password: str) -> User:
        """
        Authenticate user with email and password.

        Args:
            email: User email
            password: User password

        Returns:
            Authenticated user

        Raises:
            AuthenticationError: If credentials are invalid
        """
        result = await self.db.execute(
            select(User).where(User.email == email, User.is_active == True)
        )
        user = result.scalar_one_or_none()

        if not user or not verify_password(password, user.password_hash):
            logger.warning("authentication_failed", email=email)
            raise AuthenticationError("Invalid email or password")

        # Update last login
        user.last_login_at = datetime.now(timezone.utc)
        await self.db.commit()

        logger.info("user_authenticated", user_id=str(user.id), email=user.email)

        return user

    async def create_tokens(self, user: User) -> TokenResponse:
        """
        Create access and refresh tokens for user.

        Args:
            user: User object

        Returns:
            Token response with access and refresh tokens
        """
        # Create access token
        access_token = create_access_token(
            data={
                "sub": str(user.id),
                "email": user.email,
                "org_id": str(user.organization_id),
                "role": user.role,
            }
        )

        # Create refresh token
        refresh_token = create_refresh_token(
            data={
                "sub": str(user.id),
                "type": "refresh",
            }
        )

        # Store refresh token in database
        token_hash = hashlib.sha256(refresh_token.encode()).hexdigest()
        expires_at = datetime.now(timezone.utc) + timedelta(days=settings.refresh_token_expire_days)

        db_refresh_token = RefreshToken(
            user_id=user.id,
            token_hash=token_hash,
            expires_at=expires_at,
        )

        self.db.add(db_refresh_token)
        await self.db.commit()

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=settings.access_token_expire_minutes * 60,
        )

    async def refresh_access_token(self, refresh_token: str) -> TokenResponse:
        """
        Refresh access token using refresh token.

        Args:
            refresh_token: Refresh token string

        Returns:
            New token response

        Raises:
            AuthenticationError: If refresh token is invalid or expired
        """
        from app.core.security import decode_token

        # Verify refresh token
        try:
            payload = decode_token(refresh_token)
        except ValueError as e:
            raise AuthenticationError(str(e))

        if payload.get("type") != "refresh":
            raise AuthenticationError("Invalid token type")

        user_id = UUID(payload.get("sub"))

        # Check if token exists in database and is not revoked
        token_hash = hashlib.sha256(refresh_token.encode()).hexdigest()

        result = await self.db.execute(
            select(RefreshToken).where(
                RefreshToken.user_id == user_id,
                RefreshToken.token_hash == token_hash,
                RefreshToken.revoked == False,
                RefreshToken.expires_at > datetime.now(timezone.utc),
            )
        )
        db_token = result.scalar_one_or_none()

        if not db_token:
            raise AuthenticationError("Invalid or expired refresh token")

        # Get user
        result = await self.db.execute(
            select(User).where(User.id == user_id, User.is_active == True)
        )
        user = result.scalar_one_or_none()

        if not user:
            raise AuthenticationError("User not found or inactive")

        # Revoke old refresh token (token rotation)
        db_token.revoked = True

        # Create new tokens
        tokens = await self.create_tokens(user)
        await self.db.commit()

        logger.info("token_refreshed", user_id=str(user.id))

        return tokens

    async def revoke_refresh_token(self, refresh_token: str) -> None:
        """
        Revoke a refresh token (logout).

        Args:
            refresh_token: Refresh token to revoke
        """
        token_hash = hashlib.sha256(refresh_token.encode()).hexdigest()

        result = await self.db.execute(
            select(RefreshToken).where(RefreshToken.token_hash == token_hash)
        )
        db_token = result.scalar_one_or_none()

        if db_token:
            db_token.revoked = True
            await self.db.commit()
            logger.info("token_revoked", token_id=str(db_token.id))

    @staticmethod
    def _generate_slug(name: str) -> str:
        """Generate URL-friendly slug from organization name."""
        import re

        slug = name.lower()
        slug = re.sub(r"[^\w\s-]", "", slug)
        slug = re.sub(r"[-\s]+", "-", slug)
        return slug.strip("-")[:100]
