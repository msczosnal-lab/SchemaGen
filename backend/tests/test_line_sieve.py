"""Testy sita linii — obramowki bbox -> frame, tekst -> other, przewody zostaja."""

from backend.models.schema import Component, GraphicLine
from backend.recognize.line_classifier import LineClassifier
from backend.recognize.line_sieve import apply_sieve

# Symbol: bbox [100,100,300,200] (x1,y1,x2,y2)
COMP = Component(id="sym_0", type="relay", bbox=[100, 100, 300, 200], source="yolo")


def _wire(pts) -> GraphicLine:
    return GraphicLine(id="gl", points=pts, role="wire")


def test_top_edge_demoted_to_frame() -> None:
    # linia wzdluz gornej krawedzi (y=100, x 100..300) = obramowka
    edge = _wire([[100, 100], [300, 100]])
    [out] = apply_sieve([edge], [COMP], [], edge_tol=6.0)
    assert out.role == "frame"
    assert not LineClassifier.is_connection_candidate(out)


def test_left_edge_demoted_to_frame() -> None:
    edge = _wire([[100, 100], [100, 200]])  # lewy bok (x=100, y 100..200)
    [out] = apply_sieve([edge], [COMP], [], edge_tol=6.0)
    assert out.role == "frame"


def test_perpendicular_wire_touching_edge_stays_wire() -> None:
    # przewod dotyka prawej krawedzi (x=300) punktowo i idzie w prawo (poziom)
    wire = _wire([[300, 150], [400, 150]])
    [out] = apply_sieve([wire], [COMP], [], edge_tol=6.0)
    assert out.role == "wire"
    assert LineClassifier.is_connection_candidate(out)


def test_wire_far_from_box_stays_wire() -> None:
    wire = _wire([[500, 500], [600, 500]])
    [out] = apply_sieve([wire], [COMP], [], edge_tol=6.0)
    assert out.role == "wire"


def test_short_segment_in_text_bbox_demoted_other() -> None:
    # krotki segment wewnatrz bbox tekstu OCR
    seg = _wire([[410, 405], [430, 405]])
    text_bbox = [400, 400, 460, 420]
    [out] = apply_sieve([seg], [COMP], [text_bbox], edge_tol=6.0)
    assert out.role == "other"
    assert not LineClassifier.is_connection_candidate(out)


def test_non_candidate_untouched() -> None:
    stroke = GraphicLine(id="gl", points=[[100, 100], [300, 100]], role="device_stroke")
    [out] = apply_sieve([stroke], [COMP], [], edge_tol=6.0)
    assert out.role == "device_stroke"  # nie ruszamy nie-kandydatow


def test_bus_along_edge_demoted() -> None:
    bus = GraphicLine(id="gl", points=[[100, 200], [300, 200]], role="bus")  # dolny bok
    [out] = apply_sieve([bus], [COMP], [], edge_tol=6.0)
    assert out.role == "frame"
