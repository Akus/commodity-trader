def test_market_order_fills(client):
    r = client.post("/orders", json={"symbol": "GOLD", "side": "buy", "quantity": 10})
    assert r.status_code == 201
    body = r.json()
    assert body["status"] == "filled"
    assert body["filled_price"] > 0
    assert body["notional"] == round(body["filled_price"] * 10, 2)


def test_order_unknown_symbol_rejected(client):
    r = client.post("/orders", json={"symbol": "DOGE", "side": "buy", "quantity": 1})
    assert r.status_code == 201
    assert r.json()["status"] == "rejected"


def test_unfillable_limit_rejected(client):
    # Buy limit far below market never crosses.
    r = client.post(
        "/orders",
        json={"symbol": "GOLD", "side": "buy", "quantity": 1, "limit_price": 1.0},
    )
    assert r.json()["status"] == "rejected"


def test_invalid_quantity_422(client):
    r = client.post("/orders", json={"symbol": "GOLD", "side": "buy", "quantity": 0})
    assert r.status_code == 422


def test_order_roundtrip_lookup(client):
    created = client.post(
        "/orders", json={"symbol": "SILVER", "side": "sell", "quantity": 5}
    ).json()
    got = client.get(f"/orders/{created['id']}")
    assert got.status_code == 200
    assert got.json()["id"] == created["id"]
