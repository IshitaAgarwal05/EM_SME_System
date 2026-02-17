"""
Lightweight Inventory models.

Tables:
  items                — SKU catalog
  inventory_movements  — stock ledger (every in/out)
"""

import uuid
from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Date, ForeignKey, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDMixin


MOVEMENT_TYPES = (
    "purchase_in",   # stock received from purchase
    "sale_out",      # stock dispatched on invoice
    "adjustment",    # manual count correction
    "return_in",     # customer return
    "return_out",    # return to vendor
)


class Item(Base, UUIDMixin, TimestampMixin):
    """Sellable/storable item in the catalogue."""

    __tablename__ = "items"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    sku: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    unit: Mapped[str] = mapped_column(String(30), default="pcs", nullable=False)

    # Costing
    cost_price: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False, default=Decimal("0"))
    sale_price: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False, default=Decimal("0"))

    # Stock tracking
    current_qty: Mapped[Decimal] = mapped_column(Numeric(10, 3), nullable=False, default=Decimal("0"))
    reorder_level: Mapped[Decimal] = mapped_column(Numeric(10, 3), nullable=False, default=Decimal("0"))

    # GST rates for this item
    cgst_rate: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=Decimal("0"), nullable=False)
    sgst_rate: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=Decimal("0"), nullable=False)
    igst_rate: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=Decimal("0"), nullable=False)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, index=True)

    # Link to CoA account for COGS postings
    cogs_account_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("accounts.id", ondelete="SET NULL"),
        nullable=True,
    )
    inventory_account_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("accounts.id", ondelete="SET NULL"),
        nullable=True,
    )

    movements: Mapped[list["InventoryMovement"]] = relationship(
        "InventoryMovement", back_populates="item", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Item {self.sku} {self.name}>"


class InventoryMovement(Base, UUIDMixin, TimestampMixin):
    """
    Every stock change is recorded here (stock ledger).
    qty is always positive; movement_type indicates direction.
    """

    __tablename__ = "inventory_movements"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    item_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("items.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    movement_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    # purchase_in | sale_out | adjustment | return_in | return_out
    movement_type: Mapped[str] = mapped_column(String(30), nullable=False, index=True)
    qty: Mapped[Decimal] = mapped_column(Numeric(10, 3), nullable=False)
    unit_cost: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False, default=Decimal("0"))

    # Reference to source document
    reference_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    reference_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True, index=True)

    # Auto-posted journal entry (COGS on sale_out)
    journal_entry_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("journal_entries.id", ondelete="SET NULL"),
        nullable=True,
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    item: Mapped["Item"] = relationship("Item", back_populates="movements")

    def __repr__(self) -> str:
        return f"<InventoryMovement {self.movement_type} qty={self.qty}>"
