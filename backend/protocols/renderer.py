from __future__ import annotations

from typing import Protocol

from backend.models.schema import SchemaModel


class RendererProtocol(Protocol):
    def render(self, model: SchemaModel, output_path: str) -> str: ...
