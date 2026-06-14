"""Silnik walidacji regułowej + diff ground truth."""

from __future__ import annotations

import json
from pathlib import Path

from backend.models.schema import SchemaModel, ValidationReport
from backend.paths import VALIDATION_RULES


def _load_rules() -> dict:
    if VALIDATION_RULES.exists():
        return json.loads(VALIDATION_RULES.read_text(encoding="utf-8"))
    return {}


def _model_text(model: SchemaModel) -> str:
    return model.model_dump_json(by_alias=True).upper()


def _diff_ground_truth(pred: SchemaModel, gt: SchemaModel) -> list[str]:
    diffs: list[str] = []
    pred_ids = {c.id for c in pred.components}
    gt_ids = {c.id for c in gt.components}
    missing = gt_ids - pred_ids
    extra = pred_ids - gt_ids
    for comp_id in sorted(missing):
        diffs.append(f"Brak komponentu w predykcji: {comp_id}")
    for comp_id in sorted(extra):
        diffs.append(f"Nadmiarowy komponent w predykcji: {comp_id}")

    pred_conn = {(c.from_ref, c.to) for c in pred.connections}
    gt_conn = {(c.from_ref, c.to) for c in gt.connections}
    for conn in sorted(gt_conn - pred_conn):
        diffs.append(f"Brak polaczenia: {conn[0]} -> {conn[1]}")
    return diffs


def _check_user_intent(model: SchemaModel, rules: dict) -> list[str]:
    warnings: list[str] = []
    intent = model.user_intent
    if not intent:
        return warnings
    expected = rules.get("expected_components_for_intent", {})
    drive = intent.drive_type
    if drive and drive in expected:
        required_types = set(expected[drive])
        found_types = {c.type for c in model.components}
        for req in required_types - found_types:
            warnings.append(f"Intencja '{drive}' wymaga typu '{req}' — brak w modelu")
    return warnings


class RulesEngine:
    def validate(
        self,
        model: SchemaModel,
        ground_truth: SchemaModel | None = None,
    ) -> ValidationReport:
        rules = _load_rules()
        text = _model_text(model)
        errors: list[str] = []
        warnings: list[str] = []

        for potential in rules.get("required_potentials", []):
            if potential.upper() not in text:
                errors.append(f"Brak potencjalu: {potential}")

        for marker in rules.get("required_connection_markers", []):
            if marker.upper() not in text:
                warnings.append(f"Brak oznaczenia uzwojenia/polaczenia: {marker}")

        motor_tag = rules.get("motor_tag", "")
        if motor_tag and motor_tag.upper() not in text:
            warnings.append(f"Brak tagu silnika: {motor_tag}")

        if not model.components:
            errors.append("Model nie zawiera komponentow")

        warnings.extend(_check_user_intent(model, rules))

        gt_diff: list[str] = []
        if ground_truth:
            gt_diff = _diff_ground_truth(model, ground_truth)
            errors.extend(gt_diff)

        return ValidationReport(
            approved=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            ground_truth_diff=gt_diff,
        )


def validate_model(
    model_path: str | Path,
    ground_truth_path: str | Path | None = None,
    report_path: str | Path | None = None,
) -> ValidationReport:
    model = SchemaModel.model_validate_json(Path(model_path).read_text(encoding="utf-8"))
    gt = None
    if ground_truth_path:
        gt = SchemaModel.model_validate_json(Path(ground_truth_path).read_text(encoding="utf-8"))
    report = RulesEngine().validate(model, gt)
    if report_path:
        Path(report_path).write_text(report.model_dump_json(indent=2), encoding="utf-8")
    return report
