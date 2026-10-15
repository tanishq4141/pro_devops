def test_adjust_stock_sale_and_restock(client, product):
    pid = product["id"]
    sale = client.post(f"/api/products/{pid}/adjust", json={"change": -45, "reason": "SALE"})
    assert sale.status_code == 200
    assert sale.json()["quantity"] == 5
    assert sale.json()["stock_status"] == "LOW_STOCK"

    restock = client.post(f"/api/products/{pid}/adjust", json={"change": 100, "reason": "RESTOCK", "note": "PO-77"})
    assert restock.json()["quantity"] == 105


def test_adjust_stock_cannot_go_negative(client, product):
    response = client.post(f"/api/products/{product['id']}/adjust", json={"change": -51, "reason": "SALE"})
    assert response.status_code == 409
    assert client.get(f"/api/products/{product['id']}").json()["quantity"] == 50


def test_adjust_stock_rejects_zero_and_unknown_reason(client, product):
    pid = product["id"]
    assert client.post(f"/api/products/{pid}/adjust", json={"change": 0, "reason": "SALE"}).status_code == 422
    assert client.post(f"/api/products/{pid}/adjust", json={"change": 1, "reason": "GIFT"}).status_code == 422


def test_movement_history_records_every_change(client, product):
    pid = product["id"]
    client.post(f"/api/products/{pid}/adjust", json={"change": -2, "reason": "DAMAGED"})
    history = client.get(f"/api/products/{pid}/movements").json()
    assert [(m["change"], m["reason"], m["quantity_after"]) for m in history] == [(-2, "DAMAGED", 48), (50, "RESTOCK", 50)]
    assert client.get("/api/movements", params={"limit": 1}).json()[0]["reason"] == "DAMAGED"


def test_stats(client, product):
    client.post("/api/products", json={"sku": "LOW-1", "name": "Label Roll", "category": "Packaging",
                                       "quantity": 3, "reorder_level": 5, "unit_price": "100"})
    client.post("/api/products", json={"sku": "OUT-1", "name": "Toner", "quantity": 0})
    stats = client.get("/api/products/stats").json()
    assert stats["totalProducts"] == 3
    assert stats["totalUnits"] == 53
    assert stats["inventoryValue"] == "125250.00"  # 50*2499 + 3*100
    assert stats["lowStock"] == 1
    assert stats["outOfStock"] == 1
    assert stats["categories"] == 3
