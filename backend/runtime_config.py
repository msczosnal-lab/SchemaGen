"""Wspolne ustawienia runtime z config/*.yaml."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import yaml

from backend.paths import CONFIG

INGEST_CFG = CONFIG / "ingest.yaml"
RUNTIME_CFG = CONFIG / "runtime.yaml"


def _load_yaml(path: Path, defaults: dict) -> dict:
    if not path.exists():
        return defaults
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        return defaults
    out = dict(defaults)
    out.update(data)
    return out


@lru_cache(maxsize=1)
def ingest_settings() -> dict:
    return _load_yaml(INGEST_CFG, {"pdf_dpi": 400, "legacy_pdf_dpi": 200})


@lru_cache(maxsize=1)
def runtime_settings() -> dict:
    return _load_yaml(
        RUNTIME_CFG,
        {
            "yolo_imgsz": 1280,
            "yolo_batch": 4,
            "yolo_conf_threshold": 0.15,
            "roi_bottom_cut_frac": 1.0,
        },
    )


def pdf_dpi() -> int:
    return int(ingest_settings()["pdf_dpi"])


def legacy_pdf_dpi() -> int:
    return int(ingest_settings()["legacy_pdf_dpi"])


def yolo_imgsz() -> int:
    return int(runtime_settings()["yolo_imgsz"])


def yolo_batch() -> int:
    return int(runtime_settings()["yolo_batch"])


def yolo_conf_threshold() -> float:
    return float(runtime_settings()["yolo_conf_threshold"])


def roi_bottom_cut_frac() -> float:
    """Ulamek wysokosci: linie w calosci ponizej sa pomijane. Clamp do (0, 1]."""
    val = float(runtime_settings()["roi_bottom_cut_frac"])
    if val <= 0.0 or val > 1.0:
        return 1.0
    return val
