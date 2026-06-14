"""Testy eksportu ONNX — bez ultralytics/torch (sciezka guard + rejestracja)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

import train.export_onnx as eo
from train.train_symbols import register_model


def test_export_onnx_missing_weights_raises(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        eo.export_onnx(weights_path=str(tmp_path / "nope.pt"))


def test_register_model_writes_registry(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    registry = tmp_path / "registry.json"
    monkeypatch.setattr("train.train_symbols.REGISTRY_PATH", registry)
    monkeypatch.setattr("train.train_symbols.MODELS", tmp_path)

    register_model("symbols_v1", str(tmp_path / "symbols_v1.onnx"), {"map50": 0.04})

    data = json.loads(registry.read_text(encoding="utf-8"))
    assert data["active"] == "symbols_v1"
    assert data["versions"]["symbols_v1"]["metrics"]["map50"] == 0.04
