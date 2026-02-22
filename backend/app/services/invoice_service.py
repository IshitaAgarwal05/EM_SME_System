"""
Invoice Service — GST-ready invoice creation, payment recording, and PDF generation.

Auto-posts journal entries on:
  - Invoice creation: Dr AR / Cr Revenue + GST Payable
  - Payment recorded: Dr Bank / Cr AR
  - Invoice void: reversal of creation entry
"""

from __future__ import annotations

import uuid
from datetime import date
from decimal import Decimal
from typing import Any

import structlog
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.invoice import Invoice, InvoiceLineItem, InvoiceNumberSequence, InvoicePayment
from app.services.accounting_service import AccountingService, LineSpec
from app.services.coa_service import CoAService

logger = structlog.get_logger()


class InvoiceService:
    def __init__(self, db: AsyncSession, organization_id: uuid.UUID):
        self.db = db
        self.org_id = organization_id
        self._accounting = AccountingService(db, organization_id)
        self._coa = CoAService(db, organization_id)

    # -----------------------------------------------------------------------
    # Invoice number generation (atomic)
    # -----------------------------------------------------------------------
    async def _next_invoice_number(self) -> str:
        """Atomically increment and return next invoice number string."""
        result = await self.db.execute(
            select(InvoiceNumberSequence).where(
                InvoiceNumberSequence.organization_id == self.org_id
            )
        )
        seq = result.scalar_one_or_none()
        if not seq:
            seq = InvoiceNumberSequence(organization_id=self.org_id, prefix="INV", last_number=0)
            self.db.add(seq)
            await self.db.flush()

        seq.last_number += 1
        await self.db.flush()
        return f"{seq.prefix}-{seq.last_number:04d}"

    # -----------------------------------------------------------------------
    # Create Invoice
    # -----------------------------------------------------------------------
    async def create_invoice(
        self,
        client_name: str,
        issue_date: date,
        line_items: list[dict],
        client_email: str | None = None,
        client_gstin: str | None = None,
        client_address: str | None = None,
        due_date: date | None = None,
        notes: str | None = None,
        terms: str | None = None,
        currency: str = "INR",
        created_by: uuid.UUID | None = None,
        auto_post: bool = True,
    ) -> Invoice:
        """
        Create an invoice and (optionally) auto-post the journal entry.

        line_items: list of {
          "description": str,
          "quantity": Decimal,
          "unit_price": Decimal,
          "cgst_rate": Decimal,   # e.g. 9 for 9%
          "sgst_rate": Decimal,
          "igst_rate": Decimal,
          "account_id": UUID | None  (defaults to 4010 Service Revenue)
        }
        """
        inv_number = await self._next_invoice_number()

        # Build line item objects and totals
        subtotal = Decimal("0")
        total_cgst = Decimal("0")
        total_sgst = Decimal("0")
        total_igst = Decimal("0")
        db_lines: list[InvoiceLineItem] = []

        for item in line_items:
            qty = Decimal(str(item.get("quantity", 1)))
            unit_price = Decimal(str(item["unit_price"]))
            amount = (qty * unit_price).quantize(Decimal("0.01"))

            cgst_rate = Decimal(str(item.get("cgst_rate", 0)))
            sgst_rate = Decimal(str(item.get("sgst_rate", 0)))
            igst_rate = Decimal(str(item.get("igst_rate", 0)))

            line_cgst = (amount * cgst_rate / 100).quantize(Decimal("0.01"))
            line_sgst = (amount * sgst_rate / 100).quantize(Decimal("0.01"))
            line_igst = (amount * igst_rate / 100).quantize(Decimal("0.01"))

            subtotal += amount
            total_cgst += line_cgst
            total_sgst += line_sgst
            total_igst += line_igst

            db_lines.append(
                InvoiceLineItem(
                    description=item["description"],
                    quantity=qty,
                    unit_price=unit_price,
                    amount=amount,
                    cgst_rate=cgst_rate,
                    sgst_rate=sgst_rate,
                    igst_rate=igst_rate,
                    account_id=item.get("account_id"),
                    item_id=item.get("item_id"),
                )
            )

        total_tax = total_cgst + total_sgst + total_igst
        total_amount = subtotal + total_tax

        invoice = Invoice(
            organization_id=self.org_id,
            invoice_number=inv_number,
            client_name=client_name,
            client_email=client_email,
            client_gstin=client_gstin,
            client_address=client_address,
            issue_date=issue_date,
            due_date=due_date,
            subtotal=subtotal,
            cgst_amount=total_cgst,
            sgst_amount=total_sgst,
            igst_amount=total_igst,
            total_amount=total_amount,
            paid_amount=Decimal("0"),
            status="draft",
            notes=notes,
            terms=terms,
            currency=currency,
            created_by=created_by,
        )
        self.db.add(invoice)
        await self.db.flush()

        for line in db_lines:
            line.invoice_id = invoice.id
            self.db.add(line)

        await self.db.flush()

        # Auto-post journal entry
        if auto_post and total_amount > 0:
            journal_lines = await self._build_invoice_journal_lines(
                total_amount, subtotal, total_cgst, total_sgst, total_igst
            )
            entry = await self._accounting.post_journal_entry(
                entry_date=issue_date,
                description=f"Invoice {inv_number} — {client_name}",
                lines=journal_lines,
                reference=inv_number,
                source="invoice",
                source_id=invoice.id,
                created_by=created_by,
            )
            invoice.journal_entry_id = entry.id
            invoice.status = "sent"

        # ── Auto-deduct inventory for linked line items ─────────────
        items_with_id = [(li, item) for li, item in zip(db_lines, line_items) if item.get("item_id")]
        if items_with_id:
            from app.services.inventory_service import InventoryService
            inv_svc = InventoryService(self.db, self.org_id)
            for db_line, raw_item in items_with_id:
                try:
                    await inv_svc.adjust_stock(
                        item_id=raw_item["item_id"],
                        movement_type="sale_out",
                        qty=db_line.quantity,
                        movement_date=issue_date,
                        unit_cost=db_line.unit_price,
                        reference_type="invoice",
                        reference_id=invoice.id,
                        notes=f"Invoice {inv_number}",
                    )
                except Exception as e:
                    logger.warning("stock_deduct_failed", item_id=str(raw_item["item_id"]), error=str(e))

        await self.db.commit()
        await self.db.refresh(invoice)
        logger.info("invoice_created", number=inv_number, total=str(total_amount))
        return invoice

    # -----------------------------------------------------------------------
    # Record Payment
    # -----------------------------------------------------------------------
    async def record_payment(
        self,
        invoice_id: uuid.UUID,
        amount: Decimal,
        payment_date: date,
        payment_mode: str | None = None,
        reference: str | None = None,
        notes: str | None = None,
        received_by: uuid.UUID | None = None,
    ) -> InvoicePayment:
        """
        Record a payment receipt against an invoice.
        Auto-posts: Dr Bank / Cr Accounts Receivable.
        Updates invoice.paid_amount and status.
        """
        result = await self.db.execute(
            select(Invoice).where(
                Invoice.id == invoice_id,
                Invoice.organization_id == self.org_id,
            )
        )
        invoice = result.scalar_one_or_none()
        if not invoice:
            raise ValueError("Invoice not found")
        if invoice.status == "void":
            raise ValueError("Cannot record payment on a voided invoice")
        if invoice.status == "paid":
            raise ValueError("Invoice is already fully paid")

        outstanding = invoice.total_amount - invoice.paid_amount
        if amount > outstanding:
            raise ValueError(
                f"Payment amount {amount} exceeds outstanding balance {outstanding}"
            )

        # Post journal: Dr Bank, Cr AR
        bank_acct = await self._coa.get_account_by_code("1020")
        ar_acct = await self._coa.get_account_by_code("1100")
        if not bank_acct or not ar_acct:
            raise ValueError(
                "Default Bank (1020) or AR (1100) account not found. "
                "Run POST /accounting/coa/seed first."
            )

        entry = await self._accounting.post_journal_entry(
            entry_date=payment_date,
            description=f"Payment received — {invoice.invoice_number}",
            lines=[
                LineSpec(account_id=bank_acct.id, debit=amount),
                LineSpec(account_id=ar_acct.id, credit=amount),
            ],
            reference=invoice.invoice_number,
            source="payment",
            source_id=invoice.id,
            created_by=received_by,
        )

        payment = InvoicePayment(
            invoice_id=invoice_id,
            organization_id=self.org_id,
            payment_date=payment_date,
            amount=amount,
            payment_mode=payment_mode,
            reference=reference,
            notes=notes,
            journal_entry_id=entry.id,
            received_by=received_by,
        )
        self.db.add(payment)

        # Update invoice totals and status
        invoice.paid_amount += amount
        new_outstanding = invoice.total_amount - invoice.paid_amount
        if new_outstanding <= 0:
            invoice.status = "paid"
        else:
            invoice.status = "partial"

        await self.db.commit()
        logger.info("invoice_payment_recorded", invoice_id=str(invoice_id), amount=str(amount))
        return payment

    # -----------------------------------------------------------------------
    # Void Invoice
    # -----------------------------------------------------------------------
    async def void_invoice(
        self, invoice_id: uuid.UUID, voided_by: uuid.UUID | None = None
    ) -> Invoice:
        """Void an invoice by reversing its journal entry."""
        result = await self.db.execute(
            select(Invoice).where(
                Invoice.id == invoice_id,
                Invoice.organization_id == self.org_id,
            )
        )
        invoice = result.scalar_one_or_none()
        if not invoice:
            raise ValueError("Invoice not found")
        if invoice.status == "void":
            raise ValueError("Invoice is already voided")
        if invoice.paid_amount > 0:
            raise ValueError("Cannot void a partially/fully paid invoice")

        if invoice.journal_entry_id:
            await self._accounting.void_entry(invoice.journal_entry_id, voided_by=voided_by)

        invoice.status = "void"
        await self.db.commit()
        logger.info("invoice_voided", invoice_id=str(invoice_id))
        return invoice

    # -----------------------------------------------------------------------
    # List / Get
    # -----------------------------------------------------------------------
    async def list_invoices(
        self,
        page: int = 1,
        page_size: int = 50,
        status: str | None = None,
    ) -> dict[str, Any]:
        from sqlalchemy import func
        q = (
            select(Invoice)
            .where(Invoice.organization_id == self.org_id)
            .order_by(Invoice.issue_date.desc())
        )
        if status:
            q = q.where(Invoice.status == status)

        count_q = select(func.count()).select_from(q.subquery())
        total = (await self.db.execute(count_q)).scalar() or 0

        q = q.options(selectinload(Invoice.line_items)).offset((page - 1) * page_size).limit(page_size)
        invoices = (await self.db.execute(q)).scalars().all()

        return {
            "total": total,
            "page": page,
            "page_size": page_size,
            "items": [_invoice_to_dict(inv) for inv in invoices],
        }

    async def get_invoice(self, invoice_id: uuid.UUID) -> Invoice:
        result = await self.db.execute(
            select(Invoice)
            .options(selectinload(Invoice.line_items), selectinload(Invoice.payments))
            .where(Invoice.id == invoice_id, Invoice.organization_id == self.org_id)
        )
        inv = result.scalar_one_or_none()
        if not inv:
            raise ValueError("Invoice not found")
        return inv

    # -----------------------------------------------------------------------
    # PDF generation (basic, using reportlab if available)
    # -----------------------------------------------------------------------
    async def generate_pdf(self, invoice_id: uuid.UUID) -> bytes:
        """
        Generate a PDF invoice. Requires `reportlab` to be installed.
        Falls back to a clear error if not available.
        """
        invoice = await self.get_invoice(invoice_id)
        try:
            return _render_pdf(invoice)
        except ImportError:
            raise RuntimeError(
                "reportlab is not installed. Run: pip install reportlab"
            )

    # -----------------------------------------------------------------------
    # Internal: build journal lines for invoice creation
    # -----------------------------------------------------------------------
    async def _build_invoice_journal_lines(
        self,
        total_amount: Decimal,
        subtotal: Decimal,
        cgst: Decimal,
        sgst: Decimal,
        igst: Decimal,
    ) -> list[LineSpec]:
        ar = await self._coa.get_account_by_code("1100")
        revenue = await self._coa.get_account_by_code("4010")
        cgst_acc = await self._coa.get_account_by_code("2110")
        sgst_acc = await self._coa.get_account_by_code("2120")
        igst_acc = await self._coa.get_account_by_code("2130")

        if not ar or not revenue:
            raise ValueError(
                "Accounts Receivable (1100) or Revenue (4010) not found. "
                "Run POST /accounting/coa/seed first."
            )

        lines: list[LineSpec] = [
            LineSpec(account_id=ar.id, debit=total_amount, description="Accounts Receivable"),
            LineSpec(account_id=revenue.id, credit=subtotal, description="Revenue"),
        ]
        if cgst > 0 and cgst_acc:
            lines.append(LineSpec(account_id=cgst_acc.id, credit=cgst, description="CGST Payable"))
        if sgst > 0 and sgst_acc:
            lines.append(LineSpec(account_id=sgst_acc.id, credit=sgst, description="SGST Payable"))
        if igst > 0 and igst_acc:
            lines.append(LineSpec(account_id=igst_acc.id, credit=igst, description="IGST Payable"))

        return lines


