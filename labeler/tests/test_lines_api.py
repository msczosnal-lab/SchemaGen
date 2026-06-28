"""Testy API labelera — linie: semantic-groups, match-color, eksport graphic_lines."""

import tempfile
from pathlib import Path

from fastapi.testclient import TestClient

from labeler.app import app
from labeler.export import label_to_schema
from backend.models.label import LabelRecord, LineAnnotation
from backend.recognize.line_classifier import LineClassifier

client = TestClient(app)


def test_derive_terminals_endpoint():
    # dwa przewody dochodzace do gornej krawedzi bboxa [0,0,100,20] w x=20 i x=80
    res = client.post(
        "/api/derive-terminals",
        json={
            "bbox": [0, 0, 100, 20],
            "lines": [
                {"points": [[20, -40], [20, 0]], "role": "wire"},
                {"points": [[80, -40], [80, 0]], "role": "wire"},
            ],
            "tol": 10,
        },
    )
    assert res.status_code == 200
    terms = res.json()["terminals"]
    assert len(terms) == 2
    assert sorted(round(t["x"], 2) for t in terms) == [0.2, 0.8]
    assert all(t["y"] == 0.0 for t in terms)


def test_semantic_groups_endpoint():
    res = client.get("/api/semantic-groups")
    assert res.status_code == 200
    names = [g["name"] for g in res.json()["groups"]]
    assert "cable" in names
    assert "inverter" in names


def test_match_color_endpoint_inverter():
    res = client.get("/api/match-color", params={"hex": "#9933FF"})
    assert res.status_code == 200
    assert res.json()["semantic_group"] == "inverter"


def test_match_color_no_match():
    res = client.get("/api/match-color", params={"hex": ""})
    assert res.status_code == 200
    assert res.json()["semantic_group"] == ""


def test_export_graphic_lines_roundtrip():
    record = LabelRecord(
        page_id="lines",
        image_path="lines.png",
        image_width=200,
        image_height=200,
        lines=[
            LineAnnotation(
                id="l1",
                points=[[10, 10], [100, 10]],
                role="wire",
                semantic_group="cable",
                color_ref="#000000",
            ),
            LineAnnotation(
                id="l2",
                points=[[20, 20], [40, 60]],
                role="device_stroke",
                semantic_group="inverter",
            ),
        ],
    )
    model = label_to_schema(record)
    assert len(model.graphic_lines) == 2
    wire = next(g for g in model.graphic_lines if g.id == "l1")
    assert wire.role == "wire"
    # tylko wire/bus to kandydaci na Connection
    cands = [g for g in model.graphic_lines if LineClassifier.is_connection_candidate(g)]
    assert [g.id for g in cands] == ["l1"]


def test_save_annotations_with_lines(tmp_path, monkeypatch):
    db = tmp_path / "test.db"
    monkeypatch.setattr("backend.db.DB_PATH", db)
    from backend.db import init_db

    init_db()
    payload = {
        "record": {
            "page_id": "p_lines",
            "image_path": "p_lines.png",
            "image_width": 100,
            "image_height": 100,
            "bboxes": [],
            "lines": [
                {
                    "id": "l1",
                    "points": [[0, 0], [50, 0]],
                    "role": "bus",
                    "style": "solid",
                    "semantic_group": "cable",
                    "color_ref": "#000000",
                }
            ],
            "texts": [],
            "connections": [],
        }
    }
    res = client.post("/api/annotations", json=payload)
    assert res.status_code == 200
    got = client.get("/api/annotations/p_lines")
    assert got.status_code == 200
    lines = got.json().get("lines", [])
    assert len(lines) == 1
    assert lines[0]["role"] == "bus"
