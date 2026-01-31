"""
Seed script: inserts 12 sample invoices with line items for demo/testing.
Run from the backend/ directory:
    PYTHONPATH=. /home/ishita/.cache/pypoetry/virtualenvs/event-management-backend-hBIlJ0Xn-py3.12/bin/python seed_invoices.py
"""
import asyncio
from datetime import date, timedelta
import random

# --- Sample Data ---
CLIENTS = [
    ("Reliance Events Pvt Ltd", "reliance@events.com", "27AAACR5055K1ZX"),
    ("Tata Consulting Services", "tcs@finance.com", "27AAACT2727Q1ZX"),
    ("Infosys BPM Ltd", "infosys@bpm.in", None),
    ("Wipro Technologies", "wipro@wipro.com", "29AAACW3401E1ZR"),
    ("HDFC Bank Corporate", None, None),
    ("Mahindra & Mahindra", "mahindra@corp.in", "27AAACM4085R1ZX"),
    ("Bajaj Auto Ltd", "bajaj@auto.com", "27AAACB3432R1ZX"),
    ("Akash Enterprises", "akash@enterprise.in", None),
    ("Priya Events Management", "priya@events.in", None),
    ("Sun Pharma Industries", "sunpharma@corp.com", "24AAACS9735C1ZX"),
]

SERVICES = [
    ("Event Management Services", 25000, 9, 9, 0),
    ("Photography & Videography", 15000, 9, 9, 0),
    ("Decoration & Setup", 12000, 9, 9, 0),
    ("Sound & Lighting", 18000, 9, 9, 0),
    ("Catering Services", 30000, 2.5, 2.5, 0),
    ("Venue Booking Assistance", 8000, 9, 9, 0),
    ("Digital Marketing Campaign", 20000, 9, 9, 0),
    ("Corporate Training Program", 40000, 9, 9, 0),
    ("Security Services", 6000, 9, 9, 0),
    ("Transport & Logistics", 5000, 9, 9, 0),
]

STATUSES = ["sent", "sent", "sent", "paid", "paid", "partial", "draft"]


async def seed():
    from app.db.session import AsyncSessionLocal
    from app.models.user import User
    from app.models.organization import Organization
    from app.services.invoice_service import InvoiceService
    from app.services.coa_service import CoAService
    from sqlalchemy import select

    async with AsyncSessionLocal() as db:
        # Get first org + user
        org_res = await db.execute(select(Organization).limit(1))
        org = org_res.scalar_one_or_none()
        if not org:
            print("ERROR: No organization found. Log in via the UI first to create one.")
            return

        user_res = await db.execute(select(User).where(User.organization_id == org.id).limit(1))
        user = user_res.scalar_one_or_none()
        if not user:
            print("ERROR: No user found in org.")
            return

        print(f"Seeding invoices for org: {org.name} | user: {user.email}")

        # Seed CoA first (needed for journal posting)
        coa = CoAService(db, org.id)
        try:
            await coa.seed_default_accounts()
            print("CoA seeded.")
        except Exception as e:
            print(f"CoA seed skipped (probably already exists): {e}")

        svc = InvoiceService(db, org.id)
        today = date.today()

        for i in range(12):
            client = random.choice(CLIENTS)
            num_lines = random.randint(1, 3)
            lines = []
            for _ in range(num_lines):
                svc_name, base_price, cgst, sgst, igst = random.choice(SERVICES)
                qty = random.choice([1, 2, 3])
                lines.append({
                    "description": svc_name,
                    "quantity": qty,
                    "unit_price": base_price + random.randint(-2000, 5000),
                    "cgst_rate": cgst,
                    "sgst_rate": sgst,
                    "igst_rate": igst,
                })

            issue_offset = random.randint(-60, 0)
            due_offset = random.randint(15, 45)
            issue = today + timedelta(days=issue_offset)
            due = issue + timedelta(days=due_offset)

            try:
                inv = await svc.create_invoice(
                    client_name=client[0],
                    client_email=client[1],
                    client_gstin=client[2],
                    issue_date=issue,
                    due_date=due,
                    line_items=lines,
                    notes="Thank you for your business!",
                    created_by=user.id,
                )
                print(f"  Created {inv.invoice_number} — {client[0]} — ₹{float(inv.total_amount):,.2f}")
            except Exception as e:
                print(f"  ERROR creating invoice #{i+1}: {e}")
                await db.rollback()

        await db.commit()
        print("\nDone! Refresh the Invoices page.")


if __name__ == "__main__":
    asyncio.run(seed())
