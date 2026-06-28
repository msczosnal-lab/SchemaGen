"""Testy klasyfikacji linii."""

from backend.models.schema import GraphicLine
from backend.recognize.line_classifier import LineClassifier
from backend.recognize.line_tracer import LineSegment


def test_connection_candidate_only_wire() -> None:
    # ADR connection-model: "bus" wycofane -> tylko wire jest kandydatem na Connection
    wire = GraphicLine(id="w", points=[[0, 0], [1, 1]], role="wire")
    bus = GraphicLine(id="b", points=[[0, 0], [1, 1]], role="bus")
    assert LineClassifier.is_connection_candidate(wire)
    assert not LineClassifier.is_connection_candidate(bus)


def test_connection_candidate_rejects_device_stroke() -> None:
    frame = GraphicLine(id="f", points=[[0, 0], [1, 1]], role="device_stroke")
    crossing = GraphicLine(id="c", points=[[0, 0], [1, 1]], role="crossing")
    assert not LineClassifier.is_connection_candidate(frame)
    assert not LineClassifier.is_connection_candidate(crossing)


def test_classify_black_short_line_is_wire() -> None:
    seg = LineSegment(0, 0, 30, 0, detected_color="#000000")
    [line] = LineClassifier().classify([seg])
    assert line.role == "wire"
    assert line.semantic_group in ("cable", "pe_wire")  # czern -> kabel
    assert line.detected_color == "#000000"
    assert LineClassifier.is_connection_candidate(line)


def test_classify_purple_matches_inverter_device_stroke() -> None:
    seg = LineSegment(0, 0, 40, 40, detected_color="#9933FF")
    [line] = LineClassifier().classify([seg])
    assert line.semantic_group == "inverter"
    assert line.role == "device_stroke"
    assert not LineClassifier.is_connection_candidate(line)


def test_classify_long_axis_line_is_wire() -> None:
    # ADR: dluga linia osiowa NIE jest juz "bus" -> zostaje wire (szyne robi net-builder)
    seg = LineSegment(0, 5, 500, 5, detected_color="#000000")
    [line] = LineClassifier().classify([seg], bus_min_length=400)
    assert line.role == "wire"
    assert LineClassifier.is_connection_candidate(line)


def test_classify_dashed_group_sets_dash_role() -> None:
    # #666666 -> grupa dashed_aux (roles=[dash])
    seg = LineSegment(0, 0, 20, 0, detected_color="#666666")
    [line] = LineClassifier().classify([seg])
    assert line.role == "dash"
    assert line.style == "dashed"
    assert not LineClassifier.is_connection_candidate(line)
