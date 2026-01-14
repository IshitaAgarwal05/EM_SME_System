"""
Meeting and scheduling Pydantic schemas.
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, EmailStr

from app.schemas.common import TimestampSchema


class MeetingParticipantBase(BaseModel):
    """Base schema for meeting participant."""
    email: EmailStr | None = None
    user_id: UUID | None = None
    is_required: bool = True


class MeetingParticipantResponse(MeetingParticipantBase):
    """Schema for participant response."""
    response_status: str = "pending"
    responded_at: datetime | None = None

    class Config:
        from_attributes = True


class MeetingBase(BaseModel):
    """Base meeting schema."""
    title: str = Field(min_length=1, max_length=500)
    description: str | None = None
    start_time: datetime
    end_time: datetime
    timezone: str = "Asia/Kolkata"
    location: str | None = None
    meeting_link: str | None = None
    meeting_type: str | None = Field(default="online", pattern="^(online|in_person|phone)$")


class MeetingCreate(MeetingBase):
    """Schema for creating a meeting."""
    participants: list[MeetingParticipantBase] = Field(default_factory=list)
    agenda: str | None = None


class MeetingUpdate(BaseModel):
    """Schema for updating a meeting."""
    title: str | None = Field(default=None, min_length=1, max_length=500)
    description: str | None = None
    start_time: datetime | None = None
    end_time: datetime | None = None
    timezone: str | None = None
    location: str | None = None
    meeting_link: str | None = None
    status: str | None = Field(default=None, pattern="^(scheduled|cancelled|completed)$")
    agenda: str | None = None
    notes: str | None = None


class MeetingResponse(MeetingBase, TimestampSchema):
    """Schema for meeting response."""
    id: UUID
    organization_id: UUID
    status: str
    organized_by: UUID
    participants: list[MeetingParticipantResponse] = Field(default_factory=list)
    calendar_event_id: str | None
    
    class Config:
        from_attributes = True
