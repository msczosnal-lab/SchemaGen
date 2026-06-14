# COWORK_TASK: sync/prompts/003-line-tracer-classifier.md

"""Klasyfikacja linii: rola (wire/bus/device_stroke/...) + grupa semantyczna z koloru."""

from __future__ import annotations

from backend.colors.palette import ColorPalette, load_palette
from backend.models.schema import GraphicLine
from backend.recognize.line_tracer import LineSegment


CONNECTION_ROLES = frozenset({"wire", "bus"})


class LineClassifier:
    def __init__(self, palette: ColorPalette | None = None) -> None:
        self._palette = palette or load_palette()

    def classify(self, segments: list[LineSegment]) -> list[GraphicLine]:
        raise NotImplementedError(
            "COWORK: segment -> GraphicLine (role, semantic_group, detected_color)"
        )

    @staticmethod
    def is_connection_candidate(line: GraphicLine) -> bool:
        return line.role in CONNECTION_ROLES
