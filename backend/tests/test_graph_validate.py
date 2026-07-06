"""Testy walidacji SchematicGraph (ortho, snap, obrys terminala)."""

from __future__ import annotations

from backend.models.schema import Terminal
from backend.models.schematic_graph import GraphLine, GraphSymbol, SchematicGraph
from labeler.graph_validate import graph_rules, validate_graph


def _valid_graph(**kwargs) -> SchematicGraph:
    base = dict(
        page_id="t",
        image_width=2000,
        image_height=1500,
        symbols=[
            GraphSymbol(
                id="a",
                type="relay",
                bbox=[100, 100, 200, 200],
                terminals=[Terminal(id="1", x=0.0, y=0.5)],
            ),
            GraphSymbol(
                id="b",
                type="fuse",
                bbox=[300, 100, 400, 200],
                terminals=[Terminal(id="2", x=1.0, y=0.5)],
            ),
        ],
        lines=[
            GraphLine.model_validate(
                {
                    "id": "L1",
                    "from": "a:1",
                    "to": "b:2",
                    "vertices": [[100, 150], [300, 150]],
                    "kind": "power",
                }
            ),
        ],
    )
    base.update(kwargs)
    return SchematicGraph(**base)


def test_validate_graph_ok() -> None:
    r = validate_graph(_valid_graph())
    assert r.valid
    assert r.errors == []


def test_validate_empty_vertices_ok() -> None:
    g = _valid_graph(
        lines=[
            GraphLine.model_validate(
                {"id": "L1", "from": "a:1", "to": "b:2", "kind": "power"}
            ),
        ],
    )
    r = validate_graph(g)
    assert r.valid


def test_validate_terminal_not_on_edge() -> None:
    g = _valid_graph(
        symbols=[
            GraphSymbol(
                id="a",
                type="relay",
                bbox=[100, 100, 200, 200],
                terminals=[Terminal(id="1", x=0.5, y=0.5)],
            ),
            GraphSymbol(
                id="b",
                type="fuse",
                bbox=[300, 100, 400, 200],
                terminals=[Terminal(id="2", x=1.0, y=0.5)],
            ),
        ],
    )
    r = validate_graph(g)
    assert not r.valid
    assert any("obrysem" in e for e in r.errors)


def test_validate_unknown_line_ref() -> None:
    g = _valid_graph(
        lines=[
            GraphLine.model_validate(
                {"id": "L1", "from": "a:1", "to": "missing:9", "kind": "power"}
            ),
        ],
    )
    r = validate_graph(g)
    assert not r.valid
    assert any("nieznany" in e for e in r.errors)


def test_validate_non_ortho_segment() -> None:
    g = _valid_graph(
        lines=[
            GraphLine.model_validate(
                {
                    "id": "L1",
                    "from": "a:1",
                    "to": "b:2",
                    "vertices": [[100, 150], [200, 250]],
                    "kind": "power",
                }
            ),
        ],
    )
    r = validate_graph(g)
    assert not r.valid
    assert any("osiowy" in e for e in r.errors)


def test_validate_vertices_not_snapped() -> None:
    g = _valid_graph(
        lines=[
            GraphLine.model_validate(
                {
                    "id": "L1",
                    "from": "a:1",
                    "to": "b:2",
                    "vertices": [[500, 500], [300, 150]],
                    "kind": "power",
                }
            ),
        ],
    )
    r = validate_graph(g)
    assert not r.valid
    assert any("terminalu from" in e for e in r.errors)


def test_graph_rules_has_keys() -> None:
    rules = graph_rules()
    assert "snap_tol_min" in rules
    assert "wire_axis_tol_deg" in rules
