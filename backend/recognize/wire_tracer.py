"""DEPRECATED: uzyj line_tracer.LineTracer — linia != polaczenie."""

from backend.recognize.line_tracer import LineSegment as WireSegment
from backend.recognize.line_tracer import LineTracer as WireTracer

__all__ = ["WireSegment", "WireTracer"]
