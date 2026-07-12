"""Testy analizy powodu pudła linii GT."""

from __future__ import annotations

from backend.models.schema import Terminal
from backend.models.schematic_graph import GraphLine, GraphSymbol, SchematicGraph
from backend.validate.line_failure_analysis import analyze_line_failures


def _graph(
    syms: list[GraphSymbol],
    lines: list[GraphLine],
) -> SchematicGraph:
    return SchematicGraph(
        page_id="t",
        image_width=1000,
        image_height=800,
        symbols=syms,
        lines=lines,
    )


def test_matched_line() -> None:
    sym_a = GraphSymbol(
        id="a",
        type="relay",
        bbox=[100, 100, 200, 200],
        terminals=[Terminal(id="1", x=1.0, y=0.5)],
    )
    sym_b = GraphSymbol(
        id="b",
        type="fuse",
        bbox=[400, 100, 500, 200],
        terminals=[Terminal(id="2", x=0.0, y=0.5)],
    )
    ln = GraphLine.model_validate(
        {"id": "L1", "from": "a:1", "to": "b:2", "kind": "power"}
    )
    gt = _graph([sym_a, sym_b], [ln])
    draft = _graph(
        [
            GraphSymbol(
                id="sym_0",
                type="relay",
                bbox=[100, 100, 200, 200],
                terminals=[Terminal(id="1", x=1.0, y=0.5)],
            ),
            GraphSymbol(
                id="sym_1",
                type="fuse",
                bbox=[400, 100, 500, 200],
                terminals=[Terminal(id="2", x=0.0, y=0.5)],
            ),
        ],
        [GraphLine.model_validate({"id": "d1", "from": "sym_0:1", "to": "sym_1:2", "kind": "power"})],
    )
    rep = analyze_line_failures(gt, draft)
    assert rep["matched"] == 1
    assert rep["reason_counts"] == {}


def test_symbol_missing_from() -> None:
    gt_sym = GraphSymbol(
        id="a",
        type="zlaczka",
        bbox=[100, 100, 150, 150],
        terminals=[Terminal(id="1", x=0.0, y=0.5)],
    )
    gt = _graph(
        [gt_sym],
        [GraphLine.model_validate({"id": "L1", "from": "a:1", "to": "a:1", "kind": "link"})],
    )
    draft = _graph([], [])
    rep = analyze_line_failures(gt, draft)
    assert rep["missed"] == 1
    assert rep["reason_counts"].get("symbol_missing_from", 0) >= 1


def test_topology_mismatch() -> None:
    gt = _graph(
        [
            GraphSymbol(id="z1", type="zlaczka", bbox=[0, 0, 10, 10], terminals=[Terminal(id="1", x=0, y=0.5)]),
            GraphSymbol(id="z2", type="zlaczka", bbox=[50, 0, 60, 10], terminals=[Terminal(id="1", x=1, y=0.5)]),
        ],
        [GraphLine.model_validate({"id": "L1", "from": "z1:1", "to": "z2:1", "kind": "link"})],
    )
    draft = _graph(
        [
            GraphSymbol(id="d1", type="zlaczka", bbox=[0, 0, 10, 10], terminals=[Terminal(id="1", x=0, y=0.5)]),
            GraphSymbol(id="d2", type="zlaczka", bbox=[50, 0, 60, 10], terminals=[Terminal(id="1", x=1, y=0.5)]),
            GraphSymbol(id="d3", type="relay", bbox=[100, 0, 110, 10], terminals=[Terminal(id="1", x=0, y=0.5)]),
        ],
        [
            GraphLine.model_validate({"id": "x1", "from": "d1:1", "to": "d3:1", "kind": "power"}),
            GraphLine.model_validate({"id": "x2", "from": "d2:1", "to": "d3:1", "kind": "power"}),
        ],
    )
    rep = analyze_line_failures(gt, draft)
    assert rep["missed"] == 1
    assert rep["lines"][0]["reason"] == "topology_mismatch"