# ---------------------------------------------------------------------------
# PDF Renderer (reportlab)
# ---------------------------------------------------------------------------
def _render_pdf(invoice: Invoice) -> bytes:
    """Render a simple A4 invoice PDF using reportlab."""
    from io import BytesIO
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.lib.units import cm
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer

    buf = BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, topMargin=2 * cm, bottomMargin=2 * cm)
    styles = getSampleStyleSheet()
    story = []

    # Header
    story.append(Paragraph(f"<b>INVOICE</b>", styles["Title"]))
    story.append(Paragraph(f"Invoice No: {invoice.invoice_number}", styles["Normal"]))
    story.append(Paragraph(f"Date: {invoice.issue_date}", styles["Normal"]))
    if invoice.due_date:
        story.append(Paragraph(f"Due Date: {invoice.due_date}", styles["Normal"]))
    story.append(Spacer(1, 0.5 * cm))

    # Client
    story.append(Paragraph(f"<b>Bill To:</b> {invoice.client_name}", styles["Normal"]))
    if invoice.client_gstin:
        story.append(Paragraph(f"GSTIN: {invoice.client_gstin}", styles["Normal"]))
    story.append(Spacer(1, 0.5 * cm))

    # Line items table
    header = ["#", "Description", "Qty", "Unit Price", "CGST%", "SGST%", "IGST%", "Amount"]
    rows = [header]
    for i, item in enumerate(invoice.line_items, 1):
        rows.append([
            str(i),
            item.description,
            str(item.quantity),
            f"₹{item.unit_price:,.2f}",
            f"{item.cgst_rate}%",
            f"{item.sgst_rate}%",
            f"{item.igst_rate}%",
            f"₹{item.amount:,.2f}",
        ])

    t = Table(rows, repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#cc0000")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f9f9f9")]),
    ]))
    story.append(t)
    story.append(Spacer(1, 0.5 * cm))

    # Totals
    totals = [
        ["Subtotal", f"₹{invoice.subtotal:,.2f}"],
        ["CGST", f"₹{invoice.cgst_amount:,.2f}"],
        ["SGST", f"₹{invoice.sgst_amount:,.2f}"],
        ["IGST", f"₹{invoice.igst_amount:,.2f}"],
        ["TOTAL", f"₹{invoice.total_amount:,.2f}"],
        ["Paid", f"₹{invoice.paid_amount:,.2f}"],
        ["Outstanding", f"₹{invoice.outstanding_amount:,.2f}"],
    ]
    t2 = Table(totals, colWidths=[10 * cm, 5 * cm])
    t2.setStyle(TableStyle([
        ("ALIGN", (1, 0), (1, -1), "RIGHT"),
        ("FONTNAME", (0, -3), (-1, -3), "Helvetica-Bold"),
        ("LINEABOVE", (0, -3), (-1, -3), 1, colors.black),
        ("GRID", (0, 0), (-1, -1), 0.3, colors.lightgrey),
    ]))
    story.append(t2)

    if invoice.notes:
        story.append(Spacer(1, 0.5 * cm))
        story.append(Paragraph(f"<b>Notes:</b> {invoice.notes}", styles["Normal"]))

    doc.build(story)
    return buf.getvalue()


