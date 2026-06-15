"""Testy API labelera — paleta symboli."""

from fastapi.testclient import TestClient

from labeler.app import app

client = TestClient(app)


def test_symbol_palette_endpoint():
    res = client.get("/api/symbol-palette", params={"limit": 60})
    assert res.status_code == 200
    data = res.json()
    assert "symbols" in data
    assert len(data["symbols"]) >= 40


def test_symbol_palette_search():
    res = client.get("/api/symbol-palette", params={"q": "stycznik"})
    assert res.status_code == 200
    ids = [s["id"] for s in res.json()["symbols"]]
    assert "contactor" in ids


def test_tag_usage_endpoint(tmp_path, monkeypatch):
    db = tmp_path / "test.db"
    cat = tmp_path / "element-catalog.yaml"
    cat.write_text("elements: []\n", encoding="utf-8")
    monkeypatch.setattr("backend.db.DB_PATH", db)
    monkeypatch.setattr("backend.catalog.CATALOG_PATH", cat)
    from backend.db import init_db

    init_db()
    res = client.post("/api/tag-usage", json={"labels": ["Wolne haslo test"]})
    assert res.status_code == 200
    data = res.json()
    assert data["bumped"] == 1
    assert data["catalog_added"] == 1

    res2 = client.get("/api/symbol-palette", params={"limit": 100})
    labels = [s["label_pl"] for s in res2.json()["symbols"]]
    assert "Wolne haslo test" in labels
