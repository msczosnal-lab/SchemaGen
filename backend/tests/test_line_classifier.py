"""Testy klasyfikacji linii."""

from backend.models.schema import GraphicLine
from backend.recognize.line_classifier import LineClassifier


def test_connection_candidate_wire_and_bus() -> None:
    wire = GraphicLine(id="w", points=[[0, 0], [1, 1]], role="wire")
    bus = GraphicLine(id="b", points=[[0, 0], [1, 1]], role="bus")
    assert LineClassifier.is_connection_candidate(wire)
    assert LineClassifier.is_connection_candidate(bus)


def test_connection_candidate_rejects_device_stroke() -> None:
    frame = GraphicLine(id="f", points=[[0, 0], [1, 1]], role="device_stroke")
    crossing = GraphicLine(id="c", points=[[0, 0], [1, 1]], role="crossing")
    assert not LineClassifier.is_connection_candidate(frame)
    assert not LineClassifier.is_connection_candidate(crossing)
