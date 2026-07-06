"""Testy API SchematicGraph v2 (prompt 022 krok 4)."""

from __future__ import annotations

from fastapi.testclient import TestClient

import pytest

from backend.models.detection import SymbolDetection
from labeler.app import app
from labeler.gt_loader import gt_source, load_gt_schema

client = TestClient(app)

PAGE = "test_graph_api_page"


@pytest.fixture()
def tmp_db(tmp_path, monkeypatch):
    db_path = tmp_path / "test.db"
    from backend import db as db_mod
    import backend.paths as paths_mod

    monkeypatch.setattr(db_mod, "DB_PATH", db_path)
    monkeypatch.setattr(paths_mod, "DB_PATH", db_path)
    db_mod.init_db()
    yield db_path


def _valid_graph_payload() -> dict:
    return {
        "version": 2,
        "page_id": PAGE,
        "image_width": 1000,
        "image_height": 800,
        "symbols": [
            {
                "id": "a",
                "type": "relay",
                "bbox": [100, 100, 200, 200],
                "terminals": [{"id": "1", "x": 0.0, "y": 0.5}],
            },
            {
                "id": "b",
                "type": "fuse",
                "bbox": [400, 100, 500, 200],
                "terminals": [{"id": "2", "x": 1.0, "y": 0.5}],
            },
        ],
        "lines": [
            {
                "id": "L1",
                "from": "a:1",
                "to": "b:2",
                "vertices": [[100, 150], [500, 150]],
                "kind": "power",
            },
        ],
    }


def test_graph_rules():
    res = client.get("/api/graph-rules")
    assert res.status_code == 200
    data = res.json()
    assert "snap_tol_min" in data
    assert "wire_axis_tol_deg" in data


def test_graph_crud_roundtrip(tmp_db):
    payload = _valid_graph_payload()
    post = client.post(f"/api/graph/{PAGE}", json=payload)
    assert post.status_code == 200
    assert post.json()["symbol_count"] == 2

    get = client.get(f"/api/graph/{PAGE}")
    assert get.status_code == 200
    body = get.json()
    assert body["page_id"] == PAGE
    assert len(body["symbols"]) == 2
    assert body["lines"][0]["from"] == "a:1"


def test_graph_save_rejects_invalid(tmp_db):
    bad = _valid_graph_payload()
    bad["symbols"][0]["terminals"] = [{"id": "1", "x": 0.5, "y": 0.5}]
    res = client.post(f"/api/graph/{PAGE}", json=bad)
    assert res.status_code == 422


def test_graph_validate_endpoint(tmp_db):
    res = client.post("/api/graph/validate", json=_valid_graph_payload())
    assert res.status_code == 200
    assert res.json()["valid"] is True


def test_graph_dump(tmp_db):
    client.post(f"/api/graph/{PAGE}", json=_valid_graph_payload())
    res = client.get(f"/api/graph/{PAGE}/dump")
    assert res.status_code == 200
    dump = res.json()["dump"]
    assert "bbox: relay" in dump
    assert "line: L1 OD a:1 DO b:2" in dump


def test_prefill_mock_yolo(tmp_db, monkeypatch, tmp_path):
    from backend import paths as paths_mod
    from labeler import graph_prefill as gp

    img = tmp_path / f"{PAGE}.png"
    img.write_bytes(
        b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01"
        b"\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc\x00\x01"
        b"\x00\x00\x05\x00\x01\r\n-\xdb\x00\x00\x00\x00IEND\xaeB`\x82"
    )
    monkeypatch.setattr(paths_mod, "RAW", tmp_path)
    monkeypatch.setattr(gp, "RAW", tmp_path)
    monkeypatch.setattr(
        gp,
        "image_size_for_page",
        lambda page_id: (1000, 800),
    )

    zlaczka_pattern = {
        "method": "line-contact",
        "expected": [
            {"edge": "left", "frac": 0.5, "required": True},
            {"edge": "right", "frac": 0.5, "required": True},
            {"edge": "top", "frac": 0.5, "required": False},
        ],
    }
    monkeypatch.setattr(
        gp,
        "load_patterns",
        lambda path=None: {"version": 1, "classes": {"zlaczka": zlaczka_pattern}},
    )

    class FakeDet:
        def detect(self, image_path):
            return [
                SymbolDetection(
                    class_id=5,
                    class_name="zlaczka",
                    x=100,
                    y=200,
                    width=50,
                    height=80,
                    confidence=0.9,
                ),
            ]

    monkeypatch.setattr(gp, "_default_detector", lambda: FakeDet())

    res = client.post(f"/api/graph/{PAGE}/prefill")
    assert res.status_code == 200
    body = res.json()
    assert body["symbol_count"] == 1
    assert body["terminal_count"] == 2

    get = client.get(f"/api/graph/{PAGE}")
    sym = get.json()["symbols"][0]
    assert sym["type"] == "zlaczka"
    terms = {(t["x"], t["y"]) for t in sym["terminals"]}
    assert (0.0, 0.5) in terms
    assert (1.0, 0.5) in terms


def test_prefill_409_without_force(tmp_db, monkeypatch, tmp_path):
    from backend import paths as paths_mod
    from labeler import graph_prefill as gp

    img = tmp_path / f"{PAGE}.png"
    img.write_bytes(
        b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01"
        b"\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc\x00\x01"
        b"\x00\x00\x05\x00\x01\r\n-\xdb\x00\x00\x00\x00IEND\xaeB`\x82"
    )
    monkeypatch.setattr(paths_mod, "RAW", tmp_path)
    monkeypatch.setattr(gp, "RAW", tmp_path)
    monkeypatch.setattr(
        gp, "image_size_for_page", lambda page_id: (1000, 800)
    )
    monkeypatch.setattr(
        gp, "load_patterns", lambda path=None: {"version": 1, "classes": {}}
    )
    class FakeDet:
        def detect(self, image_path):
            return []

    monkeypatch.setattr(gp, "_default_detector", lambda: FakeDet())

    first = client.post(f"/api/graph/{PAGE}/prefill")
    assert first.status_code == 200
    second = client.post(f"/api/graph/{PAGE}/prefill")
    assert second.status_code == 409


def test_gt_loader_prefers_graph(tmp_db):
    payload = _valid_graph_payload()
    client.post(f"/api/graph/{PAGE}", json=payload)

    assert gt_source(PAGE) == "graph_v2"
    schema = load_gt_schema(PAGE)
    assert schema is not None
    assert len(schema.connections) == 1
    assert schema.connections[0].from_ref == "a:1"
