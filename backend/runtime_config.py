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
            # ROI: pomijaj linie w calosci ponizej tego ulamka wysokosci strony
            # (tabliczka/tabelki na dole arkusza). 1.0 = bez ciecia.
            "roi_bottom_cut_frac": 1.0,
            # Tolerancja terminala (px) — skalowana z rozdzielczoscia strony.
            "terminal_tol_frac": 0.012,
            "terminal_tol_min": 12.0,
            # Progi Hough (LineTracer) — frac wzgledem max(W,H) + floory.
            "hough_min_len_frac": 0.02,
            "hough_gap_frac": 0.0015,
            "hough_min_len_floor": 20,
            "hough_threshold_floor": 50,
            "hough_gap_floor": 4,
            # Strict: Connection tylko gdy oba konce trafiaja w terminal.
            "connection_require_terminal": False,
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


def terminal_tol_frac() -> float:
    return float(runtime_settings()["terminal_tol_frac"])


def terminal_tol_min() -> float:
    return float(runtime_settings()["terminal_tol_min"])


def hough_params() -> dict:
    """Progi Hough z configu (frac wzgledem max(W,H) + floory)."""
    s = runtime_settings()
    return {
        "min_len_frac": float(s["hough_min_len_frac"]),
        "gap_frac": float(s["hough_gap_frac"]),
        "min_len_floor": int(s["hough_min_len_floor"]),
        "threshold_floor": int(s["hough_threshold_floor"]),
        "gap_floor": int(s["hough_gap_floor"]),
    }
