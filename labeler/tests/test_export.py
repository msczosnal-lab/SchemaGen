"""Testy eksportu labelera."""

from labeler.export import export_yolo, label_to_schema
from backend.models.label import BboxAnnotation, LabelRecord


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


def test_export_yolo_line() -> None:
    record = LabelRecord(
        page_id="test_yolo",
        image_path="test.png",
        image_width=100,
        image_height=100,
        bboxes=[BboxAnnotation(id="a", class_name="motor", x=10, y=10, width=20, height=20)],
    )
    import tempfile
    from pathlib import Path

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


def test_export_yolo_keeps_all_nested_bboxes() -> None:
    import tempfile
    from pathlib import Path

    record = LabelRecord(
        page_id="nested_yolo",
        image_path="nested.png",
        image_width=400,
        image_height=400,
        bboxes=[
            BboxAnnotation(id="element_1", class_name="element", x=0, y=0, width=200, height=200),
            BboxAnnotation(id="element_2", class_name="element", x=50, y=50, width=30, height=30),
        ],
    )
    with tempfile.TemporaryDirectory() as tmp:
        path = export_yolo(record, Path(tmp))
        lines = [ln for ln in path.read_text(encoding="utf-8").splitlines() if ln.strip()]
        assert len(lines) == 2  # oba bboxy mimo zagniezdzenia
