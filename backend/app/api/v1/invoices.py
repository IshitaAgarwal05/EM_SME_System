"""
Invoice API endpoints.
"""

import uuid
from datetime import date
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated, Any

from app.dependencies import CurrentUser, get_db
from app.services.invoice_service import InvoiceService

router = APIRouter(prefix="/invoices", tags=["Invoices"])


class LineItemRequest(BaseModel):
    description: str
    quantity: Decimal = Field(default=Decimal("1"), gt=0)
    unit_price: Decimal = Field(..., gt=0)
    cgst_rate: Decimal = Field(default=Decimal("0"), ge=0)
    sgst_rate: Decimal = Field(default=Decimal("0"), ge=0)
    igst_rate: Decimal = Field(default=Decimal("0"), ge=0)
    account_id: uuid.UUID | None = None
    item_id: uuid.UUID | None = None


class CreateInvoiceRequest(BaseModel):
    client_name: str
    client_email: str | None = None
    client_gstin: str | None = None
    client_address: str | None = None
    issue_date: date
    due_date: date | None = None
    line_items: list[LineItemRequest] = Field(..., min_length=1)
    notes: str | None = None
    terms: str | None = None
    currency: str = "INR"
    auto_post: bool = True


class RecordPaymentRequest(BaseModel):
    amount: Decimal = Field(..., gt=0)
    payment_date: date
    payment_mode: str | None = None
    reference: str | None = None
    notes: str | None = None


@router.get("")
async def list_invoices(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: CurrentUser,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=200),
    status: str | None = Query(default=None),
):
    svc = InvoiceService(db, current_user.organization_id)
    return await svc.list_invoices(page=page, page_size=page_size, status=status)


@router.post("", status_code=201)
async def create_invoice(
    body: CreateInvoiceRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: CurrentUser,
):
    svc = InvoiceService(db, current_user.organization_id)
    try:
        invoice = await svc.create_invoice(
            client_name=body.client_name,
            issue_date=body.issue_date,
            line_items=[item.model_dump() for item in body.line_items],
            client_email=body.client_email,
            client_gstin=body.client_gstin,
            client_address=body.client_address,
            due_date=body.due_date,
            notes=body.notes,
            terms=body.terms,
            currency=body.currency,
            created_by=current_user.id,
            auto_post=body.auto_post,
        )
    except ValueError as e:
        raise HTTPException(422, str(e))
    from app.services.invoice_service import _invoice_to_dict
    return _invoice_to_dict(invoice)


@router.get("/{invoice_id}")
async def get_invoice(
    invoice_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: CurrentUser,
):
    svc = InvoiceService(db, current_user.organization_id)
    try:
        inv = await svc.get_invoice(invoice_id)
    except ValueError as e:
        raise HTTPException(404, str(e))
    from app.services.invoice_service import _invoice_to_dict
    return _invoice_to_dict(inv)


@router.post("/{invoice_id}/payments", status_code=201)
async def record_payment(
    invoice_id: uuid.UUID,
    body: RecordPaymentRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: CurrentUser,
):
    svc = InvoiceService(db, current_user.organization_id)
    try:
        payment = await svc.record_payment(
            invoice_id=invoice_id,
            amount=body.amount,
            payment_date=body.payment_date,
            payment_mode=body.payment_mode,
            reference=body.reference,
            notes=body.notes,
            received_by=current_user.id,
        )
    except ValueError as e:
        raise HTTPException(400, str(e))
    return {
        "id": str(payment.id),
        "invoice_id": str(payment.invoice_id),
        "amount": float(payment.amount),
        "payment_date": str(payment.payment_date),
        "status": "recorded",
    }


@router.post("/{invoice_id}/void")
async def void_invoice(
    invoice_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: CurrentUser,
):
    svc = InvoiceService(db, current_user.organization_id)
    try:
        inv = await svc.void_invoice(invoice_id, voided_by=current_user.id)
    except ValueError as e:
        raise HTTPException(400, str(e))
    return {"invoice_number": inv.invoice_number, "status": inv.status}


@router.get("/{invoice_id}/pdf")
async def download_pdf(
    invoice_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: CurrentUser,
):
    svc = InvoiceService(db, current_user.organization_id)
    try:
        pdf_bytes = await svc.generate_pdf(invoice_id)
    except (ValueError, RuntimeError) as e:
        raise HTTPException(400, str(e))
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=invoice-{invoice_id}.pdf"},
    )
