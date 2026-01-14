
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field
from app.schemas.common import TimestampSchema

class AnnouncementBase(BaseModel):
    title: str = Field(min_length=1, max_length=500)
    content: str
    target_role: str | None = None
    target_user_ids: list[str] | None = None
    target_groups: list[str] | None = None  # ["all", "my_team", "contractors"]

class AnnouncementCreate(AnnouncementBase):
    pass

class AnnouncementResponse(AnnouncementBase):
    id: UUID
    organization_id: UUID
    created_by_id: UUID
    created_at: datetime

    class Config:
        from_attributes = True

class FileUploadResponse(BaseModel):
    id: UUID
    organization_id: UUID
    uploaded_by: UUID
    filename: str
    file_type: str | None = None
    file_size: int | None = None
    processing_status: str
    rows_imported: int | None = None
    error_message: str | None = None
    created_at: datetime

    class Config:
        from_attributes = True

class ReminderCreate(BaseModel):
    reminder_type: str
    related_entity_id: UUID
    scheduled_for: datetime
    message: str

class ReminderResponse(TimestampSchema):
    id: UUID
    organization_id: UUID
    reminder_type: str
    related_entity_id: UUID
    scheduled_for: datetime
    message: str
    sent: bool
    sent_at: datetime | None = None

    class Config:
        from_attributes = True
