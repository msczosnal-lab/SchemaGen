"""Testy konwersji SchemaModel → SchematicGraph v2."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from backend.models.schema import (
    Component,
    Connection,
    GraphicLine,
    SchemaMeta,
    SchemaModel,
    Terminal,
)
from backend.models.schematic_graph import SchematicGraph
from backend.validate.diff_metrics import diff_graph, diff_graph_lines
from labeler.graph_compile import graph_to_schema
from labeler.schema_to_graph import schema_to_graph

_GT_DIR = Path(__file__).resolve().parents[2] / "gt"


def _gt_files() -> list[Path]:
    return sorted(_GT_DIR.glob("*.json")) if _GT_DIR.is_dir() else []


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


@pytest.mark.parametrize("gt_path", _gt_files(), ids=lambda p: p.stem)
def test_real_gt_roundtrip_symbols_preserved(gt_path: Path) -> None:
    """GT v2 (realny plik) -> SchemaModel -> schema_to_graph: symbole 1:1, linie OD-DO nie znikaja."""
    import json as _json
    raw = _json.loads(gt_path.read_text(encoding="utf-8"))
    gt = SchematicGraph.model_validate(raw)
    if not gt.symbols:
        pytest.skip(f"{gt_path.name}: pusty GT")
    schema = graph_to_schema(gt)
    back = schema_to_graph(schema, gt.page_id, gt.image_width, gt.image_height)
    assert len(back.symbols) == len(gt.symbols), "utrata symboli"
    assert {s.id for s in back.symbols} == {s.id for s in gt.symbols}
    d = diff_graph_lines(gt, back)
    assert d["match"] == d["gt_count"], f"{gt_path.name}: linie zgubione {d['match']}/{d['gt_count']} only_gt={d['only_gt'][:3]}"


def test_diff_graph_lines_id_remap_f1_perfect() -> None:
    """Ta sama topologia przy roznych id symboli/terminali -> F1=1.0 (remap IoU)."""
    from backend.models.schematic_graph import GraphLine, GraphSymbol, SchematicGraph
    from backend.models.schema import Terminal

    def _graph(sid_a, sid_b, ta, tb) -> SchematicGraph:
        return SchematicGraph(
            page_id="t",
            image_width=1000,
            image_height=800,
            symbols=[
                GraphSymbol(
                    id=sid_a, type="relay", bbox=[100, 100, 200, 200],
                    terminals=[Terminal(id=ta, x=1.0, y=0.5)],
                ),
                GraphSymbol(
                    id=sid_b, type="fuse", bbox=[400, 100, 500, 200],
                    terminals=[Terminal(id=tb, x=0.0, y=0.5)],
                ),
            ],
            lines=[GraphLine.model_validate(
                {"id": "L0", "from": f"{sid_a}:{ta}", "to": f"{sid_b}:{tb}", "kind": "power"}
            )],
        )

    gt = _graph("k1", "f1", "1", "2")
    draft = _graph("sym_0", "sym_1", "A", "B")  # inne id symboli i terminali
    d = diff_graph_lines(gt, draft)
    assert d["match"] == 1, d
    assert d["f1"] == 1.0, d


def test_schema_to_graph_listwa_from_connection_potential() -> None:
    schema = SchemaModel(
        meta=SchemaMeta(source="t"),
        components=[
            Component(
                id="z1",
                type="zlaczka",
                bbox=[0, 0, 10, 10],
                terminals=[Terminal(id="1", x=0, y=0.5)],
            ),
            Component(
                id="r1",
                type="relay",
                bbox=[50, 0, 60, 10],
                terminals=[Terminal(id="1", x=0, y=0.5)],
            ),
        ],
        connections=[
            Connection.model_validate(
                {
                    "from": "z1:1",
                    "to": "r1:1",
                    "kind": "power",
                    "potential": "S24VDC",
                }
            )
        ],
    )
    graph = schema_to_graph(schema, "t", 100, 100)
    z1 = next(s for s in graph.symbols if s.id == "z1")
    assert z1.listwa == "S24VDC"


def test_diff_graph_detects_missing_symbol() -> None:
    schema = _sample_schema()
    gt = schema_to_graph(schema, "t", 1000, 800)
    draft = schema_to_graph(schema, "t", 1000, 800)
    draft.symbols = draft.symbols[:1]
    d = diff_graph(gt, draft)
    assert d["symbols"]["match"] == 1
    assert d["symbols"]["gt_count"] == 2
    assert len(d["fn_bboxes"]) == 1
