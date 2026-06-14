"""MCP schemagen-local — walidacja i status offline."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def validate_schema(model_path: str, ground_truth: str | None = None) -> str:
    cmd = [sys.executable, "-m", "backend.cli", "validate", model_path]
    if ground_truth:
        cmd.extend(["--ground-truth", ground_truth])
    result = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
    return result.stdout or result.stderr


def training_status() -> str:
    registry = ROOT / "data" / "models" / "registry.json"
    if not registry.exists():
        return json.dumps({"active": None, "message": "Brak wytrenowanych modeli"})
    return registry.read_text(encoding="utf-8")


def list_labeled() -> str:
    labeled = ROOT / "data" / "labeled"
    if not labeled.exists():
        return json.dumps([])
    files = sorted(labeled.glob("*.schema.json"))
    return json.dumps([f.name for f in files], ensure_ascii=False, indent=2)


if __name__ == "__main__":
    print(training_status())
