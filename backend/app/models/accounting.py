"""
Double-Entry Accounting Engine models.

Tables:
  accounts         — hierarchical Chart of Accounts
  journal_entries  — entry header (must be balanced)
  journal_lines    — individual debit/credit lines
  financial_years  — lock control per org per year
"""

import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.organization import Organization
    from app.models.user import User


# ---------------------------------------------------------------------------
# Account Types (Schedule III aligned)
# ---------------------------------------------------------------------------
ACCOUNT_TYPES = {
    "asset": ["current_asset", "non_current_asset", "bank_cash"],
    "liability": ["current_liability", "non_current_liability"],
    "equity": ["equity"],
    "income": ["revenue", "other_income"],
    "expense": ["cogs", "employee_expense", "depreciation", "finance_cost", "other_expense"],
}


class Account(Base, UUIDMixin, TimestampMixin):
    """
    Hierarchical Chart of Accounts entry.
    Each org gets a standard seeded set; custom accounts can be added by users.
    """

    __tablename__ = "accounts"
    __table_args__ = (
        UniqueConstraint("organization_id", "code", name="uq_accounts_org_code"),
    )

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    parent_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("accounts.id", ondelete="RESTRICT"),
        nullable=True,
        index=True,
    )
    code: Mapped[str] = mapped_column(String(20), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    # "asset" | "liability" | "equity" | "income" | "expense"
    account_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    # More granular sub-type, e.g. "current_asset", "revenue", "cogs"
    sub_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    # System accounts cannot be deleted/renamed arbitrarily
    is_system: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, index=True)

    # Self-referential parent/children relationship
    parent: Mapped["Account | None"] = relationship(
        "Account", back_populates="children", remote_side="Account.id"
    )
    children: Mapped[list["Account"]] = relationship(
        "Account", back_populates="parent", cascade="all, delete-orphan"
    )
    journal_lines: Mapped[list["JournalLine"]] = relationship(
        "JournalLine", back_populates="account"
    )

    def __repr__(self) -> str:
        return f"<Account {self.code} {self.name}>"


class JournalEntry(Base, UUIDMixin, TimestampMixin):
    """
    Journal Entry header. All business events that affect books must
    produce a balanced journal entry (sum debits == sum credits).

    Status flow:  draft → posted → voided
    Only 'posted' entries are included in financial reports.
    """

    __tablename__ = "journal_entries"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    entry_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    reference: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    # Source that auto-created this entry: "invoice", "payment", "inventory", "manual"
    source: Mapped[str] = mapped_column(String(50), default="manual", nullable=False)
    # Reference to the source object (invoice_id, payment_id, etc.)
    source_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True, index=True)
    # "draft" | "posted" | "voided"
    status: Mapped[str] = mapped_column(String(20), default="draft", nullable=False, index=True)
    # If this entry is a voiding reversal, points to the original entry
    reversed_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("journal_entries.id", ondelete="SET NULL"),
        nullable=True,
    )
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    fiscal_year: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)

    lines: Mapped[list["JournalLine"]] = relationship(
        "JournalLine", back_populates="entry", cascade="all, delete-orphan"
    )
    reversal: Mapped["JournalEntry | None"] = relationship(
        "JournalEntry", remote_side="JournalEntry.id", foreign_keys=[reversed_by]
    )

    def __repr__(self) -> str:
        return f"<JournalEntry {self.entry_date} {self.description[:30]}>"


class JournalLine(Base, UUIDMixin):
    """
    Individual debit or credit line within a journal entry.
    Exactly one of (debit, credit) must be non-zero for each line.
    """

    __tablename__ = "journal_lines"
    __table_args__ = (
        CheckConstraint(
            "(debit > 0 AND credit = 0) OR (credit > 0 AND debit = 0)",
            name="ck_journal_lines_debit_or_credit",
        ),
    )

    entry_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("journal_entries.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    account_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("accounts.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    debit: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False, default=Decimal("0"))
    credit: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False, default=Decimal("0"))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    entry: Mapped["JournalEntry"] = relationship("JournalEntry", back_populates="lines")
    account: Mapped["Account"] = relationship("Account", back_populates="journal_lines")

    def __repr__(self) -> str:
        side = f"Dr {self.debit}" if self.debit else f"Cr {self.credit}"
        return f"<JournalLine {self.account_id} {side}>"


class FinancialYear(Base, UUIDMixin, TimestampMixin):
    """
    Financial year lock control. Once locked, no new journal entries
    may be posted for that year.
    """

    __tablename__ = "financial_years"
    __table_args__ = (
        UniqueConstraint("organization_id", "year", name="uq_financial_years_org_year"),
    )

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    is_locked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    locked_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    locked_at: Mapped[datetime | None] = mapped_column(nullable=True)

    def __repr__(self) -> str:
        return f"<FinancialYear {self.year} locked={self.is_locked}>"
