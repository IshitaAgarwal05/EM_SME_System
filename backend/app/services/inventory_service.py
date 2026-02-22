"""
Inventory service — stock adjustments, ledger, and COGS journal posting.
"""

from __future__ import annotations

import uuid
from datetime import date
from decimal import Decimal
from typing import Any

import structlog
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.inventory import InventoryMovement, Item
from app.services.accounting_service import AccountingService, LineSpec
from app.services.coa_service import CoAService

logger = structlog.get_logger()

# Movements that increase stock
INBOUND = {"purchase_in", "return_in", "adjustment"}
# Movements that decrease stock
OUTBOUND = {"sale_out", "return_out"}


class InventoryService:
    def __init__(self, db: AsyncSession, organization_id: uuid.UUID):
        self.db = db
        self.org_id = organization_id
        self._accounting = AccountingService(db, organization_id)
        self._coa = CoAService(db, organization_id)

    async def create_item(
        self,
        sku: str,
        name: str,
        cost_price: Decimal,
        sale_price: Decimal,
        unit: str = "pcs",
        description: str | None = None,
        reorder_level: Decimal = Decimal("0"),
        cgst_rate: Decimal = Decimal("0"),
        sgst_rate: Decimal = Decimal("0"),
        igst_rate: Decimal = Decimal("0"),
    ) -> Item:
        # Get default CoA accounts
        cogs_acct = await self._coa.get_account_by_code("5010")
        inv_acct = await self._coa.get_account_by_code("1200")

        item = Item(
            organization_id=self.org_id,
            sku=sku,
            name=name,
            description=description,
            unit=unit,
            cost_price=cost_price,
            sale_price=sale_price,
            reorder_level=reorder_level,
            cgst_rate=cgst_rate,
            sgst_rate=sgst_rate,
            igst_rate=igst_rate,
            cogs_account_id=cogs_acct.id if cogs_acct else None,
            inventory_account_id=inv_acct.id if inv_acct else None,
        )
        self.db.add(item)
        await self.db.commit()
        await self.db.refresh(item)
        return item

    async def adjust_stock(
        self,
        item_id: uuid.UUID,
        movement_type: str,
        qty: Decimal,
        movement_date: date,
        unit_cost: Decimal | None = None,
        reference_type: str | None = None,
        reference_id: uuid.UUID | None = None,
        notes: str | None = None,
    ) -> InventoryMovement:
        """
        Record a stock movement and update item.current_qty.
        On sale_out: auto-post COGS journal entry.
        """
        item = await self.db.get(Item, item_id)
        if not item or item.organization_id != self.org_id:
            raise ValueError("Item not found")

        effective_cost = unit_cost if unit_cost is not None else item.cost_price
        journal_entry_id: uuid.UUID | None = None

        # Post COGS journal for outbound movements
        if movement_type in OUTBOUND and item.cogs_account_id and item.inventory_account_id:
            cogs_amount = (qty * effective_cost).quantize(Decimal("0.01"))
            if cogs_amount > 0:
                entry = await self._accounting.post_journal_entry(
                    entry_date=movement_date,
                    description=f"COGS — {item.name} x{qty}",
                    lines=[
                        LineSpec(account_id=item.cogs_account_id, debit=cogs_amount),
                        LineSpec(account_id=item.inventory_account_id, credit=cogs_amount),
                    ],
                    source="inventory",
                    source_id=reference_id,
                    reference=f"{movement_type}/{item.sku}",
                )
                journal_entry_id = entry.id

        # Record movement
        movement = InventoryMovement(
            organization_id=self.org_id,
            item_id=item_id,
            movement_date=movement_date,
            movement_type=movement_type,
            qty=qty,
            unit_cost=effective_cost,
            reference_type=reference_type,
            reference_id=reference_id,
            journal_entry_id=journal_entry_id,
            notes=notes,
        )
        self.db.add(movement)

        # Update item.current_qty
        if movement_type in INBOUND:
            item.current_qty += qty
        elif movement_type in OUTBOUND:
            item.current_qty -= qty
        # adjustment: positive qty = add, negative = subtract
        elif movement_type == "adjustment":
            item.current_qty += qty

        await self.db.commit()
        logger.info("stock_adjusted", item_id=str(item_id), type=movement_type, qty=str(qty))
        return movement

    async def get_stock_ledger(self, item_id: uuid.UUID) -> dict[str, Any]:
        """Full movement history for an item with running balance."""
        item = await self.db.get(Item, item_id)
        if not item or item.organization_id != self.org_id:
            raise ValueError("Item not found")

        result = await self.db.execute(
            select(InventoryMovement)
            .where(InventoryMovement.item_id == item_id)
            .order_by(InventoryMovement.movement_date, InventoryMovement.created_at)
        )
        movements = result.scalars().all()

        running_qty = Decimal("0")
        entries = []
        for m in movements:
            delta = m.qty if m.movement_type in INBOUND else -m.qty
            if m.movement_type == "adjustment":
                delta = m.qty
            running_qty += delta
            entries.append(
                {
                    "date": str(m.movement_date),
                    "type": m.movement_type,
                    "qty_change": float(delta),
                    "running_qty": float(running_qty),
                    "unit_cost": float(m.unit_cost),
                    "notes": m.notes,
                }
            )

        return {
            "item": {
                "id": str(item.id),
                "sku": item.sku,
                "name": item.name,
                "current_qty": float(item.current_qty),
            },
            "movements": entries,
        }

    async def list_items(self, active_only: bool = True) -> list[dict[str, Any]]:
        q = select(Item).where(Item.organization_id == self.org_id)
        if active_only:
            q = q.where(Item.is_active == True)
        q = q.order_by(Item.name)
        result = await self.db.execute(q)
        items = result.scalars().all()
        return [_item_to_dict(i) for i in items]

    async def get_low_stock(self) -> list[dict[str, Any]]:
        """Items where current_qty <= reorder_level."""
        result = await self.db.execute(
            select(Item).where(
                Item.organization_id == self.org_id,
                Item.is_active == True,
                Item.current_qty <= Item.reorder_level,
            ).order_by(Item.current_qty)
        )
        return [_item_to_dict(i) for i in result.scalars().all()]


def _item_to_dict(i: Item) -> dict[str, Any]:
    return {
        "id": str(i.id),
        "sku": i.sku,
        "name": i.name,
        "unit": i.unit,
        "cost_price": float(i.cost_price),
        "sale_price": float(i.sale_price),
        "current_qty": float(i.current_qty),
        "reorder_level": float(i.reorder_level),
        "cgst_rate": float(i.cgst_rate),
        "sgst_rate": float(i.sgst_rate),
        "igst_rate": float(i.igst_rate),
        "is_active": i.is_active,
    }
