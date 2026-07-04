# COWORK_TASK: sync/prompts/005-train-symbols.md

"""Trening YOLOv8n na RTX 2080 (8GB VRAM, batch<=8)."""

from __future__ import annotations

import json
from pathlib import Path

from backend.paths import DATA, LABELED, MODELS, REGISTRY_PATH
from backend.runtime_config import yolo_batch, yolo_imgsz

DATASET_YAML = LABELED / "data.yaml"
RUNS_DIR = DATA / "runs"
MAX_BATCH = 8  # limit dla RTX 2080 (8GB VRAM)


def train(
    data_yaml: str | None = None,
    epochs: int = 150,
    batch: int | None = None,
    imgsz: int | None = None,
    device: int | str = 0,
    model: str = "yolov8n.pt",
    project: str | None = None,
    name: str = "symbols_v1",
    patience: int = 30,
    fliplr: float = 0.0,
    flipud: float = 0.0,
    degrees: float = 0.0,
    cache: bool = False,
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
    imgsz = imgsz if imgsz is not None else yolo_imgsz()
    batch = batch if batch is not None else yolo_batch()
    batch = min(batch, MAX_BATCH)  # twardy limit VRAM

    try:
        from ultralytics import YOLO
    except ImportError as exc:  # pragma: no cover - srodowisko bez GPU (PC ZW)
        raise RuntimeError(
            "Brak pakietu ultralytics. Zainstaluj na PC z GPU: "
            "`pip install -e \".[gpu]\"`."
        ) from exc

    out_dir = Path(project) if project else RUNS_DIR
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
        patience=patience,
        cache=cache,       # cache obrazow -> szybsze epoki (mniej I/O)
        cos_lr=True,
        # Augmentacja pod schematy: obrot + lustro WLACZONE — sens symboli jest
        # orientacyjnie niezmienniczy (np. linia strzalki jest wzgledem grotu,
        # nie wzgledem gory obrazu). Mnozy dane bez psucia etykiet.
        # CALA augmentacja zmieniajaca obraz WYLACZONA (scale/translate/hsv/mosaic/
        # shear/perspective): bboxy sa ciasne i poprawne, dorzucanie tla/kontekstu szkodzi.
        fliplr=fliplr,
        flipud=flipud,
        degrees=degrees,
        shear=0.0,
        perspective=0.0,
        mosaic=0.0,
        mixup=0.0,
        hsv_h=0.0,
        hsv_s=0.0,
        hsv_v=0.0,
        scale=0.0,
        translate=0.0,
    )

    save_dir = Path(getattr(results, "save_dir", out_dir / name))
    best = save_dir / "weights" / "best.pt"
    metrics = _extract_metrics(results)
    summary = {
        "best_weights": str(best),
        "save_dir": str(save_dir),
        "epochs": epochs,
        "batch": batch,
        "imgsz": imgsz,
        "model": model,
        "augment": {"fliplr": fliplr, "flipud": flipud, "degrees": degrees},
        "metrics": metrics,
    }

    MODELS.mkdir(parents=True, exist_ok=True)
    summary_path = MODELS / f"{name}_train_summary.json"
    summary_path.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    summary["summary_json"] = str(summary_path)
    return summary


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


def _cli() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Trening YOLOv8n symboli (RTX 2080).")
    parser.add_argument("--data", default=None, help="data.yaml (domyslnie data/labeled/data.yaml)")
    parser.add_argument("--epochs", type=int, default=150)
    parser.add_argument("--batch", type=int, default=None, help=f"domyslnie {yolo_batch()} (config/runtime.yaml)")
    parser.add_argument("--imgsz", type=int, default=None, help=f"domyslnie {yolo_imgsz()} (config/runtime.yaml)")
    parser.add_argument("--device", default="0", help="0 = GPU, 'cpu' = CPU")
    parser.add_argument("--name", default="symbols_v1")
    parser.add_argument("--patience", type=int, default=30)
    parser.add_argument("--cache", action="store_true", help="cache obrazow (szybsze epoki)")
    parser.add_argument("--fliplr", type=float, default=0.0)
    parser.add_argument("--flipud", type=float, default=0.0)
    parser.add_argument("--degrees", type=float, default=0.0)
    args = parser.parse_args()

    device: int | str = int(args.device) if args.device.isdigit() else args.device
    summary = train(
        data_yaml=args.data,
        epochs=args.epochs,
        batch=args.batch,
        imgsz=args.imgsz,
        device=device,
        name=args.name,
        patience=args.patience,
        fliplr=args.fliplr,
        flipud=args.flipud,
        degrees=args.degrees,
        cache=args.cache,
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    _cli()
