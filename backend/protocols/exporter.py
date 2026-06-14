from __future__ import annotations

from typing import Protocol

from backend.models.label import LabelRecord


class LabelExporterProtocol(Protocol):
    def export_yolo(self, record: LabelRecord, output_dir: str) -> str: ...

    def to_schema_model(self, record: LabelRecord) -> "backend.models.schema.SchemaModel": ...
