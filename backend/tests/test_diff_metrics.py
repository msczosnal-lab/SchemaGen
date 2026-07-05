"""Testy metryk diff GT vs runtime (bez obrazow)."""

from __future__ import annotations

from backend.models.schema import Component, Connection, GraphicLine, SchemaModel
from backend.validate.diff_metrics import (
    aggregate_score,
    diff_components,
    diff_connections,
    diff_lines,
    diff_tags,
)


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


# --- 020: P/R/F1, per_class, model_gaps ---


def test_diff_connections_prf() -> None:
    gt = SchemaModel(
        connections=[
            Connection.model_validate({"from": "a", "to": "b", "kind": "power"}),
            Connection.model_validate({"from": "b", "to": "c", "kind": "power"}),
        ]
    )
    rt = SchemaModel(
        connections=[
            Connection.model_validate({"from": "a", "to": "b", "kind": "power"}),
        ]
    )
    d = diff_connections(gt, rt)
    assert d["precision"] == 1.0
    assert d["recall"] == 0.5
    assert 0.66 < d["f1"] < 0.67


def test_diff_components_per_class_and_model_gaps() -> None:
    gt = SchemaModel(
        components=[
            Component(id="g1", type="relay", bbox=[10, 10, 50, 50]),
            Component(id="g2", type="arrow_in", bbox=[100, 100, 140, 140]),
        ]
    )
    rt = SchemaModel(
        components=[
            Component(id="r1", type="relay", bbox=[11, 11, 51, 51]),
        ]
    )
    d = diff_components(gt, rt)
    assert d["per_class"]["relay"]["match"] == 1
    assert d["per_class"]["relay"]["f1"] == 1.0
    assert d["per_class"]["arrow_in"]["gt"] == 1
    assert d["per_class"]["arrow_in"]["match"] == 0
    assert d["model_gaps"] == ["arrow_in"]


# --- 020: diff_lines ---


def _line(lid: str, pts: list[list[float]], role: str = "wire") -> GraphicLine:
    return GraphicLine(id=lid, points=pts, role=role)


def test_diff_lines_identical() -> None:
    gt = SchemaModel(graphic_lines=[_line("g1", [[0, 0], [200, 0]])])
    rt = SchemaModel(graphic_lines=[_line("r1", [[0, 0], [200, 0]])])
    d = diff_lines(gt, rt, tol=8.0)
    assert d["f1"] == 1.0
    assert d["per_role"]["wire"]["f1"] == 1.0


def test_diff_lines_shifted_beyond_tol() -> None:
    gt = SchemaModel(graphic_lines=[_line("g1", [[0, 0], [200, 0]])])
    rt = SchemaModel(graphic_lines=[_line("r1", [[0, 50], [200, 50]])])
    d = diff_lines(gt, rt, tol=8.0)
    assert d["f1"] == 0.0


def test_diff_lines_partial_coverage() -> None:
    gt = SchemaModel(graphic_lines=[_line("g1", [[0, 0], [200, 0]])])
    rt = SchemaModel(graphic_lines=[_line("r1", [[0, 0], [100, 0]])])
    d = diff_lines(gt, rt, tol=8.0)
    assert d["precision"] > 0.9  # cala linia rt lezy na gt
    assert 0.3 < d["recall"] < 0.7  # ~polowa gt pokryta


def test_diff_lines_empty_runtime() -> None:
    gt = SchemaModel(graphic_lines=[_line("g1", [[0, 0], [200, 0]])])
    rt = SchemaModel()
    d = diff_lines(gt, rt, tol=8.0)
    assert d["recall"] == 0.0
    assert d["f1"] == 0.0


# --- 020: aggregate_score ---


_W = {"components": 0.30, "lines": 0.25, "connections": 0.35, "tags": 0.10}


def test_aggregate_score_perfect() -> None:
    report = {
        "components": {"gt_count": 5, "f1": 1.0},
        "lines": {"gt_count": 5, "f1": 1.0},
        "connections": {"gt_count": 5, "f1": 1.0},
        "tags": {"gt_count": 5, "f1": 1.0},
    }
    s = aggregate_score(report, _W)
    assert s["score"] == 100.0


def test_aggregate_score_renormalizes_empty_layer() -> None:
    report = {
        "components": {"gt_count": 5, "f1": 1.0},
        "lines": {"gt_count": 0, "f1": 0.0},  # brak GT linii -> wylaczona
        "connections": {"gt_count": 5, "f1": 1.0},
        "tags": {"gt_count": 5, "f1": 1.0},
    }
    s = aggregate_score(report, _W)
    assert s["score"] == 100.0
    assert "lines" not in s["per_layer"]


def test_aggregate_score_monotonic() -> None:
    lo = {
        "components": {"gt_count": 5, "f1": 0.5},
        "connections": {"gt_count": 5, "f1": 0.5},
    }
    hi = {
        "components": {"gt_count": 5, "f1": 0.5},
        "connections": {"gt_count": 5, "f1": 0.9},
    }
    assert aggregate_score(hi, _W)["score"] > aggregate_score(lo, _W)["score"]
