"""
Seed script: inserts 10 inventory items with varying stock levels (some low).
Run from backend/ directory:
    PYTHONPATH=. /home/ishita/.cache/pypoetry/virtualenvs/event-management-backend-hBIlJ0Xn-py3.12/bin/python seed_inventory.py
"""
import asyncio
from decimal import Decimal

ITEMS = [
    # (sku, name, unit, cost, sale, opening_qty, reorder_level, cgst, sgst, igst)
    # Healthy stock
    ("SND-001", "Portable PA Sound System",   "set",   8000,  15000, 12, 3,  9,   9,   0),
    ("LGT-002", "LED Stage Lighting Kit",     "set",   5000,  10000, 8,  2,  9,   9,   0),
    ("VID-003", "Sony FX3 Camera (Rental)",   "day",   2500,  6000,  15, 4,  9,   9,   0),
    ("DEC-004", "Floral Decoration Package",  "set",   3000,  7500,  20, 5,  9,   9,   0),
    ("CAT-005", "Premium Buffet Package",     "plate", 180,   400,   200,50,  2.5, 2.5, 0),
    ("TEN-006", "Outdoor Tent (20x20 ft)",    "set",   12000, 25000, 6,  2,  9,   9,   0),
    # Low stock (below reorder level)
    ("FOG-007", "Fog Machine",                "pcs",   3500,  7000,  1,  3,  9,   9,   0),  # low
    ("PRJ-008", "HD Projector + Screen",      "set",   7000,  14000, 2,  3,  9,   9,   0),  # low
    ("MIC-009", "Wireless Microphone Set",    "set",   2000,  5000,  1,  5,  9,   9,   0),  # critically low
    ("STG-010", "Portable Stage Platform",    "set",   15000, 30000, 0,  2,  9,   9,   0),  # out of stock
]


async def seed():
    from app.db.session import AsyncSessionLocal
    from app.models.organization import Organization
    from app.services.inventory_service import InventoryService
    from sqlalchemy import select

    async with AsyncSessionLocal() as db:
        org_res = await db.execute(select(Organization).limit(1))
        org = org_res.scalar_one_or_none()
        if not org:
            print("ERROR: No organisation found.")
            return

        svc = InventoryService(db, org.id)
        print(f"Seeding inventory for org: {org.name}\n")

        for sku, name, unit, cost, sale, opening_qty, reorder_level, cgst, sgst, igst in ITEMS:
            try:
                item = await svc.create_item(
                    sku=sku,
                    name=name,
                    unit=unit,
                    cost_price=Decimal(str(cost)),
                    sale_price=Decimal(str(sale)),
                    reorder_level=Decimal(str(reorder_level)),
                    cgst_rate=Decimal(str(cgst)),
                    sgst_rate=Decimal(str(sgst)),
                    igst_rate=Decimal(str(igst)),
                )
                # Set opening stock via adjustment
                if opening_qty > 0:
                    from datetime import date
                    await svc.adjust_stock(
                        item_id=item.id,
                        movement_type="adjustment",
                        qty=Decimal(str(opening_qty)),
                        movement_date=date.today(),
                        notes="Opening stock"
                    )
                stock_status = "✅ OK" if opening_qty > reorder_level else ("⚠️ LOW" if opening_qty > 0 else "🔴 OUT")
                print(f"  {stock_status}  {sku:10s}  {name:35s}  stock={opening_qty:3d}  reorder≤{reorder_level}")
            except Exception as e:
                print(f"  ERROR {sku}: {e}")

        print("\n✅ Done. Refresh the Inventory page.")


if __name__ == "__main__":
    asyncio.run(seed())
