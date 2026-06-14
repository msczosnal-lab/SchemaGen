# COWORK_TASK: sync/prompts/004-graph-builder.md

"""Budowa grafu polaczen z detekcji + OCR + linii."""

from __future__ import annotations

from backend.models.schema import SchemaModel
from backend.recognize.ocr_engine import PaddleOcrEngine
from backend.recognize.symbol_detector import OnnxSymbolDetector
from backend.recognize.wire_tracer import WireTracer


class GraphBuilder:
    def __init__(
        self,
        detector: OnnxSymbolDetector | None = None,
        ocr: PaddleOcrEngine | None = None,
        tracer: WireTracer | None = None,
    ) -> None:
        self._detector = detector
        self._ocr = ocr
        self._tracer = tracer

    def build(self, image_path: str, source: str = "") -> SchemaModel:
        raise NotImplementedError("COWORK: polacz detect + OCR + wire trace w SchemaModel")
