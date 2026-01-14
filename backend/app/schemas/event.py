"""
Pydantic schemas for Event and Category models.
"""

from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, Field


# Event Schemas
class EventBase(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    description: str | None = None
    event_type: str = Field(default="event")  # event, product, unit, project
    start_date: date | None = None
    end_date: date | None = None
    budget: float | None = None
    status: str = Field(default="active")  # active, completed, cancelled


class EventCreate(EventBase):
    pass


class EventUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    event_type: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    budget: float | None = None
    status: str | None = None


class EventResponse(EventBase):
    id: UUID
    organization_id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Category Schemas
class CategoryBase(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    category_type: str  # expense, income
    color: str | None = None
    icon: str | None = None


class CategoryCreate(CategoryBase):
    pass


class CategoryUpdate(BaseModel):
    name: str | None = None
    category_type: str | None = None
    color: str | None = None
    icon: str | None = None


class CategoryResponse(CategoryBase):
    id: UUID
    organization_id: UUID
    is_default: bool
    created_at: datetime

    class Config:
        from_attributes = True


class CategoryBulkCreate(BaseModel):
    categories: list[CategoryCreate]
