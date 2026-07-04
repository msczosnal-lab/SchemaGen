"""Testy eksportu labelera (multi-class: klasa z pola `tag`)."""

import tempfile
from pathlib import Path

from labeler.export import export_yolo, label_to_schema
from backend.models.label import BboxAnnotation, LabelRecord, Terminal


def test_label_to_schema() -> None:
    record = LabelRecord(
        page_id="test",
        image_path="test.png",
        image_width=400,
        image_height=300,
        bboxes=[
            BboxAnnotation(id="M1", class_name="motor", x=10, y=10, width=50, height=50, tag="-M1")
        ],
    )
    model = label_to_schema(record)
    assert model.components[0].type == "motor"


def test_label_to_schema_maps_terminals() -> None:
    record = LabelRecord(
        page_id="t",
        image_path="t.png",
        bboxes=[
            BboxAnnotation(
                id="X1", class_name="terminal_block", x=0, y=0, width=100, height=20,
                terminals=[Terminal(id="1", x=0.2, y=0.5), Terminal(id="2", x=0.8, y=0.5)],
            )
        ],
    )
    comp = label_to_schema(record).components[0]
    assert [t.id for t in comp.terminals] == ["1", "2"]
    assert comp.terminals[0].x == 0.2 and comp.terminals[0].y == 0.5


def test_export_yolo_line() -> None:
    record = LabelRecord(
        page_id="test_yolo",
        image_path="test.png",
        image_width=100,
        image_height=100,
        bboxes=[BboxAnnotation(id="a", class_name="element", x=10, y=10, width=20, height=20,
                               tag="silnik")],
    )
    with tempfile.TemporaryDirectory() as tmp:
        path = export_yolo(record, Path(tmp))
        text = path.read_text(encoding="utf-8").strip()
        assert text
        parts = text.split()
        assert len(parts) == 5


def test_label_to_schema_hierarchy() -> None:
    record = LabelRecord(
        page_id="nested",
        image_path="nested.png",
        image_width=400,
        image_height=400,
        bboxes=[
            BboxAnnotation(id="element_1", class_name="element", x=0, y=0, width=200, height=200,
                           tag="Blok zasilania RUPS1"),
            BboxAnnotation(id="element_2", class_name="element", x=50, y=50, width=30, height=70,
                           tag="Rozlacznik -11"),
        ],
    )
    model = label_to_schema(record)
    child = next(c for c in model.components if c.id == "element_2")
    assert child.parent_id == "element_1"
    assert child.depth == 1
    assert child.rel_bbox
    assert any(
        r.relation == "contains" and r.from_id == "element_1" and r.to_id == "element_2"
        for r in model.spatial_relations
    )


def test_export_yolo_keeps_all_tagged_bboxes() -> None:
    record = LabelRecord(
        page_id="nested_yolo",
        image_path="nested.png",
        image_width=400,
        image_height=400,
        bboxes=[
            BboxAnnotation(id="element_1", class_name="element", x=0, y=0, width=200, height=200,
                           tag="silnik"),
            BboxAnnotation(id="element_2", class_name="element", x=50, y=50, width=30, height=30,
                           tag="rozłącznik"),
        ],
    )
    with tempfile.TemporaryDirectory() as tmp:
        path = export_yolo(record, Path(tmp))
        lines = [ln for ln in path.read_text(encoding="utf-8").splitlines() if ln.strip()]
        assert len(lines) == 2  # oba otagowane bboxy
        # dwie rozne klasy -> rozne class_id
        assert {ln.split()[0] for ln in lines} == {"0", "1"}


def test_export_yolo_empty_tag_skipped() -> None:
    """Multi-class: nieprzypisany bbox (pusty tag) NIE idzie do treningu."""
    record = LabelRecord(
        page_id="unassigned",
        image_path="test.png",
        image_width=100,
        image_height=100,
        bboxes=[
            BboxAnnotation(id="u1", class_name="element", x=5, y=5, width=40, height=40, tag=""),
        ],
    )
    with tempfile.TemporaryDirectory() as tmp:
        path = export_yolo(record, Path(tmp))
        text = path.read_text(encoding="utf-8").strip()
        assert text == ""  # pominiety


def test_label_to_schema_context_assignments() -> None:
    record = LabelRecord(
        page_id="ctx",
        image_path="ctx.png",
        image_width=200,
        image_height=200,
        bboxes=[
            BboxAnnotation(id="z1", class_name="element", x=10, y=50, width=6, height=6,
                           tag="złączka"),
            BboxAnnotation(id="lst", class_name="element", x=5, y=48, width=40, height=10,
                           tag="listwa złączek"),
        ],
    )
    model = label_to_schema(record)
    assert model.context_assignments
    z1 = next(a for a in model.context_assignments if a.bbox_id == "z1")
    assert z1.role == "zlaczka"
    assert z1.anchor_id == "lst"


def test_export_yolo_contextual_tag_skipped() -> None:
    """Klasy kontekstowe (train-classes.yaml) zostaja w GT, nie w YOLO."""
    record = LabelRecord(
        page_id="ctx",
        image_path="test.png",
        image_width=100,
        image_height=100,
        bboxes=[
            BboxAnnotation(id="a", class_name="element", x=10, y=10, width=20, height=20,
                           tag="silnik"),
            BboxAnnotation(id="b", class_name="element", x=40, y=10, width=10, height=10,
                           tag="złącze"),
        ],
    )
    with tempfile.TemporaryDirectory() as tmp:
        path = export_yolo(record, Path(tmp))
        lines = [ln for ln in path.read_text(encoding="utf-8").splitlines() if ln.strip()]
        assert len(lines) == 1
        assert lines[0].split()[0] == "0"  # tylko silnik -> motor
