"""
Invitation API endpoints for team member onboarding.
"""

from datetime import datetime
from uuid import UUID

import structlog
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.models.invitation import Invitation
from app.models.organization import Organization
from app.models.user import User
from app.schemas.invitation import (
    InvitationAccept,
    InvitationCreate,
    InvitationPublicInfo,
    InvitationResponse,
)
from app.services.auth_service import AuthService
from app.services.email_service import EmailService

logger = structlog.get_logger()
router = APIRouter()


@router.post("", response_model=InvitationResponse, status_code=status.HTTP_201_CREATED)
async def create_invitation(
    invitation_data: InvitationCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Invitation:
    """
    Create a new team invitation (Manager only).
    
    Sends an email with a magic link to join the organization.
    """
    # Check if user is a manager
    if current_user.role != "manager":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only managers can invite team members",
        )

    # Check if email already exists in organization
    existing_user = await db.execute(
        select(User).where(
            User.email == invitation_data.email,
            User.organization_id == current_user.organization_id,
        )
    )
    if existing_user.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email already exists in your organization",
        )

    # Check for pending invitation
    existing_invitation = await db.execute(
        select(Invitation).where(
            Invitation.email == invitation_data.email,
            Invitation.organization_id == current_user.organization_id,
            Invitation.status == "pending",
        )
    )
    if existing_invitation.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Pending invitation already exists for this email",
        )

    # Create invitation
    invitation = Invitation(
        organization_id=current_user.organization_id,
        email=invitation_data.email,
        role=invitation_data.role,
        invited_by_id=current_user.id,
        token=Invitation.generate_token(),
        expires_at=Invitation.default_expiry(),
        status="pending",
    )

    db.add(invitation)
    await db.commit()
    await db.refresh(invitation)

    # Send invitation email
    try:
        email_service = EmailService()
        await email_service.send_invitation_email(
            to_email=invitation.email,
            inviter_name=current_user.full_name,
            organization_name=current_user.organization.name,
            invite_token=invitation.token,
            role=invitation.role,
        )
        logger.info(
            "invitation_created",
            invitation_id=str(invitation.id),
            email=invitation.email,
            role=invitation.role,
        )
    except Exception as e:
        logger.error("invitation_email_failed", error=str(e))
        # Don't fail the request if email fails
        pass

    return invitation


@router.get("", response_model=list[InvitationResponse])
async def list_invitations(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[Invitation]:
    """List all pending invitations for the organization."""
    result = await db.execute(
        select(Invitation)
        .where(
            Invitation.organization_id == current_user.organization_id,
            Invitation.status == "pending",
        )
        .order_by(Invitation.created_at.desc())
    )
    return list(result.scalars().all())


@router.get("/{token}/info", response_model=InvitationPublicInfo)
async def get_invitation_info(
    token: str,
    db: AsyncSession = Depends(get_db),
) -> InvitationPublicInfo:
    """
    Get public invitation info (no auth required).
    
    Used to display invitation details before user accepts.
    """
    result = await db.execute(
        select(Invitation).where(Invitation.token == token)
    )
    invitation = result.scalar_one_or_none()

    if not invitation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invitation not found",
        )

    # Load relationships
    await db.refresh(invitation, ["organization", "invited_by"])

    return InvitationPublicInfo(
        organization_name=invitation.organization.name,
        role=invitation.role,
        invited_by_name=invitation.invited_by.full_name,
        expires_at=invitation.expires_at,
        is_valid=invitation.is_valid(),
    )


@router.post("/{token}/accept", status_code=status.HTTP_201_CREATED)
async def accept_invitation(
    token: str,
    accept_data: InvitationAccept,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Accept an invitation and create user account (no auth required).
    
    Returns access token for immediate login.
    """
    result = await db.execute(
        select(Invitation).where(Invitation.token == token)
    )
    invitation = result.scalar_one_or_none()

    if not invitation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invitation not found",
        )

    if not invitation.is_valid():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invitation has expired or is no longer valid",
        )

    # Check if email already registered
    existing_user = await db.execute(
        select(User).where(User.email == invitation.email)
    )
    if existing_user.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email already exists",
        )

    # Create user
    auth_service = AuthService()
    password_hash = auth_service.hash_password(accept_data.password)

    new_user = User(
        organization_id=invitation.organization_id,
        email=invitation.email,
        password_hash=password_hash,
        full_name=accept_data.full_name,
        phone=accept_data.phone,
        role=invitation.role,
        is_active=True,
        email_verified=True,  # Auto-verify via invitation
    )

    db.add(new_user)

    # Mark invitation as accepted
    invitation.status = "accepted"
    invitation.accepted_at = datetime.utcnow()

    await db.commit()
    await db.refresh(new_user)

    # Generate access token
    access_token = auth_service.create_access_token(user_id=new_user.id)
    refresh_token = await auth_service.create_refresh_token(db, new_user.id)

    logger.info(
        "invitation_accepted",
        invitation_id=str(invitation.id),
        user_id=str(new_user.id),
        email=new_user.email,
    )

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": {
            "id": str(new_user.id),
            "email": new_user.email,
            "full_name": new_user.full_name,
            "role": new_user.role,
            "organization_id": str(new_user.organization_id),
        },
    }


@router.delete("/{invitation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_invitation(
    invitation_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    """Revoke a pending invitation (Manager only)."""
    if current_user.role != "manager":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only managers can revoke invitations",
        )

    result = await db.execute(
        select(Invitation).where(
            Invitation.id == invitation_id,
            Invitation.organization_id == current_user.organization_id,
        )
    )
    invitation = result.scalar_one_or_none()

    if not invitation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invitation not found",
        )

    invitation.status = "revoked"
    await db.commit()

    logger.info("invitation_revoked", invitation_id=str(invitation_id))
