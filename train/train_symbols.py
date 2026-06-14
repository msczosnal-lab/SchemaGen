# COWORK_TASK: sync/prompts/005-train-symbols.md

"""Trening YOLOv8n na RTX 2080."""

from __future__ import annotations

import json
from pathlib import Path

from backend.paths import LABELED, MODELS, REGISTRY_PATH


def train(data_yaml: str | None = None, epochs: int = 50, batch: int = 8) -> dict:
    """Fine-tune YOLOv8n. COWORK: ultralytics train loop."""
    yaml_path = data_yaml or str(LABELED / "data.yaml")
    if not Path(yaml_path).exists():
        raise FileNotFoundError(f"Brak datasetu: {yaml_path}. Oznacz dane w labelerze i wyeksportuj.")
    raise NotImplementedError("COWORK: ultralytics YOLO.train + zapis wag")


def register_model(version: str, onnx_path: str, metrics: dict | None = None) -> None:
    MODELS.mkdir(parents=True, exist_ok=True)
    registry: dict = {"active": version, "versions": {}}
    if REGISTRY_PATH.exists():
        registry = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    registry.setdefault("versions", {})[version] = {
        "onnx_path": onnx_path,
        "metrics": metrics or {},
    }
    registry["active"] = version
    REGISTRY_PATH.write_text(json.dumps(registry, indent=2), encoding="utf-8")


if __name__ == "__main__":
    train()
