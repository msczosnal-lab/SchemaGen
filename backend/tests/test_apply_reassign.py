"""Testy apply_reassign zapisu do GT v2 (prompt 027)."""

from __future__ import annotations

from backend import db, gt_store
from backend.db import load_schematic_graph, rebuild_cache_from_gt
from backend.models.schematic_graph import SchematicGraph
from scripts.apply_reassign import _delete_symbols, _load_page_graph, _retag_symbol


def _graph(page_id: str, sym_id: str, cls: str = "relay") -> dict:
    return {
        "version": 2,
        "page_id": page_id,
        "image_width": 100,
        "image_height": 100,
        "symbols": [
            {
                "id": sym_id,
                "type": cls,
                "tag": cls,
                "bbox": [10, 10, 30, 30],
                "terminals": [{"id": "t1", "x": 0.5, "y": 0.5, "name": ""}],
            }
        ],
        "lines": [
            {
                "id": "ln1",
                "from": f"{sym_id}:t1",
                "to": "other:t1",
                "vertices": [],
                "kind": "power",
            }
        ],
    }


def test_retag_and_delete_helpers():
    g = SchematicGraph.model_validate(_graph("p1", "s1"))
    _retag_symbol(g.symbols[0], "przekaznik")
    assert g.symbols[0].type == "przekaznik"
    assert g.symbols[0].tag == "przekaznik"
    n = _delete_symbols(g, {"s1"})
    assert n == 1
    assert g.symbols == []
    assert g.lines == []


def test_load_and_save_gt_v2(tmp_path, monkeypatch):
    db_path = tmp_path / "test.db"
    gt_dir = tmp_path / "gt"
    gt_dir.mkdir(exist_ok=True)
    import backend.paths as paths_mod
    import backend.db as db_mod

    monkeypatch.setattr(paths_mod, "DB_PATH", db_path)
    monkeypatch.setattr(paths_mod, "GT", gt_dir)
    monkeypatch.setattr(db_mod, "DB_PATH", db_path)
    db_mod.init_db()

    page_id = "p_test"
    sym_id = "element_1"
    db.save_schematic_graph(page_id, _graph(page_id, sym_id, "relay"))

    graph = _load_page_graph(page_id)
    assert graph is not None
    _retag_symbol(graph.symbols[0], "przekaznik")
    db.save_schematic_graph(page_id, graph.model_dump(mode="json", by_alias=True))
    rebuild_cache_from_gt()

    raw = gt_store.read_gt_json(page_id)
    assert raw is not None
    assert raw["symbols"][0]["type"] == "przekaznik"
    cached = load_schematic_graph(page_id)
    assert cached["symbols"][0]["type"] == "przekaznik"
