# COWORK_TASK: sync/prompts/004-graph-builder.md

"""Budowa grafu polaczen z detekcji + OCR + linii."""

from __future__ import annotations

from backend.models.schema import SchemaModel
from backend.recognize.ocr_engine import PaddleOcrEngine
from backend.recognize.symbol_detector import OnnxSymbolDetector
from backend.recognize.line_classifier import LineClassifier
from backend.recognize.line_tracer import LineTracer


class GraphBuilder:
    def __init__(
        self,
        detector: OnnxSymbolDetector | None = None,
        ocr: PaddleOcrEngine | None = None,
        tracer: LineTracer | None = None,
        classifier: LineClassifier | None = None,
    ) -> None:
        self._detector = detector
        self._ocr = ocr
        self._tracer = tracer
        self._classifier = classifier

    def build(self, image_path: str, source: str = "") -> SchemaModel:
        raise NotImplementedError(
            "COWORK: detect + OCR + line trace/classify -> SchemaModel; "
            "connections tylko z graphic_lines role wire|bus"
        )
