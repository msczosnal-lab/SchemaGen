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
