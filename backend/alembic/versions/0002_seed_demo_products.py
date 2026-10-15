"""seed demo products so a fresh environment is not empty

Revision ID: 0002_seed_demo_products
"""
from datetime import datetime, timezone

from alembic import op
import sqlalchemy as sa

revision = "0002_seed_demo_products"
down_revision = "0001_create_inventory"
branch_labels = None
depends_on = None

DEMO = [
    ("ELEC-1001", "USB-C Charger 65W", "Electronics", "VoltEdge Supplies", 120, 25, 1899),
    ("ELEC-1002", "Wireless Mouse", "Electronics", "VoltEdge Supplies", 14, 20, 749),
    ("FURN-2001", "Ergonomic Office Chair", "Furniture", "Comfort Works", 6, 5, 12499),
    ("FURN-2002", "Standing Desk Frame", "Furniture", "Comfort Works", 0, 3, 18999),
    ("STAT-3001", "A4 Copier Paper (500)", "Stationery", "PaperTrail Co", 340, 50, 329),
    ("STAT-3002", "Gel Pen Blue (10 pack)", "Stationery", "PaperTrail Co", 9, 15, 120),
    ("PACK-4001", "Corrugated Box Medium", "Packaging", "BoxMart", 800, 200, 38),
]


def upgrade():
    now = datetime.now(timezone.utc)
    products = sa.table(
        "products",
        sa.column("sku"), sa.column("name"), sa.column("description"), sa.column("category"),
        sa.column("supplier"), sa.column("quantity"), sa.column("reorder_level"),
        sa.column("unit_price"), sa.column("created_at"), sa.column("updated_at"),
    )
    op.bulk_insert(products, [
        {"sku": s, "name": n, "description": "", "category": c, "supplier": sup, "quantity": q,
         "reorder_level": r, "unit_price": p, "created_at": now, "updated_at": now}
        for s, n, c, sup, q, r, p in DEMO
    ])


def downgrade():
    op.execute("DELETE FROM products WHERE sku IN (%s)" % ",".join(f"'{d[0]}'" for d in DEMO))
