def test_create_product_uppercases_sku_and_sets_status(client, product):
    assert product["sku"] == "TEST-001"
    assert product["stock_status"] == "IN_STOCK"
    assert product["id"] > 0


def test_create_product_rejects_duplicate_sku(client, product):
    response = client.post("/api/products", json={"sku": "TEST-001", "name": "Duplicate"})
    assert response.status_code == 409


def test_create_product_validates_payload(client):
    response = client.post("/api/products", json={"sku": "BAD SKU!", "name": "", "quantity": -5})
    assert response.status_code == 422


def test_list_products(client, product):
    response = client.get("/api/products")
    assert response.status_code == 200
    assert [p["sku"] for p in response.json()] == ["TEST-001"]


def test_list_products_search_and_status_filter(client, product):
    client.post("/api/products", json={"sku": "LOW-1", "name": "Label Roll", "quantity": 3, "reorder_level": 5})
    client.post("/api/products", json={"sku": "OUT-1", "name": "Toner", "quantity": 0})

    assert [p["sku"] for p in client.get("/api/products", params={"q": "scanner"}).json()] == ["TEST-001"]
    assert [p["sku"] for p in client.get("/api/products", params={"status": "LOW_STOCK"}).json()] == ["LOW-1"]
    assert [p["sku"] for p in client.get("/api/products", params={"status": "OUT_OF_STOCK"}).json()] == ["OUT-1"]


def test_get_product_and_404(client, product):
    assert client.get(f"/api/products/{product['id']}").json()["name"] == "Barcode Scanner"
    assert client.get("/api/products/9999").status_code == 404


def test_update_product(client, product):
    response = client.put(f"/api/products/{product['id']}", json={"unit_price": "1999.50", "reorder_level": 60})
    assert response.status_code == 200
    body = response.json()
    assert body["unit_price"] == "1999.50"
    assert body["stock_status"] == "LOW_STOCK"  # 50 units <= reorder level 60


def test_delete_product(client, product):
    assert client.delete(f"/api/products/{product['id']}").status_code == 204
    assert client.get(f"/api/products/{product['id']}").status_code == 404
    assert client.delete(f"/api/products/{product['id']}").status_code == 404
