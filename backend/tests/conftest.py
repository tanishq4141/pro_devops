"""Test configuration.

Tests never touch PostgreSQL: DATABASE_URL is pointed at a throw-away SQLite
file *before* the app is imported, and every test starts with empty tables.
"""
import os
import tempfile

_db_file = os.path.join(tempfile.gettempdir(), "stockpilot_test.db")
os.environ["DATABASE_URL"] = f"sqlite:///{_db_file}"

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.db import Base, engine  # noqa: E402
from app.main import app  # noqa: E402


@pytest.fixture()
def client():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    with TestClient(app) as c:
        yield c


@pytest.fixture()
def product(client):
    payload = {
        "sku": "test-001",
        "name": "Barcode Scanner",
        "category": "Electronics",
        "supplier": "ScanCo",
        "quantity": 50,
        "reorder_level": 10,
        "unit_price": "2499.00",
    }
    response = client.post("/api/products", json=payload)
    assert response.status_code == 201, response.text
    return response.json()
