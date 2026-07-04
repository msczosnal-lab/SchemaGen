from backend.geometry.bbox_layout import enrich_label_record
from backend.geometry.coord_scale import (
    detect_low_dpi_factor,
    detect_scale_factor,
    scale_label_record,
)
from backend.models.label import BboxAnnotation, LabelRecord, LineAnnotation, TextAnnotation


def test_scale_label_record_scales_all_geometry() -> None:
    record = LabelRecord(
        page_id="p001",
        image_path="p001.png",
        image_width=200,
        image_height=100,
        bboxes=[
            BboxAnnotation(
                id="a",
                class_name="element",
                x=10,
                y=20,
                width=30,
                height=40,
                tag="K1",
            )
        ],
        texts=[
            TextAnnotation(id="t1", text="ABC", x=5, y=6, width=10, height=8),
        ],
        lines=[
            LineAnnotation(id="l1", points=[[1, 2], [3, 4]]),
        ],
    )
    record = enrich_label_record(record)

    scaled = scale_label_record(record, 2.0)
    b = scaled.bboxes[0]
    assert b.x == 20.0 and b.y == 40.0 and b.width == 60.0 and b.height == 80.0
    assert scaled.texts[0].x == 10.0 and scaled.texts[0].y == 12.0
    assert scaled.lines[0].points == [[2.0, 4.0], [6.0, 8.0]]
    assert scaled.image_width == 400 and scaled.image_height == 200
    assert scaled.bboxes[0].rel_bbox == []


def test_detect_scale_factor_from_stored_dimensions() -> None:
    record = LabelRecord(
        page_id="p001",
        image_path="p001.png",
        image_width=200,
        image_height=100,
    )
    assert detect_scale_factor(record, actual_size=(400, 200)) == 2.0
    assert detect_scale_factor(record, actual_size=(200, 100)) is None


def test_detect_low_dpi_factor_when_extent_is_small() -> None:
    record = LabelRecord(
        page_id="p001",
        image_path="p001.png",
        image_width=400,
        image_height=200,
        bboxes=[
            BboxAnnotation(
                id="a",
                class_name="element",
                x=10,
                y=10,
                width=170,
                height=80,
            )
        ],
    )
    assert detect_low_dpi_factor(record) == 2.0

    record.bboxes[0].width = 300
    assert detect_low_dpi_factor(record) is None

    record.bboxes[0].width = 170
    record.bboxes[0].height = 30
    assert detect_low_dpi_factor(record) is None
