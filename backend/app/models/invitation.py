"""
Invitation model for team member invitations.
"""

import uuid
from datetime import datetime, timedelta
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, UUIDMixin

if TYPE_CHECKING:
    from app.models.user import Organization, User


class Invitation(Base, UUIDMixin):
    """Team invitation model for onboarding new members."""

    __tablename__ = "invitations"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    email: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    role: Mapped[str] = mapped_column(
        String(50), nullable=False, default="employee"
    )  # manager, employee, contractor
    
    invited_by_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    
    token: Mapped[str] = mapped_column(
        String(64), nullable=False, unique=True, index=True
    )  # unique invite token
    
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    
    accepted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="pending", index=True
    )  # pending, accepted, expired, revoked
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    # Relationships
    organization: Mapped["Organization"] = relationship("Organization", back_populates="invitations")
    invited_by: Mapped["User"] = relationship("User", foreign_keys=[invited_by_id])

    def __repr__(self) -> str:
        return f"<Invitation {self.email} to {self.organization_id} ({self.status})>"

    def is_valid(self) -> bool:
        """Check if invitation is still valid."""
        return (
            self.status == "pending"
            and self.expires_at > datetime.utcnow()
            and self.accepted_at is None
        )

    @staticmethod
    def generate_token() -> str:
        """Generate a secure random token."""
        import secrets
        return secrets.token_urlsafe(48)

    @staticmethod
    def default_expiry() -> datetime:
        """Get default expiry time (7 days from now)."""
        return datetime.utcnow() + timedelta(days=7)
