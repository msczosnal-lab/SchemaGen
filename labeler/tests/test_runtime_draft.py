"""Testy konwersji runtime draft + batch derive."""

import json

from fastapi.testclient import TestClient

from backend.models.schema import Component, Connection, GraphicLine, SchemaMeta, SchemaModel, Terminal
from labeler.app import app
from labeler.runtime_draft import schema_to_label_record

client = TestClient(app)


def test_derive_terminals_page_batch():
    res = client.post(
        "/api/derive-terminals-page",
        json={
            "bboxes": [
                {"id": "a", "bbox": [0, 0, 100, 20]},
                {"id": "b", "bbox": [200, 0, 300, 20]},
            ],
            "lines": [
                {"points": [[20, -40], [20, 0]], "role": "wire"},
                {"points": [[250, -40], [250, 0]], "role": "wire"},
            ],
            "tol": 10,
        },
    )
    assert res.status_code == 200
    data = res.json()
    assert data["with_terminals"] == 2
    assert len(data["results"]["a"]) == 1
    assert len(data["results"]["b"]) == 1


def test_schema_to_label_record_maps_connections_and_terminals():
    schema = SchemaModel(
        meta=SchemaMeta(source="t"),
        components=[
            Component(
                id="X1",
                type="relay",
                bbox=[10, 10, 50, 40],
                terminals=[Terminal(id="1", x=0.5, y=0.0)],
            )
        ],
        graphic_lines=[
            GraphicLine(id="l1", points=[[0, 0], [10, 10]], role="wire"),
        ],
        connections=[Connection.model_validate({"from": "X1:1", "to": "Y2", "kind": "power"})],
    )
    rec = schema_to_label_record("t", schema, 100, 100)
    assert rec.bboxes[0].terminals[0].id == "1"
    assert len(rec.lines) == 1
    assert rec.connections[0].from_ref == "X1:1"
    assert rec.connections[0].to == "Y2"
