"""Testy grupowania wierszy i ContextResolver."""

from backend.geometry.row_layout import ContextResolver, Row, dedup_detections_by_row, group_into_rows
from backend.models.label import BboxAnnotation


def _b(id_: str, x: float, y: float, w: float, h: float, tag: str) -> BboxAnnotation:
    return BboxAnnotation(
        id=id_, class_name="element", x=x, y=y, width=w, height=h, tag=tag
    )


def test_group_into_rows_two_lines():
    bboxes = [
        _b("a", 10, 100, 8, 8, "złączka"),
        _b("b", 30, 102, 8, 8, "złączka"),
        _b("c", 10, 200, 8, 8, "złączka"),
    ]
    rows = group_into_rows(bboxes)
    assert len(rows) == 2
    assert {b.id for b in rows[0].bboxes} == {"a", "b"}
    assert {b.id for b in rows[1].bboxes} == {"c"}


def test_context_resolver_strip_with_anchor():
    bboxes = [
        _b("z1", 10, 50, 6, 6, "złączka"),
        _b("z2", 25, 51, 6, 6, "złączka"),
        _b("lst", 5, 48, 40, 10, "listwa złączek"),
    ]
    out = ContextResolver().resolve(bboxes)
    z1 = next(a for a in out if a.bbox_id == "z1")
    assert z1.role == "zlaczka"
    assert z1.anchor_id == "lst"
    assert z1.strip_kind == "listwa_zlaczek"


def test_context_resolver_cable_markers():
    bboxes = [
        _b("m1", 10, 80, 5, 5, "oznaczenie przewodu"),
        _b("m2", 22, 81, 5, 5, "oznaczenie przewodu"),
        _b("cab", 8, 78, 30, 8, "oznaczenie kabla"),
    ]
    out = ContextResolver().resolve(bboxes)
    m1 = next(a for a in out if a.bbox_id == "m1")
    assert m1.role == "oznaczenie_przewodu"
    assert m1.anchor_id == "cab"


class _FakeDet:
    def __init__(self, x, y, w, h, conf, name):
        self.x, self.y, self.width, self.height = x, y, w, h
        self.confidence = conf
        self.class_name = name


def test_dedup_row_overlapping_same_class():
    dets = [
        _FakeDet(10, 100, 20, 10, 0.9, "relay"),
        _FakeDet(12, 101, 20, 10, 0.4, "relay"),
        _FakeDet(100, 100, 20, 10, 0.8, "relay"),
    ]
    kept = dedup_detections_by_row(dets)
    assert len(kept) == 2
    confs = sorted(d.confidence for d in kept)
    assert confs == [0.8, 0.9]
