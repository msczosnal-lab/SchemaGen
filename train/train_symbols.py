# COWORK_TASK: sync/prompts/005-train-symbols.md

"""Trening YOLOv8n na RTX 2080 (8GB VRAM, batch<=8)."""

from __future__ import annotations

import json
from pathlib import Path

from backend.paths import DATA, MODELS, REGISTRY_PATH

DATASET_YAML = DATA / "dataset" / "data.yaml"
MAX_BATCH = 8  # limit dla RTX 2080 (8GB VRAM)


def train(
    data_yaml: str | None = None,
    epochs: int = 50,
    batch: int = 8,
    imgsz: int = 640,
    device: int | str = 0,
    model: str = "yolov8n.pt",
    project: str | None = None,
    name: str = "symbols",
) -> dict:
    """Fine-tune YOLOv8n na oznaczonych symbolach.

    Trening GPU uruchamia Filip lokalnie (RTX 2080). Na PC ZW import ultralytics
    jest leniwy — testy nie wymagaja torch/ultralytics ani datasetu.
    """
    yaml_path = data_yaml or str(DATASET_YAML)
    if not Path(yaml_path).exists():
        raise FileNotFoundError(
            f"Brak datasetu: {yaml_path}. Uruchom najpierw "
            f"`python -m train.dataset_export`."
        )
    batch = min(batch, MAX_BATCH)  # twardy limit VRAM

    try:
        from ultralytics import YOLO
    except ImportError as exc:  # pragma: no cover - srodowisko bez GPU (PC ZW)
        raise RuntimeError(
            "Brak pakietu ultralytics. Zainstaluj na PC z GPU: "
            "`pip install ultralytics`."
        ) from exc

    out_dir = Path(project) if project else (MODELS / "runs")
    out_dir.mkdir(parents=True, exist_ok=True)

    yolo = YOLO(model)
    results = yolo.train(
        data=yaml_path,
        epochs=epochs,
        batch=batch,
        imgsz=imgsz,
        device=device,
        project=str(out_dir),
        name=name,
    )

    save_dir = Path(getattr(results, "save_dir", out_dir / name))
    best = save_dir / "weights" / "best.pt"
    metrics = _extract_metrics(results)
    return {
        "best_weights": str(best),
        "save_dir": str(save_dir),
        "epochs": epochs,
        "batch": batch,
        "metrics": metrics,
    }


def _extract_metrics(results: object) -> dict:
    """Wyciagnij metryki z wyniku ultralytics (best-effort, format moze sie roznic)."""
    box = getattr(getattr(results, "box", None), "map50", None)
    out: dict = {}
    if box is not None:
        try:
            out["map50"] = float(box)
        except (TypeError, ValueError):
            pass
    return out


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
