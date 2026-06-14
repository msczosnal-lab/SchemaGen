# COWORK_TASK: sync/prompts/006-export-onnx.md

"""Eksport wytrenowanego modelu do ONNX."""

from __future__ import annotations

from pathlib import Path

from backend.paths import MODELS
from train.train_symbols import register_model


def export_onnx(weights_path: str, version: str = "v1") -> str:
    """COWORK: torch -> ONNX z opset compatible z onnxruntime-gpu."""
    raise NotImplementedError("COWORK: export ONNX")


if __name__ == "__main__":
    out = MODELS / "symbols_v1.onnx"
    print(f"Docelowy plik: {out}")
