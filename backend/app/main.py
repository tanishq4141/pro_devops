from contextlib import asynccontextmanager
from decimal import Decimal

from fastapi import Depends, FastAPI, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator
from sqlalchemy import func, or_, select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from .config import settings
from .db import Base, engine, get_db
from .models import Product, StockMovement
from .schemas import (
    MovementOut,
    ProductCreate,
    ProductOut,
    ProductUpdate,
    StatsOut,
    StockAdjust,
    StockStatus,
)


@asynccontextmanager
async def lifespan(_: FastAPI):
    # Containers run `alembic upgrade head` before Uvicorn starts.
    # create_all is a no-op when tables exist and keeps tests self-contained.
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(title=settings.app_name, version=settings.app_version, lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
Instrumentator().instrument(app).expose(app, endpoint="/metrics")


# ---------------------------------------------------------------- platform --
@app.get("/", tags=["Platform"])
def root():
    return {"service": settings.app_name, "version": settings.app_version, "docs": "/docs"}


@app.get("/health", tags=["Platform"])
def health():
    """Liveness: the process is up."""
    return {"status": "UP"}


@app.get("/ready", tags=["Platform"])
def ready(db: Session = Depends(get_db)):
    """Readiness: the database is reachable."""
    db.execute(text("SELECT 1"))
    return {"status": "READY"}


# ---------------------------------------------------------------- helpers ---
def _get_product_or_404(db: Session, product_id: int) -> Product:
    product = db.get(Product, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


def _movement_out(m: StockMovement) -> MovementOut:
    return MovementOut(
        id=m.id,
        product_id=m.product_id,
        product_name=m.product.name,
        sku=m.product.sku,
        change=m.change,
        reason=m.reason,
        note=m.note,
        quantity_after=m.quantity_after,
        created_at=m.created_at,
    )


# ---------------------------------------------------------------- products --
@app.get("/api/products", tags=["Products"], response_model=list[ProductOut])
def list_products(
    q: str | None = Query(default=None, description="Search name, SKU or supplier"),
    category: str | None = None,
    stock_status: StockStatus | None = Query(default=None, alias="status"),
    db: Session = Depends(get_db),
):
    stmt = select(Product).order_by(Product.id.desc())
    if q:
        like = f"%{q.lower()}%"
        stmt = stmt.where(
            or_(
                func.lower(Product.name).like(like),
                func.lower(Product.sku).like(like),
                func.lower(Product.supplier).like(like),
            )
        )
    if category:
        stmt = stmt.where(Product.category == category)
    if stock_status == "OUT_OF_STOCK":
        stmt = stmt.where(Product.quantity <= 0)
    elif stock_status == "LOW_STOCK":
        stmt = stmt.where(Product.quantity > 0, Product.quantity <= Product.reorder_level)
    elif stock_status == "IN_STOCK":
        stmt = stmt.where(Product.quantity > Product.reorder_level)
    return list(db.scalars(stmt))


@app.get("/api/products/stats", tags=["Products"], response_model=StatsOut)
def stats(db: Session = Depends(get_db)):
    total, units, value, categories = db.execute(
        select(
            func.count(Product.id),
            func.coalesce(func.sum(Product.quantity), 0),
            func.coalesce(func.sum(Product.quantity * Product.unit_price), 0),
            func.count(func.distinct(Product.category)),
        )
    ).one()
    out_of_stock = db.scalar(select(func.count(Product.id)).where(Product.quantity <= 0))
    low_stock = db.scalar(
        select(func.count(Product.id)).where(Product.quantity > 0, Product.quantity <= Product.reorder_level)
    )
    return StatsOut(
        totalProducts=total,
        totalUnits=int(units),
        inventoryValue=Decimal(value).quantize(Decimal("0.01")),
        lowStock=low_stock,
        outOfStock=out_of_stock,
        categories=categories,
    )


@app.get("/api/products/{product_id}", tags=["Products"], response_model=ProductOut)
def get_product(product_id: int, db: Session = Depends(get_db)):
    return _get_product_or_404(db, product_id)


@app.post("/api/products", tags=["Products"], response_model=ProductOut, status_code=status.HTTP_201_CREATED)
def create_product(payload: ProductCreate, db: Session = Depends(get_db)):
    product = Product(**payload.model_dump())
    product.sku = product.sku.upper()
    db.add(product)
    try:
        db.flush()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail=f"SKU {product.sku} already exists")
    if product.quantity:
        db.add(StockMovement(product_id=product.id, change=product.quantity, reason="RESTOCK",
                             note="Opening stock", quantity_after=product.quantity))
    db.commit()
    db.refresh(product)
    return product


@app.put("/api/products/{product_id}", tags=["Products"], response_model=ProductOut)
def update_product(product_id: int, payload: ProductUpdate, db: Session = Depends(get_db)):
    product = _get_product_or_404(db, product_id)
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(product, key, value)
    db.commit()
    db.refresh(product)
    return product


@app.delete("/api/products/{product_id}", tags=["Products"], status_code=status.HTTP_204_NO_CONTENT)
def delete_product(product_id: int, db: Session = Depends(get_db)):
    product = _get_product_or_404(db, product_id)
    db.delete(product)
    db.commit()


# ---------------------------------------------------------------- stock -----
@app.post("/api/products/{product_id}/adjust", tags=["Stock"], response_model=ProductOut)
def adjust_stock(product_id: int, payload: StockAdjust, db: Session = Depends(get_db)):
    product = _get_product_or_404(db, product_id)
    if payload.change == 0:
        raise HTTPException(status_code=422, detail="Change must not be zero")
    new_qty = product.quantity + payload.change
    if new_qty < 0:
        raise HTTPException(status_code=409, detail=f"Insufficient stock: only {product.quantity} units available")
    product.quantity = new_qty
    db.add(StockMovement(product_id=product.id, change=payload.change, reason=payload.reason,
                         note=payload.note, quantity_after=new_qty))
    db.commit()
    db.refresh(product)
    return product


@app.get("/api/products/{product_id}/movements", tags=["Stock"], response_model=list[MovementOut])
def product_movements(product_id: int, db: Session = Depends(get_db)):
    _get_product_or_404(db, product_id)
    rows = db.scalars(
        select(StockMovement).where(StockMovement.product_id == product_id).order_by(StockMovement.id.desc())
    )
    return [_movement_out(m) for m in rows]


@app.get("/api/movements", tags=["Stock"], response_model=list[MovementOut])
def recent_movements(limit: int = Query(default=10, ge=1, le=100), db: Session = Depends(get_db)):
    rows = db.scalars(select(StockMovement).order_by(StockMovement.id.desc()).limit(limit))
    return [_movement_out(m) for m in rows]
