def test_list_quotes(client):
    r = client.get("/quotes")
    assert r.status_code == 200
    data = r.json()
    assert len(data) >= 1
    symbols = {q["symbol"] for q in data}
    assert "GOLD" in symbols
    assert all(q["price"] > 0 for q in data)


def test_get_quote_case_insensitive(client):
    r = client.get("/quotes/gold")
    assert r.status_code == 200
    assert r.json()["symbol"] == "GOLD"


def test_get_unknown_quote(client):
    r = client.get("/quotes/DOGE")
    assert r.status_code == 404
