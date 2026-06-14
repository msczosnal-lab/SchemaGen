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
