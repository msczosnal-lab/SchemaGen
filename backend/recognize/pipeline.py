"""Pipeline rozpoznawania offline."""

from __future__ import annotations

import json
from pathlib import Path

from backend.models.schema import SchemaMeta, SchemaModel
from backend.paths import MODELS, REGISTRY_PATH
from backend.recognize.graph_builder import GraphBuilder


def _default_model_path() -> str:
    if REGISTRY_PATH.exists():
        registry = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
        active = registry.get("active")
        if active and active in registry.get("versions", {}):
            return registry["versions"][active]["onnx_path"]
    candidates = list(MODELS.glob("*.onnx"))
    if candidates:
        return str(candidates[0])
    return ""


class OfflineRecognizer:
    """PDF/obraz -> SchemaModel (ONNX + OCR + CV)."""

    def __init__(self, model_path: str | None = None) -> None:
        self._model_path = model_path or _default_model_path()
        self._builder = GraphBuilder()

    def recognize(self, input_path: str, progress=None) -> SchemaModel:
        from backend.ingest import normalize_image_path

        image = normalize_image_path(input_path)
        if self._model_path:
            try:
                return self._builder.build(
                    str(image), source=str(input_path), progress=progress
                )
            except NotImplementedError:
                pass
        return SchemaModel(
            meta=SchemaMeta(source=str(input_path), page=0, model_version="stub"),
            components=[],
            connections=[],
        )


def recognize_file(
    input_path: str, output_path: str | None = None, progress=None
) -> SchemaModel:
    recognizer = OfflineRecognizer()
    model = recognizer.recognize(input_path, progress=progress)
    if output_path:
        Path(output_path).write_text(
            model.model_dump_json(by_alias=True, indent=2),
            encoding="utf-8",
        )
    return model
