"""Testy konwersji SchemaModel → SchematicGraph v2."""

from __future__ import annotations

from backend.models.schema import (
    Component,
    Connection,
    GraphicLine,
    SchemaMeta,
    SchemaModel,
    Terminal,
)
from backend.validate.diff_metrics import diff_graph, diff_graph_lines
from labeler.graph_compile import graph_to_schema
from labeler.schema_to_graph import schema_to_graph


def _sample_schema() -> SchemaModel:
    return SchemaModel(
        meta=SchemaMeta(source="t", page=0),
        components=[
            Component(
                id="k1",
                type="cewka_przekaznika",
                tag="-K1",
                bbox=[100, 100, 200, 200],
                terminals=[Terminal(id="1", x=1.0, y=0.5)],
            ),
            Component(
                id="f1",
                type="bezpiecznik",
                tag="-F1",
                bbox=[400, 100, 500, 200],
                terminals=[Terminal(id="2", x=0.0, y=0.5)],
            ),
        ],
        graphic_lines=[
            GraphicLine(
                id="gl_0",
                points=[[200, 150], [400, 150]],
                role="wire",
            )
        ],
        connections=[
            Connection.model_validate(
                {"from": "k1:1", "to": "f1:2", "kind": "power"}
            )
        ],
    )


def test_schema_to_graph_symbols_and_line() -> None:
    schema = _sample_schema()
    graph = schema_to_graph(schema, "t", 1000, 800)
    assert len(graph.symbols) == 2
    assert graph.symbols[0].type == "cewka_przekaznika"
    assert len(graph.lines) == 1
    assert graph.lines[0].from_ref == "k1:1"
    assert graph.lines[0].to == "f1:2"
    assert graph.lines[0].kind == "power"


def test_schema_to_graph_roundtrip_via_compile() -> None:
    schema = _sample_schema()
    graph = schema_to_graph(schema, "t", 1000, 800)
    back = graph_to_schema(graph)
    assert len(back.components) == 2
    assert len(back.connections) == 1
    assert back.connections[0].from_ref == "k1:1"


def test_diff_graph_lines_match() -> None:
    schema = _sample_schema()
    gt = schema_to_graph(schema, "t", 1000, 800)
    draft = schema_to_graph(schema, "t", 1000, 800)
    d = diff_graph_lines(gt, draft)
    assert d["match"] == 1
    assert d["f1"] == 1.0


def test_diff_graph_detects_missing_symbol() -> None:
    schema = _sample_schema()
    gt = schema_to_graph(schema, "t", 1000, 800)
    draft = schema_to_graph(schema, "t", 1000, 800)
    draft.symbols = draft.symbols[:1]
    d = diff_graph(gt, draft)
    assert d["symbols"]["match"] == 1
    assert d["symbols"]["gt_count"] == 2
    assert len(d["fn_bboxes"]) == 1
