"""
Pydantic schemas for invitation management.
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


class InvitationCreate(BaseModel):
    """Schema for creating a new invitation."""

    email: EmailStr
    role: str = Field(..., pattern="^(manager|employee|contractor)$")


class InvitationResponse(BaseModel):
    """Schema for invitation response."""

    id: UUID
    organization_id: UUID
    email: str
    role: str
    invited_by_id: UUID
    token: str
    expires_at: datetime
    accepted_at: datetime | None
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


class InvitationAccept(BaseModel):
    """Schema for accepting an invitation."""

    full_name: str = Field(..., min_length=2, max_length=255)
    password: str = Field(..., min_length=8)
    phone: str | None = Field(None, max_length=20)


class InvitationPublicInfo(BaseModel):
    """Public invitation info (no sensitive data)."""

    organization_name: str
    role: str
    invited_by_name: str
    expires_at: datetime
    is_valid: bool
