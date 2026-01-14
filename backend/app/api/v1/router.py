"""
Main API v1 router that includes all endpoint routers.
"""

from fastapi import APIRouter

from app.api.v1 import auth, users, files, tasks, financial, analytics, reminders, meetings, ai, announcements, events, categories

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
