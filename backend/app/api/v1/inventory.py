"""Inventory API endpoints."""

import uuid
from datetime import date
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated

from app.dependencies import CurrentUser, get_db
from app.services.inventory_service import InventoryService

router = APIRouter(prefix="/inventory", tags=["Inventory"])


class CreateItemRequest(BaseModel):
    sku: str
    name: str
    cost_price: Decimal = Field(..., ge=0)
    sale_price: Decimal = Field(..., ge=0)
    unit: str = "pcs"
    description: str | None = None
    reorder_level: Decimal = Field(default=Decimal("0"), ge=0)
    cgst_rate: Decimal = Field(default=Decimal("0"), ge=0, le=100)
    sgst_rate: Decimal = Field(default=Decimal("0"), ge=0, le=100)
    igst_rate: Decimal = Field(default=Decimal("0"), ge=0, le=100)


class AdjustStockRequest(BaseModel):
    item_id: uuid.UUID
    movement_type: str = Field(..., description="purchase_in | sale_out | adjustment | return_in | return_out")
    qty: Decimal = Field(..., description="Always positive; direction determined by movement_type")
    movement_date: date
    unit_cost: Decimal | None = None
    reference_type: str | None = None
    reference_id: uuid.UUID | None = None
    notes: str | None = None


@router.get("/items")
async def list_items(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: CurrentUser,
    active_only: bool = Query(default=True),
):
    svc = InventoryService(db, current_user.organization_id)
    return await svc.list_items(active_only=active_only)


@router.post("/items", status_code=201)
async def create_item(
    body: CreateItemRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: CurrentUser,
):
    svc = InventoryService(db, current_user.organization_id)
    item = await svc.create_item(
        sku=body.sku,
        name=body.name,
        cost_price=body.cost_price,
        sale_price=body.sale_price,
        unit=body.unit,
        description=body.description,
        reorder_level=body.reorder_level,
        cgst_rate=body.cgst_rate,
        sgst_rate=body.sgst_rate,
        igst_rate=body.igst_rate,
    )
    from app.services.inventory_service import _item_to_dict
    return _item_to_dict(item)


@router.get("/items/{item_id}/ledger")
async def get_stock_ledger(
    item_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: CurrentUser,
):
    svc = InventoryService(db, current_user.organization_id)
    try:
        return await svc.get_stock_ledger(item_id)
    except ValueError as e:
        raise HTTPException(404, str(e))


@router.get("/low-stock")
async def get_low_stock(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: CurrentUser,
):
    """Items at or below reorder level."""
    svc = InventoryService(db, current_user.organization_id)
    return await svc.get_low_stock()


@router.post("/movements", status_code=201)
async def record_movement(
    body: AdjustStockRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: CurrentUser,
):
    svc = InventoryService(db, current_user.organization_id)
    try:
        movement = await svc.adjust_stock(
            item_id=body.item_id,
            movement_type=body.movement_type,
            qty=body.qty,
            movement_date=body.movement_date,
            unit_cost=body.unit_cost,
            reference_type=body.reference_type,
            reference_id=body.reference_id,
            notes=body.notes,
        )
    except ValueError as e:
        raise HTTPException(400, str(e))
    return {
        "id": str(movement.id),
        "item_id": str(movement.item_id),
        "movement_type": movement.movement_type,
        "qty": float(movement.qty),
        "date": str(movement.movement_date),
    }


@router.get("/sales-summary")
async def get_sales_summary(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: CurrentUser,
):
    """Per-item sales summary from sale_out inventory movements."""
    from sqlalchemy import select, func, case
    from app.models.inventory import InventoryMovement, Item as ItemModel

    q = (
        select(
            ItemModel.id,
            ItemModel.sku,
            ItemModel.name,
            ItemModel.unit,
            ItemModel.sale_price,
            ItemModel.current_qty,
            func.coalesce(func.sum(
                case((InventoryMovement.movement_type == "sale_out", InventoryMovement.qty), else_=0)
            ), 0).label("total_sold_qty"),
            func.coalesce(func.sum(
                case(
                    (InventoryMovement.movement_type == "sale_out",
                     InventoryMovement.qty * InventoryMovement.unit_cost),
                    else_=0
                )
            ), 0).label("total_sale_value"),
            func.max(
                case((InventoryMovement.movement_type == "sale_out", InventoryMovement.movement_date), else_=None)
            ).label("last_sale_date"),
        )
        .outerjoin(InventoryMovement, InventoryMovement.item_id == ItemModel.id)
        .where(
            ItemModel.organization_id == current_user.organization_id,
            ItemModel.is_active == True,
        )
        .group_by(
            ItemModel.id, ItemModel.sku, ItemModel.name,
            ItemModel.unit, ItemModel.sale_price, ItemModel.current_qty
        )
        .order_by(func.coalesce(func.sum(
            case((InventoryMovement.movement_type == "sale_out", InventoryMovement.qty), else_=0)
        ), 0).desc())
    )
    rows = (await db.execute(q)).all()
    return [
        {
            "item_id": str(r.id),
            "sku": r.sku,
            "name": r.name,
            "unit": r.unit,
            "sale_price": float(r.sale_price),
            "current_stock": float(r.current_qty),
            "total_sold_qty": float(r.total_sold_qty),
            "total_sale_value": float(r.total_sale_value),
            "last_sale_date": str(r.last_sale_date) if r.last_sale_date else None,
        }
        for r in rows
    ]


