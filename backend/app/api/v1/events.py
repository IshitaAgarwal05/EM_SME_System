"""
Event management API endpoints.
"""

from typing import Annotated
from uuid import UUID

import structlog
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.dependencies import CurrentUser, ManagerUser
from app.models.event import Event
from app.models.financial import Transaction
from app.schemas.event import EventCreate, EventResponse, EventUpdate

router = APIRouter(prefix="/events", tags=["Events"])
logger = structlog.get_logger()


@router.get("", response_model=list[EventResponse])
async def list_events(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: CurrentUser,
):
    """List all events for the organization."""
    query = select(Event).where(
        Event.organization_id == current_user.organization_id
    ).order_by(Event.created_at.desc())
    
    result = await db.execute(query)
    events = result.scalars().all()
    return events


@router.post("", response_model=EventResponse, status_code=status.HTTP_201_CREATED)
async def create_event(
    event_data: EventCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: ManagerUser,
):
    """Create a new event (manager only)."""
    event = Event(
        organization_id=current_user.organization_id,
        **event_data.model_dump()
    )
    db.add(event)
    await db.commit()
    await db.refresh(event)
    return event


@router.get("/{event_id}", response_model=EventResponse)
async def get_event(
    event_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: CurrentUser,
):
    """Get event details."""
    query = select(Event).where(
        Event.id == event_id,
        Event.organization_id == current_user.organization_id
    )
    result = await db.execute(query)
    event = result.scalar_one_or_none()
    
    if not event:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")
    
    return event


@router.patch("/{event_id}", response_model=EventResponse)
async def update_event(
    event_id: UUID,
    event_data: EventUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: ManagerUser,
):
    """Update event (manager only)."""
    query = select(Event).where(
        Event.id == event_id,
        Event.organization_id == current_user.organization_id
    )
    result = await db.execute(query)
    event = result.scalar_one_or_none()
    
    if not event:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")
    
    for field, value in event_data.model_dump(exclude_unset=True).items():
        setattr(event, field, value)
    
    await db.commit()
    await db.refresh(event)
    return event


@router.delete("/{event_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_event(
    event_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: ManagerUser,
):
    """Delete event (manager only)."""
    query = select(Event).where(
        Event.id == event_id,
        Event.organization_id == current_user.organization_id
    )
    result = await db.execute(query)
    event = result.scalar_one_or_none()
    
    if not event:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")
    
    await db.delete(event)
    await db.commit()


@router.get("/{event_id}/analytics")
async def get_event_analytics(
    event_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: CurrentUser,
):
    """Get analytics for a specific event."""
    # Verify event exists and belongs to organization
    event_query = select(Event).where(
        Event.id == event_id,
        Event.organization_id == current_user.organization_id
    )
    event_result = await db.execute(event_query)
    event = event_result.scalar_one_or_none()
    
    if not event:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")
    
    # Get transaction stats
    stats_query = select(
        func.sum(func.case((Transaction.transaction_type == "credit", Transaction.amount), else_=0)).label("total_income"),
        func.sum(func.case((Transaction.transaction_type == "debit", Transaction.amount), else_=0)).label("total_expense"),
        func.count(Transaction.id).label("transaction_count")
    ).where(
        Transaction.event_id == event_id,
        Transaction.organization_id == current_user.organization_id
    )
    stats_result = await db.execute(stats_query)
    stats = stats_result.one()
    
    # Get category breakdown
    category_query = select(
        Transaction.category,
        func.sum(Transaction.amount).label("amount"),
        func.count(Transaction.id).label("count")
    ).where(
        Transaction.event_id == event_id,
        Transaction.organization_id == current_user.organization_id,
        Transaction.category.isnot(None)
    ).group_by(Transaction.category)
    
    category_result = await db.execute(category_query)
    categories = [
        {"category": row.category, "amount": float(row.amount), "count": row.count}
        for row in category_result.all()
    ]
    
    return {
        "event": EventResponse.model_validate(event),
        "total_income": float(stats.total_income or 0),
        "total_expense": float(stats.total_expense or 0),
        "net": float((stats.total_income or 0) - (stats.total_expense or 0)),
        "transaction_count": stats.transaction_count,
        "category_breakdown": categories
    }
