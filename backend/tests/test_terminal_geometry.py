"""Testy geometrii terminali — przeciecie linii z krawedzia bbox."""

from backend.models.schema import Component, GraphicLine
from backend.recognize.terminal_geometry import line_bbox_edge_contacts
from backend.recognize.terminal_resolver import resolve

ZLACZKA_PATTERN = {
    "method": "line-contact",
    "expected": [
        {"edge": "left", "frac": 0.5, "required": True},
        {"edge": "right", "frac": 0.5, "required": True},
    ],
    "frac_tol": 0.15,
}


def _wire(pts) -> GraphicLine:
    return GraphicLine(id="gl", points=pts, role="wire")


def test_line_intersects_left_right_edges() -> None:
    comp = Component(id="z1", type="zlaczka", bbox=[100, 100, 150, 180], source="yolo")
    lines = [
        _wire([[50, 140], [100, 140]]),
        _wire([[150, 140], [200, 140]]),
    ]
    hits = line_bbox_edge_contacts(comp, lines, tol=5, merge_tol=5)
    xs = sorted(round(h[0], 1) for h in hits)
    assert xs == [100.0, 150.0]


def test_no_terminal_without_line_intersection() -> None:
    comp = Component(id="z1", type="zlaczka", bbox=[100, 100, 150, 180], source="yolo")
    terms = resolve(
        comp, [], None, {"zlaczka": ZLACZKA_PATTERN},
        contact_tol=10, pattern_tol=10,
    )
    assert terms == []


def test_bus_through_bbox_creates_edge_hits() -> None:
    """Szyna przecina lewa i prawa krawedz bbox — 2 kontakty."""
    comp = Component(id="z1", type="zlaczka", bbox=[100, 100, 150, 180], source="yolo")
    bus = _wire([[80, 140], [170, 140]])
    hits = line_bbox_edge_contacts(comp, [bus], tol=5, merge_tol=5)
    assert len(hits) == 2
