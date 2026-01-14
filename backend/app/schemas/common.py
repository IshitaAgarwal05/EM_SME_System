"""
Common Pydantic schemas used across the application.
"""

from datetime import datetime
from typing import Generic, TypeVar
from uuid import UUID

from pydantic import BaseModel, Field

T = TypeVar("T")


class PaginationParams(BaseModel):
    """Pagination parameters for list endpoints."""

    page: int = Field(default=1, ge=1, description="Page number (1-indexed)")
    limit: int = Field(default=50, ge=1, le=100, description="Items per page")

    @property
    def offset(self) -> int:
        """Calculate offset from page and limit."""
        return (self.page - 1) * self.limit


class PaginatedResponse(BaseModel, Generic[T]):
    """Generic paginated response wrapper."""

    items: list[T]
    total: int
    page: int
    limit: int
    pages: int

    @classmethod
    def create(cls, items: list[T], total: int, page: int, limit: int) -> "PaginatedResponse[T]":
        """Create paginated response with calculated pages."""
        pages = (total + limit - 1) // limit  # Ceiling division
        return cls(items=items, total=total, page=page, limit=limit, pages=pages)


class TimestampSchema(BaseModel):
    """Mixin for created_at and updated_at timestamps."""

    created_at: datetime
    updated_at: datetime


class MessageResponse(BaseModel):
    """Simple message response."""

    message: str


class ErrorResponse(BaseModel):
    """Error response schema."""

    error: str
    details: dict = Field(default_factory=dict)
