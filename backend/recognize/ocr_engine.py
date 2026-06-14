# COWORK_TASK: sync/prompts/002-ocr-engine.md

"""OCR tekstu schematu — PaddleOCR offline."""

from __future__ import annotations


class PaddleOcrEngine:
    def __init__(self, use_gpu: bool = True) -> None:
        self._use_gpu = use_gpu
        self._engine = None

    def extract_text(self, image_path: str) -> list[dict]:
        """Zwraca liste {text, x, y, width, height, confidence}."""
        raise NotImplementedError("COWORK: PaddleOCR extract")
