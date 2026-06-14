# COWORK_TASK: sync/prompts/001-symbol-detector.md

"""Detekcja symboli — YOLO ONNX na RTX 2080."""

from __future__ import annotations

from backend.models.detection import SymbolDetection


class OnnxSymbolDetector:
    """Detekcja symboli schematu — YOLO ONNX."""

    def __init__(self, model_path: str, class_map: dict[str, int] | None = None) -> None:
        self._model_path = model_path
        self._class_map = class_map or {}
        self._session = None

    def _ensure_session(self) -> None:
        if self._session is not None:
            return
        raise NotImplementedError("COWORK: zaladuj onnxruntime-gpu session")

    def detect(self, image_path: str) -> list[SymbolDetection]:
        """Zwraca bbox + class_id + confidence dla jednej strony PNG."""
        self._ensure_session()
        raise NotImplementedError("COWORK: implementacja inferencji ONNX")
