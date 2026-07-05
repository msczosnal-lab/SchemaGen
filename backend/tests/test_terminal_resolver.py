"""Testy TerminalResolver — wzorce z terminal-patterns.yaml + fallback."""

from backend.models.schema import Component, GraphicLine, Terminal
from backend.recognize.terminal_resolver import resolve


def _wire(pts) -> GraphicLine:
    return GraphicLine(id="gl", points=pts, role="wire")


def _zlaczka() -> Component:
    return Component(id="z1", type="zlaczka", bbox=[100, 100, 150, 180], source="yolo")


ZLACZKA_PATTERN = {
    "method": "line-contact",
    "expected": [
        {"edge": "left", "frac": 0.5, "required": True},
        {"edge": "right", "frac": 0.5, "required": True},
    ],
    "frac_tol": 0.15,
}


def test_zlaczka_pattern_creates_left_right_terminals() -> None:
    comp = _zlaczka()
    # przewody do lewej (x=100) i prawej (x=150) krawedzi
    lines = [
        _wire([[50, 140], [100, 140]]),
        _wire([[150, 140], [200, 140]]),
    ]
    terms = resolve(
        comp, lines, None, {"zlaczka": ZLACZKA_PATTERN},
        contact_tol=10, pattern_tol=10, merge_tol=10,
    )
    assert len(terms) == 2
    xs = sorted(round(t.x, 2) for t in terms)
    assert xs == [0.0, 1.0]
    assert all(abs(t.y - 0.5) < 0.01 for t in terms)


def test_unknown_class_falls_back_to_auto_terminals() -> None:
    comp = Component(id="r1", type="relay", bbox=[0, 0, 100, 50], source="yolo")
    lines = [_wire([[100, 25], [200, 25]])]
    terms = resolve(comp, lines, None, {}, contact_tol=10, pattern_tol=8, merge_tol=10)
    assert len(terms) == 1
    assert terms[0].x == 1.0


def test_existing_terminals_not_overwritten() -> None:
    comp = Component(
        id="z1", type="zlaczka", bbox=[0, 0, 100, 20], source="yolo",
        terminals=[Terminal(id="9", x=0.5, y=0.5)],
    )
    terms = resolve(
        comp, [], None, {"zlaczka": ZLACZKA_PATTERN},
        contact_tol=10, pattern_tol=8,
    )
    assert len(terms) == 1
    assert terms[0].id == "9"
