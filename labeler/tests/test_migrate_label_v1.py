"""Testy migracji LabelRecord v1 → SchematicGraph v2 (bbox + terminale, bez linii)."""

from __future__ import annotations

from backend.models.label import (
    BboxAnnotation,
    ConnectionAnnotation,
    LabelRecord,
    LineAnnotation,
    Terminal as LabelTerminal,
)
from labeler.migrate_label_v1 import label_record_to_graph, migrate_page


def test_label_record_to_graph_bbox_and_terminals_only():
    record = LabelRecord(
        page_id="t_page",
        image_path="t_page.png",
        image_width=1000,
        image_height=800,
        bboxes=[
            BboxAnnotation(
                id="b1",
                class_name="element",
                x=10,
                y=20,
                width=100,
                height=50,
                tag="złączka",
                terminals=[LabelTerminal(id="L", x=0.0, y=0.5)],
            ),
            BboxAnnotation(
                id="b2",
                class_name="mostek",
                x=200,
                y=20,
                width=30,
                height=30,
                tag="",
                terminals=[
                    LabelTerminal(id="1", x=0.0, y=0.5),
                    LabelTerminal(id="2", x=1.0, y=0.5),
                ],
            ),
        ],
        lines=[
            LineAnnotation(id="wire_old", points=[[0, 0], [100, 0]], role="wire"),
        ],
        connections=[
            ConnectionAnnotation(id="c1", **{"from": "b1:L"}, to="b2:1", kind="power"),
        ],
    )

    graph = label_record_to_graph(record)

    assert graph.page_id == "t_page"
    assert graph.image_width == 1000
    assert graph.lines == []
    assert len(graph.symbols) == 2

    sym0 = graph.symbols[0]
    assert sym0.id == "b1"
    assert sym0.type == "zlaczka"
    assert sym0.tag == "złączka"
    assert sym0.bbox == [10, 20, 110, 70]
    assert len(sym0.terminals) == 1
    assert sym0.terminals[0].id == "L"

    sym1 = graph.symbols[1]
    assert sym1.type == "mostek"
    assert len(sym1.terminals) == 2


def test_migrate_page_saves_without_lines(tmp_path, monkeypatch):
    db_path = tmp_path / "test.db"
    from backend import db as db_mod
    import backend.paths as paths_mod

    monkeypatch.setattr(db_mod, "DB_PATH", db_path)
    monkeypatch.setattr(paths_mod, "DB_PATH", db_path)
    db_mod.init_db()

    page = "migrate_test_page"
    record = LabelRecord(
        page_id=page,
        image_path=f"{page}.png",
        image_width=500,
        image_height=400,
        bboxes=[
            BboxAnnotation(
                id="x1",
                class_name="element",
                x=0,
                y=0,
                width=10,
                height=10,
                tag="bezpiecznik",
            ),
        ],
    )
    db_mod.save_annotation(page, record.model_dump())

    report = migrate_page(page)
    assert report.status == "ok"
    assert report.symbols == 1
    assert report.lines == 0
    assert report.terminals == 0
    assert report.symbols_without_terminals == ["x1"]

    raw = db_mod.load_schematic_graph(page)
    assert raw is not None
    assert raw["lines"] == []
    assert len(raw["symbols"]) == 1
    assert raw["symbols"][0]["type"] == "bezpiecznik"


def test_migrate_page_skips_existing_graph(tmp_path, monkeypatch):
    db_path = tmp_path / "test.db"
    from backend import db as db_mod
    import backend.paths as paths_mod

    monkeypatch.setattr(db_mod, "DB_PATH", db_path)
    monkeypatch.setattr(paths_mod, "DB_PATH", db_path)
    db_mod.init_db()

    page = "skip_page"
    db_mod.save_annotation(
        page,
        LabelRecord(
            page_id=page,
            image_path="x.png",
            image_width=100,
            image_height=100,
            bboxes=[
                BboxAnnotation(
                    id="a",
                    class_name="element",
                    x=1,
                    y=1,
                    width=2,
                    height=2,
                    tag="zlaczka",
                ),
            ],
        ).model_dump(),
    )
    db_mod.save_schematic_graph(
        page,
        {
            "version": 2,
            "page_id": page,
            "image_width": 100,
            "image_height": 100,
            "symbols": [],
            "lines": [],
        },
    )

    report = migrate_page(page)
    assert report.status == "skipped"
    assert "force" in report.reason
