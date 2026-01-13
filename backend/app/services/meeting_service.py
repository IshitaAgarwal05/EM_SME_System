"""
Meeting service for scheduling and managing meetings.
"""

from datetime import datetime, timedelta, timezone
from typing import Sequence
from uuid import UUID

import structlog
from sqlalchemy import select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import NotFoundError, ValidationError, AuthorizationError
from app.models.meeting import Meeting, MeetingParticipant
from app.models.user import User
from app.schemas.meeting import MeetingCreate, MeetingUpdate

logger = structlog.get_logger()


class MeetingService:
    """Service for meeting and scheduling operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_meeting(self, meeting_id: UUID) -> Meeting:
        """Get meeting by ID with participants."""
        query = (
            select(Meeting)
            .options(selectinload(Meeting.participants))
            .where(Meeting.id == meeting_id)
        )
        result = await self.db.execute(query)
        meeting = result.scalar_one_or_none()

        if not meeting:
            raise NotFoundError("Meeting", str(meeting_id))

        return meeting

    async def create_meeting(self, data: MeetingCreate, organizer: User) -> Meeting:
        """Create a new meeting."""
        
        # Check for conflicts
        if await self._check_conflicts(organizer.id, data.start_time, data.end_time):
             logger.warning("meeting_conflict_detected", user_id=str(organizer.id))
             # We allow conflict for now but could warn or block

        meeting = Meeting(
            organization_id=organizer.organization_id,
            organized_by=organizer.id,
            title=data.title,
            description=data.description,
            start_time=data.start_time,
            end_time=data.end_time,
            timezone=data.timezone,
            location=data.location,
            meeting_link=data.meeting_link,
            meeting_type=data.meeting_type or "online",
            status="scheduled"
        )
        self.db.add(meeting)
        await self.db.flush()

        # Add organizer as participant
        organizer_participant = MeetingParticipant(
            meeting_id=meeting.id,
            user_id=organizer.id,
            email=organizer.email,
            is_required=True,
            response_status="accepted",
            responded_at=datetime.now(timezone.utc)
        )
        self.db.add(organizer_participant)

        # Add other participants
        for p in data.participants:
            # Prevent adding organizer twice
            if p.user_id == organizer.id or p.email == organizer.email:
                continue

            participant = MeetingParticipant(
                meeting_id=meeting.id,
                user_id=p.user_id,
                email=p.email,
                is_required=p.is_required,
                response_status="pending"
            )
            self.db.add(participant)

        await self.db.commit()
        await self.db.refresh(meeting)
        
        # Load relationships
        meeting = await self.get_meeting(meeting.id)
        
        # Trigger notification
        await self._notify_participants(meeting, "created")
        
        return meeting

    async def update_meeting(self, meeting_id: UUID, data: MeetingUpdate, user: User) -> Meeting:
        """Update a meeting."""
        meeting = await self.get_meeting(meeting_id)
        
        if meeting.organized_by != user.id:
            raise AuthorizationError("Only the organizer can update the meeting")

        update_dict = data.model_dump(exclude_unset=True)
        for key, value in update_dict.items():
            setattr(meeting, key, value)

        await self.db.commit()
        await self.db.refresh(meeting)
        
        # Trigger notification for update
        await self._notify_participants(meeting, "updated")
        
        return meeting

    async def delete_meeting(self, meeting_id: UUID, user: User) -> None:
        """Cancel/Delete a meeting."""
        meeting = await self.get_meeting(meeting_id)
        
        if meeting.organized_by != user.id:
             raise AuthorizationError("Only the organizer can delete the meeting")
             
        meeting.status = "cancelled"
        await self.db.commit()
        
        # Trigger notification
        await self._notify_participants(meeting, "cancelled")

    async def _notify_participants(self, meeting: Meeting, action: str):
        """Simulate sending notifications to all participants."""
        participants = meeting.participants
        logger.info(
            "meeting_notification_sent",
            meeting_id=str(meeting.id),
            action=action,
            participant_count=len(participants),
            recipients=[p.email for p in participants]
        )
        # In a real system, this would queue Celery tasks for Email/SMS/Push
        for p in participants:
             # Logic to inform people and contractors involved
             logger.debug(f"Notification sent to {p.email} for meeting {action}")

    async def _check_conflicts(self, user_id: UUID, start_time: datetime, end_time: datetime) -> bool:
        """Check if user has overlapping meetings."""
        # Ensure inputs are aware if model is aware
        if start_time.tzinfo is None:
            start_time = start_time.replace(tzinfo=timezone.utc)
        if end_time.tzinfo is None:
            end_time = end_time.replace(tzinfo=timezone.utc)

        query = select(MeetingParticipant).join(Meeting).where(
            MeetingParticipant.user_id == user_id,
            Meeting.status == "scheduled",
            or_(
                and_(Meeting.start_time <= start_time, Meeting.end_time > start_time),
                and_(Meeting.start_time < end_time, Meeting.end_time >= end_time),
                and_(Meeting.start_time >= start_time, Meeting.end_time <= end_time)
            )
        )
        result = await self.db.execute(query)
        return result.first() is not None
