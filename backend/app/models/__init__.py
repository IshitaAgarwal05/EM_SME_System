"""
Import all models for Alembic migrations.
This file ensures all models are discovered by Alembic.
"""

from app.db.base import Base
from app.models.event import Category, Event
from app.models.financial import (
    BankAccount,
    Contractor,
    Payment,
    TaskPaymentLink,
    Transaction,
)
from app.models.invitation import Invitation
from app.models.meeting import Meeting, MeetingParticipant
from app.models.organization import Organization
from app.models.system import Announcement, AuditLog, FileUpload, Notification, Reminder
from app.models.task import Task, TaskAssignment, TaskComment
from app.models.user import RefreshToken, User

# New Accounting Extension Models
from app.models.accounting import Account, FinancialYear, JournalEntry, JournalLine
from app.models.inventory import InventoryMovement, Item
from app.models.invoice import Invoice, InvoiceLineItem, InvoiceNumberSequence, InvoicePayment

__all__ = [
    "Base",
    "Organization",
    "User",
    "RefreshToken",
    "Invitation",
    "Task",
    "TaskAssignment",
    "TaskComment",
    "BankAccount",
    "Transaction",
    "Contractor",
    "Payment",
    "TaskPaymentLink",
    "Meeting",
    "MeetingParticipant",
    "Reminder",
    "FileUpload",
    "AuditLog",
    "Event",
    "Category",
    "Announcement",
    "Notification",
    # Accounting Extension
    "Account",
    "JournalEntry",
    "JournalLine",
    "FinancialYear",
    "Invoice",
    "InvoiceLineItem",
    "InvoicePayment",
    "InvoiceNumberSequence",
    "Item",
    "InventoryMovement",
]
