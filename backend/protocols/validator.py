from __future__ import annotations

from typing import Protocol

from backend.models.schema import SchemaModel, ValidationReport


class ValidatorProtocol(Protocol):
    def validate(
        self,
        model: SchemaModel,
        ground_truth: SchemaModel | None = None,
    ) -> ValidationReport: ...
