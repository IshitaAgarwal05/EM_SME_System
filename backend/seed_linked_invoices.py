"""
Seed inventory-linked invoices.
Each line item carries an item_id -> triggers sale_out stock movement ->
shows up in the Sales Performance tab.

Run from backend/:
    PYTHONPATH=. /home/ishita/.cache/pypoetry/virtualenvs/event-management-backend-hBIlJ0Xn-py3.12/bin/python seed_linked_invoices.py
"""

import asyncio
from datetime import date, timedelta
import random

TODAY = date(2026, 2, 22)

# (client_name, email, days_ago, [(sku, qty)])
ORDERS = [
    ("Reliance Events Pvt Ltd",  "reliance@events.com",  5,  [("SND-001", 2), ("LGT-002", 2)]),
    ("HDFC Bank Corporate",      None,                   12, [("VID-003", 3), ("MIC-009", 1)]),
    ("Tata Consulting Services", "tcs@finance.com",      20, [("DEC-004", 4), ("CAT-005", 80)]),
    ("Wipro Technologies",       "wipro@wipro.com",      28, [("SND-001", 1), ("PRJ-008", 1)]),
    ("Bajaj Auto Ltd",           "bajaj@auto.com",       35, [("TEN-006", 2), ("LGT-002", 3)]),
    ("Priya Events Management",  "priya@events.in",      42, [("FOG-007", 1), ("VID-003", 2)]),
    ("Akash Enterprises",        "akash@enterprise.in",  50, [("CAT-005", 50), ("DEC-004", 2)]),
    ("Mahindra & Mahindra",      "mahindra@corp.in",     58, [("SND-001", 3), ("PRJ-008", 1)]),
    ("Sun Pharma Industries",    "sunpharma@corp.com",   65, [("VID-003", 4), ("MIC-009", 1)]),
    ("Infosys BPM Ltd",          "infosys@bpm.in",       72, [("LGT-002", 2), ("TEN-006", 1)]),
    ("Star Hospitality Ltd",     None,                   80, [("CAT-005", 100), ("DEC-004", 3)]),
    ("Meera Catering Co",        "meera@catering.in",    90, [("CAT-005", 120), ("FOG-007", 1)]),
]


async def seed():
    from app.db.session import AsyncSessionLocal
    from app.models.user import User
    from app.models.organization import Organization
    from app.models.inventory import Item
    from app.services.invoice_service import InvoiceService
    from sqlalchemy import select

    async with AsyncSessionLocal() as db:
        org_res = await db.execute(select(Organization).limit(1))
        org = org_res.scalar_one_or_none()
        if not org:
            print("ERROR: No organisation found."); return

        user_res = await db.execute(
            select(User).where(User.organization_id == org.id).limit(1))
        user = user_res.scalar_one_or_none()
        if not user:
            print("ERROR: No user."); return

        # Build sku → item map
        items_res = await db.execute(
            select(Item).where(Item.organization_id == org.id))
        sku_map = {i.sku: i for i in items_res.scalars().all()}

        svc = InvoiceService(db, org.id)
        print(f"Org: {org.name} | User: {user.email}\n")

        for client_name, email, days_ago, lines_spec in ORDERS:
            issue = TODAY - timedelta(days=days_ago)
            due   = issue + timedelta(days=30)
            lines = []
            for sku, qty in lines_spec:
                item = sku_map.get(sku)
                if not item:
                    print(f"  ⚠️  SKU {sku} not found, skipping line")
                    continue
                lines.append({
                    "description": item.name,
                    "quantity": qty,
                    "unit_price": float(item.sale_price),
                    "cgst_rate":  float(item.cgst_rate),
                    "sgst_rate":  float(item.sgst_rate),
                    "igst_rate":  float(item.igst_rate),
                    "item_id":    str(item.id),
                })

            if not lines:
                continue

            try:
                inv = await svc.create_invoice(
                    client_name=client_name,
                    client_email=email,
                    issue_date=issue,
                    due_date=due,
                    line_items=lines,
                    notes="Thank you for your business!",
                    created_by=user.id,
                )
                skus = ", ".join(s for s, _ in lines_spec)
                print(f"  {inv.invoice_number}  {client_name:35s}  ₹{float(inv.total_amount):>12,.2f}  [{skus}]")
            except Exception as e:
                print(f"  ERROR for {client_name}: {e}")
                await db.rollback()

        print("\n✅ Done. Refresh Invoices + Inventory → Sales Performance.")


if __name__ == "__main__":
    asyncio.run(seed())
