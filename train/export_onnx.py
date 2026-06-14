# COWORK_TASK: sync/prompts/006-export-onnx.md

"""Eksport wytrenowanego modelu YOLOv8n do ONNX (opset zgodny z onnxruntime-gpu).

PC ZW: kod + testy (guard/mock). Eksport na zywych wagach robi Filip lokalnie
(best.pt jest tylko u niego — nie w gicie).
"""

from __future__ import annotations

import shutil
from pathlib import Path

from backend.paths import DATA, MODELS, ROOT
from train.train_symbols import register_model

RUNS_DIR = DATA / "runs"
DEFAULT_WEIGHTS = RUNS_DIR / "symbols_v1" / "weights" / "best.pt"
DEFAULT_OPSET = 12  # zgodny z onnxruntime-gpu 1.17

# Lokalizacje, gdzie ultralytics moze zapisac wagi:
#  - data/runs/  (gdy train_symbols przekazal project)
#  - runs/       (domyslny ultralytics: runs/detect/train*/weights/best.pt)
_SEARCH_ROOTS = (RUNS_DIR, ROOT / "runs")


def find_best_weights() -> Path | None:
    """Znajdz best.pt: domyslny run, inaczej **najnowszy** w znanych lokalizacjach.

    ultralytics auto-inkrementuje katalog runu (symbols_v1, symbols_v12, ...)
    i przy braku `project` pisze do `runs/detect/train*/` — przeszukujemy oba.
    """
    if DEFAULT_WEIGHTS.exists():
        return DEFAULT_WEIGHTS
    candidates: list[Path] = []
    for root in _SEARCH_ROOTS:
        if root.exists():
            candidates.extend(root.glob("**/weights/best.pt"))
    if not candidates:
        return None
    return max(candidates, key=lambda p: p.stat().st_mtime)


def export_onnx(
    weights_path: str | None = None,
    version: str = "symbols_v1",
    opset: int = DEFAULT_OPSET,
    imgsz: int = 640,
    metrics: dict | None = None,
) -> str:
    """Konwertuj best.pt -> ONNX, skopiuj do data/models/ i zarejestruj wersje."""
    if weights_path:
        weights = Path(weights_path)
    else:
        found = find_best_weights()
        if found is None:
            raise FileNotFoundError(
                f"Brak best.pt w {RUNS_DIR} ani {DEFAULT_WEIGHTS}. "
                f"Najpierw trening: `python -m train.train_symbols`, "
                f"lub wskaz --weights <sciezka>."
            )
        weights = found
    if not weights.exists():
        raise FileNotFoundError(
            f"Brak wag: {weights}. Najpierw trening: `python -m train.train_symbols`."
        )
    weights_str = str(weights)
    print(f"Wagi: {weights_str}")

    try:
        from ultralytics import YOLO
    except ImportError as exc:  # pragma: no cover - srodowisko bez GPU (PC ZW)
        raise RuntimeError(
            "Brak pakietu ultralytics. Zainstaluj na PC z GPU: "
            "`pip install -e \".[gpu]\"`."
        ) from exc

    model = YOLO(weights_str)
    exported = model.export(format="onnx", opset=opset, imgsz=imgsz, dynamic=False)

    MODELS.mkdir(parents=True, exist_ok=True)
    dest = MODELS / f"{version}.onnx"
    shutil.copy2(str(exported), dest)
    register_model(version, str(dest), metrics)
    return str(dest)


def _cli() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Eksport YOLOv8n best.pt -> ONNX.")
    parser.add_argument("--weights", default=None, help="domyslnie data/runs/symbols_v1/weights/best.pt")
    parser.add_argument("--version", default="symbols_v1")
    parser.add_argument("--opset", type=int, default=DEFAULT_OPSET)
    parser.add_argument("--imgsz", type=int, default=640)
    args = parser.parse_args()
    out = export_onnx(
        weights_path=args.weights, version=args.version, opset=args.opset, imgsz=args.imgsz
    )
    print(f"ONNX: {out}")


if __name__ == "__main__":
    _cli()
