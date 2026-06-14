# COWORK_TASK: sync/prompts/003-wire-tracer.md

"""Tracing linii polaczen — OpenCV (Hough + morfologia)."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class WireSegment:
    x1: float
    y1: float
    x2: float
    y2: float


class WireTracer:
    def trace(self, image_path: str) -> list[WireSegment]:
        raise NotImplementedError("COWORK: OpenCV wire tracing")
