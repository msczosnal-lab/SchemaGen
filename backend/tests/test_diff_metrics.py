"""Testy metryk diff GT vs runtime (bez obrazow)."""

from __future__ import annotations

from backend.models.schema import Component, Connection, SchemaModel
from scripts.diff_metrics import diff_components, diff_connections, diff_tags


def test_diff_connections_match() -> None:
    gt = SchemaModel(
        connections=[
            Connection.model_validate({"from": "a", "to": "b", "kind": "power"}),
        ]
    )
    rt = SchemaModel(
        connections=[
            Connection.model_validate({"from": "a", "to": "b", "kind": "power"}),
            Connection.model_validate({"from": "c", "to": "d", "kind": "link"}),
        ]
    )
    d = diff_connections(gt, rt)
    assert d["match"] == 1
    assert len(d["only_runtime"]) == 1


def test_diff_components_iou() -> None:
    gt = SchemaModel(
        components=[
            Component(id="g1", type="relay", bbox=[10, 10, 50, 50]),
        ]
    )
    rt = SchemaModel(
        components=[
            Component(id="r1", type="relay", bbox=[12, 12, 52, 52]),
            Component(id="r2", type="fuse", bbox=[200, 200, 240, 240]),
        ]
    )
    d = diff_components(gt, rt)
    assert d["match"] == 1
    assert d["pairs"][0]["gt"] == "g1"


def test_diff_tags_normalized() -> None:
    gt = SchemaModel(components=[Component(id="g1", type="relay", tag="-F1")])
    rt = SchemaModel(components=[Component(id="r1", type="relay", tag="-f1")])
    d = diff_tags(gt, rt)
    assert d["match"] == 1
