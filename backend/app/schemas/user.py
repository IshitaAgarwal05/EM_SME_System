"""
User and authentication Pydantic schemas.
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, field_validator

from app.schemas.common import TimestampSchema


class UserBase(BaseModel):
    """Base user schema with common fields."""

    email: EmailStr
    full_name: str = Field(min_length=1, max_length=255)
    phone: str | None = Field(default=None, max_length=20)
    branch: str | None = Field(default=None, max_length=100)
    position: str | None = Field(default=None, max_length=100)


class UserCreate(UserBase):
    """Schema for user registration."""

    password: str = Field(min_length=8, max_length=100)
    organization_name: str | None = Field(
        default=None,
        min_length=1,
        max_length=255,
        description="Organization name (for first user only)",
    )

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        """Validate password strength."""
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.islower() for c in v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")
        return v


class UserLogin(BaseModel):
    """Schema for user login."""

    email: EmailStr
    password: str


class UserUpdate(BaseModel):
    """Schema for updating user profile."""

    full_name: str | None = Field(default=None, min_length=1, max_length=255)
    phone: str | None = Field(default=None, max_length=20)
    branch: str | None = Field(default=None, max_length=100)
    position: str | None = Field(default=None, max_length=100)
    role: str | None = Field(default=None, max_length=50) # Allow manager to change role
    preferences: dict | None = None


class UserResponse(UserBase, TimestampSchema):
    """Schema for user response (without password)."""

    id: UUID
    organization_id: UUID
    role: str
    is_active: bool
    email_verified: bool
    last_login_at: datetime | None
    branch: str | None
    position: str | None
    preferences: dict

    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    """Schema for JWT token response."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = Field(description="Access token expiry in seconds")


class TokenRefreshRequest(BaseModel):
    """Schema for token refresh request."""

    refresh_token: str


class PasswordResetRequest(BaseModel):
    """Schema for password reset request."""

    email: EmailStr


class PasswordResetConfirm(BaseModel):
    """Schema for password reset confirmation."""

    token: str
    new_password: str = Field(min_length=8, max_length=100)

    @field_validator("new_password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        """Validate password strength."""
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.islower() for c in v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")
        return v
