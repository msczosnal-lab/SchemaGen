"""Routing UI GT v2 (prompt 022 krok 5)."""

from fastapi.testclient import TestClient

from labeler.app import app

client = TestClient(app)


def test_root_serves_graph_html():
    res = client.get("/")
    assert res.status_code == 200
    assert "graph.js" in res.text
    assert "GT v2" in res.text


def test_legacy_serves_index_html():
    res = client.get("/legacy")
    assert res.status_code == 200
    assert "app.js" in res.text
    assert "graph.js" not in res.text


def test_graph_static_assets():
    for path in ("/static/graph.js", "/static/graph.css", "/static/graph.html"):
        res = client.get(path)
        assert res.status_code == 200, path


def test_api_pages_allows_null_timestamps(tmp_path, monkeypatch):
    db_path = tmp_path / "test.db"
    from backend import db as db_mod
    import backend.paths as paths_mod

    monkeypatch.setattr(db_mod, "DB_PATH", db_path)
    monkeypatch.setattr(paths_mod, "DB_PATH", db_path)
    db_mod.init_db()
    db_mod.upsert_page("page_no_gt", "page_no_gt.png")

    res = client.get("/api/pages")
    assert res.status_code == 200
    rows = res.json()
    row = next(r for r in rows if r["id"] == "page_no_gt")
    assert row["graph_updated_at"] is None
    assert row["annotation_updated_at"] is None
