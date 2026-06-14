from __future__ import annotations

from typing import Protocol

from backend.models.detection import SymbolDetection
from backend.models.schema import SchemaModel


class SymbolDetectorProtocol(Protocol):
    def detect(self, image_path: str) -> list[SymbolDetection]: ...


class RecognizerProtocol(Protocol):
    def recognize(self, input_path: str) -> SchemaModel: ...
