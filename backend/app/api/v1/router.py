"""
Main API v1 router that includes all endpoint routers.
"""

from fastapi import APIRouter

from app.api.v1 import (
    ai,
    analytics,
    announcements,
    auth,
    categories,
    events,
    files,
    financial,
    invitations,
    meetings,
    reminders,
    tasks,
    users,
    accounting,
    invoices,
    inventory,
    aging,
    audit,
    notifications,
    insights,
)

api_router = APIRouter()

# Include all routers
api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(files.router)
api_router.include_router(tasks.router)
api_router.include_router(financial.router)
api_router.include_router(analytics.router)
api_router.include_router(reminders.router)
api_router.include_router(meetings.router)
api_router.include_router(ai.router)
api_router.include_router(announcements.router)
api_router.include_router(events.router)
api_router.include_router(categories.router)
api_router.include_router(invitations.router)

# Accounting Extension
api_router.include_router(accounting.router)
api_router.include_router(invoices.router)
api_router.include_router(inventory.router)
api_router.include_router(aging.router)
api_router.include_router(audit.router)
api_router.include_router(notifications.router)
api_router.include_router(insights.router)
