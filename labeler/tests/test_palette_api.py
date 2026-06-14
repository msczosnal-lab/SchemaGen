"""Testy API labelera — paleta symboli."""

from fastapi.testclient import TestClient

from labeler.app import app

client = TestClient(app)


def test_symbol_palette_endpoint():
    res = client.get("/api/symbol-palette")
    assert res.status_code == 200
    data = res.json()
    assert "symbols" in data
    assert len(data["symbols"]) >= 40


def test_symbol_palette_search():
    res = client.get("/api/symbol-palette", params={"q": "stycznik"})
    assert res.status_code == 200
    ids = [s["id"] for s in res.json()["symbols"]]
    assert "contactor" in ids
