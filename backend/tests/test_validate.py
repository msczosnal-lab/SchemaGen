"""Testy walidacji i modeli."""

from pathlib import Path

import pytest

from backend.models.schema import SchemaModel
from backend.validate.rules_engine import RulesEngine

FIXTURE = Path(__file__).resolve().parents[2] / "schema" / "fixtures" / "page1_expected.json"


def test_fixture_loads() -> None:
    model = SchemaModel.model_validate_json(FIXTURE.read_text(encoding="utf-8"))
    assert any(c.id == "M1" for c in model.components)
    assert len(model.graphic_lines) >= 1


def test_validate_approved_on_fixture() -> None:
    model = SchemaModel.model_validate_json(FIXTURE.read_text(encoding="utf-8"))
    report = RulesEngine().validate(model)
    assert report.approved
    assert "PE" not in str(report.errors)


def test_validate_fails_empty() -> None:
    report = RulesEngine().validate(SchemaModel())
    assert not report.approved
