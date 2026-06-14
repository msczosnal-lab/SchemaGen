#!/usr/bin/env python3
"""Reguły walidacji CSV połączeń EPLAN — Faza 2."""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

RULES_PATH = Path(__file__).resolve().parents[2] / "config" / "validation-rules.json"


def load_rules() -> dict:
    if RULES_PATH.exists():
        return json.loads(RULES_PATH.read_text(encoding="utf-8"))
    return {
        "required_potentials": ["PE", "2L1"],
        "required_connection_markers": ["U", "V", "W"],
        "motor_tag": "=MACHINE+CABINET-M1",
    }


def read_csv_rows(csv_path: Path) -> list[dict[str, str]]:
    if not csv_path.exists():
        return []
    with csv_path.open(encoding="utf-8-sig", newline="") as handle:
        sample = handle.read(4096)
        handle.seek(0)
        try:
            dialect = csv.Sniffer().sniff(sample, delimiters=";,\t")
        except csv.Error:
            dialect = csv.excel
        reader = csv.DictReader(handle, dialect=dialect)
        return list(reader)


def validate(csv_path: Path) -> dict:
    rules = load_rules()
    rows = read_csv_rows(csv_path)
    text_blob = json.dumps(rows, ensure_ascii=False).upper()

    errors: list[str] = []
    warnings: list[str] = []

    for potential in rules.get("required_potentials", []):
        if potential.upper() not in text_blob:
            errors.append(f"Brak potencjału: {potential}")

    for marker in rules.get("required_connection_markers", []):
        if marker.upper() not in text_blob:
            warnings.append(f"Brak oznaczenia uzwojenia/połączenia: {marker}")

    motor_tag = rules.get("motor_tag", "")
    if motor_tag and motor_tag.upper() not in text_blob:
        warnings.append(f"Brak tagu silnika w CSV: {motor_tag}")

    if not rows:
        errors.append("Plik CSV jest pusty lub nieczytelny")

    approved = len(errors) == 0
    return {
        "approved": approved,
        "errors": errors,
        "warnings": warnings,
        "row_count": len(rows),
        "csv_path": str(csv_path),
        "rules_path": str(RULES_PATH),
    }


def main() -> int:
    if len(sys.argv) < 2:
        print("Użycie: validate_connections.py <connections.csv> [report.json]", file=sys.stderr)
        return 2

    csv_path = Path(sys.argv[1])
    report_path = Path(sys.argv[2]) if len(sys.argv) > 2 else None
    result = validate(csv_path)
    payload = json.dumps(result, ensure_ascii=False, indent=2)
    print(payload)
    if report_path:
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(payload, encoding="utf-8")
    return 0 if result["approved"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