# ---------------------------------------------------------------------------
# Serialisation helper
# ---------------------------------------------------------------------------
def _invoice_to_dict(inv: Invoice) -> dict[str, Any]:
    return {
        "id": str(inv.id),
        "invoice_number": inv.invoice_number,
        "client_name": inv.client_name,
        "client_email": inv.client_email,
        "client_gstin": inv.client_gstin,
        "issue_date": str(inv.issue_date),
        "due_date": str(inv.due_date) if inv.due_date else None,
        "subtotal": float(inv.subtotal),
        "cgst_amount": float(inv.cgst_amount),
        "sgst_amount": float(inv.sgst_amount),
        "igst_amount": float(inv.igst_amount),
        "total_amount": float(inv.total_amount),
        "paid_amount": float(inv.paid_amount),
        "outstanding_amount": float(inv.outstanding_amount),
        "status": inv.status,
        "currency": inv.currency,
        "line_items": [
            {
                "description": li.description,
                "quantity": float(li.quantity),
                "unit_price": float(li.unit_price),
                "amount": float(li.amount),
                "cgst_rate": float(li.cgst_rate),
                "sgst_rate": float(li.sgst_rate),
                "igst_rate": float(li.igst_rate),
            }
            for li in (inv.line_items or [])
        ],
        "journal_entry_id": str(inv.journal_entry_id) if inv.journal_entry_id else None,
        "created_at": str(inv.created_at),
    }
