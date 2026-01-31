"""
Seed script: adds invoices across all 4 aging buckets.

Today = 2026-02-22
Buckets:
  Current  (0-30 days overdue) : due between 2026-01-23 and today
  31-60 d  : due between 2025-12-23 and 2026-01-22
  61-90 d  : due between 2025-11-24 and 2025-12-22
  >90 days : due before 2025-11-24

Run from backend/ directory:
    PYTHONPATH=. /home/ishita/.cache/pypoetry/virtualenvs/event-management-backend-hBIlJ0Xn-py3.12/bin/python seed_aging.py
"""
import asyncio
from datetime import date, timedelta

# today = 2026-02-22
TODAY = date(2026, 2, 22)


SAMPLES = [
    # (client_name, email, gstin, due_days_ago, services)
    # ── CURRENT  (0-30 days overdue) ─────────────────────
    ("Akash Enterprises",       "akash@enterprise.in",  None,                    5,   [("Photography & Videography", 1, 18000, 9, 9, 0)]),
    ("HDFC Bank Corporate",     None,                   None,                    15,  [("Corporate Training Program", 2, 20000, 9, 9, 0), ("Sound & Lighting", 1, 12000, 9, 9, 0)]),
    ("Meera Catering Co",       "meera@catering.in",    None,                    25,  [("Catering Services", 1, 55000, 2.5, 2.5, 0)]),

    # ── 31-60 DAYS OVERDUE ───────────────────────────────
    ("Tata Consulting Services","tcs@finance.com",      "27AAACT2727Q1ZX",       40,  [("Digital Marketing Campaign", 1, 30000, 9, 9, 0)]),
    ("Wipro Technologies",      "wipro@wipro.com",      "29AAACW3401E1ZR",       50,  [("Event Management Services", 1, 40000, 9, 9, 0), ("Decoration & Setup", 1, 8000, 9, 9, 0)]),
    ("Sunrise Hotels Pvt Ltd",  None,                   None,                    55,  [("Sound & Lighting", 2, 10000, 9, 9, 0)]),

    # ── 61-90 DAYS OVERDUE ───────────────────────────────
    ("Reliance Events Pvt Ltd", "reliance@events.com",  "27AAACR5055K1ZX",       70,  [("Event Management Services", 3, 25000, 9, 9, 0)]),
    ("Bajaj Auto Ltd",          "bajaj@auto.com",       "27AAACB3432R1ZX",       80,  [("Corporate Training Program", 1, 45000, 9, 9, 0)]),
    ("Star Hospitality Ltd",    "star@hospitality.in",  None,                    88,  [("Photography & Videography", 2, 14000, 9, 9, 0), ("Catering Services", 1, 20000, 2.5, 2.5, 0)]),

    # ── >90 DAYS OVERDUE ─────────────────────────────────
    ("Infosys BPM Ltd",         "infosys@bpm.in",       None,                    100, [("Digital Marketing Campaign", 2, 25000, 9, 9, 0)]),
    ("Mahindra & Mahindra",     "mahindra@corp.in",     "27AAACM4085R1ZX",       120, [("Event Management Services", 2, 35000, 9, 9, 0), ("Venue Booking Assistance", 1, 9000, 9, 9, 0)]),
    ("Sun Pharma Industries",   "sunpharma@corp.com",   "24AAACS9735C1ZX",       150, [("Corporate Training Program", 1, 60000, 9, 9, 0)]),
    ("Priya Events Management", "priya@events.in",      None,                    200, [("Photography & Videography", 1, 22000, 9, 9, 0), ("Decoration & Setup", 2, 10000, 9, 9, 0)]),
]


async def seed():
    from app.db.session import AsyncSessionLocal
    from app.models.user import User
    from app.models.organization import Organization
    from app.services.invoice_service import InvoiceService
    from sqlalchemy import select

    async with AsyncSessionLocal() as db:
        org_res = await db.execute(select(Organization).limit(1))
        org = org_res.scalar_one_or_none()
        if not org:
            print("ERROR: No organisation found. Log in via the UI first.")
            return

        user_res = await db.execute(select(User).where(User.organization_id == org.id).limit(1))
        user = user_res.scalar_one_or_none()
        if not user:
            print("ERROR: No user found in org.")
            return

        print(f"Org: {org.name} | User: {user.email}\n")
        svc = InvoiceService(db, org.id)

        bucket_labels = {
            range(0, 31): "CURRENT  (0-30 d)",
            range(31, 61): "31-60 d",
            range(61, 91): "61-90 d",
        }

        for client_name, email, gstin, due_days_ago, services in SAMPLES:
            due_date = TODAY - timedelta(days=due_days_ago)
            issue_date = due_date - timedelta(days=30)

            lines = [
                {"description": desc, "quantity": qty, "unit_price": price,
                 "cgst_rate": cgst, "sgst_rate": sgst, "igst_rate": igst}
                for desc, qty, price, cgst, sgst, igst in services
            ]

            bucket = "CURRENT" if due_days_ago <= 30 else f"{due_days_ago}d overdue"

            try:
                inv = await svc.create_invoice(
                    client_name=client_name,
                    client_email=email,
                    client_gstin=gstin,
                    issue_date=issue_date,
                    due_date=due_date,
                    line_items=lines,
                    notes="Payment pending. Please settle at the earliest.",
                    created_by=user.id,
                )
                label = "CURRENT" if due_days_ago <= 30 else (
                    "31-60d" if due_days_ago <= 60 else (
                    "61-90d" if due_days_ago <= 90 else ">90d"))
                print(f"  [{label:8s}] {inv.invoice_number}  {client_name:35s}  ₹{float(inv.total_amount):>12,.2f}  due {due_date}")
            except Exception as e:
                print(f"  ERROR for {client_name}: {e}")
                await db.rollback()

        print("\n✅ Done. Refresh the Invoices and Aging pages.")


if __name__ == "__main__":
    asyncio.run(seed())
