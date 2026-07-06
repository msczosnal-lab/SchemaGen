"""Testy modelu SchematicGraph v2 (roundtrip JSON)."""

from __future__ import annotations

import json

from backend.models.schema import Terminal
from backend.models.schematic_graph import GraphLine, GraphSymbol, SchematicGraph


def _sample_graph() -> SchematicGraph:
    return SchematicGraph(
        page_id="p027",
        image_width=4963,
        image_height=3509,
        symbols=[
            GraphSymbol(
                id="sym_k1",
                type="cewka_przekaznika",
                tag="-K1",
                bbox=[100, 200, 300, 400],
                terminals=[Terminal(id="1", x=0.0, y=0.5)],
            ),
        ],
        lines=[
            GraphLine.model_validate(
                {
                    "id": "L323",
                    "from": "sym_k1:1",
                    "to": "sym_k2:3",
                    "vertices": [[100, 300], [100, 250]],
                    "kind": "power",
                }
            ),
        ],
    )


def test_schematic_graph_roundtrip_json() -> None:
    g = _sample_graph()
    raw = g.model_dump(mode="json", by_alias=True)
    assert raw["version"] == 2
    assert raw["lines"][0]["from"] == "sym_k1:1"
    restored = SchematicGraph.model_validate(raw)
    assert restored.page_id == "p027"
    assert restored.symbols[0].terminals[0].id == "1"
    assert restored.lines[0].from_ref == "sym_k1:1"


def test_schematic_graph_json_load_alias() -> None:
    payload = {
        "version": 2,
        "page_id": "p040",
        "image_width": 1000,
        "image_height": 800,
        "symbols": [],
        "lines": [{"id": "L1", "from": "a:1", "to": "b:2", "kind": "link"}],
    }
    g = SchematicGraph.model_validate(json.loads(json.dumps(payload)))
    assert g.lines[0].kind == "link"
    assert g.lines[0].to == "b:2"
