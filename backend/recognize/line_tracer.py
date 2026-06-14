# COWORK_TASK: sync/prompts/003-line-tracer-classifier.md

"""Wykrywanie linii graficznych na schemacie — OpenCV + klasyfikacja roli i koloru."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class LineSegment:
    x1: float
    y1: float
    x2: float
    y2: float
    detected_color: str = ""


class LineTracer:
    def trace(self, image_path: str) -> list[LineSegment]:
        raise NotImplementedError("COWORK: OpenCV line tracing (Hough + morfologia)")
