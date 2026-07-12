"""Wspolne ustawienia runtime z config/*.yaml."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import yaml

from backend.paths import CONFIG

INGEST_CFG = CONFIG / "ingest.yaml"
RUNTIME_CFG = CONFIG / "runtime.yaml"
EVAL_CFG = CONFIG / "eval-weights.yaml"
TERMINAL_PATTERNS_CFG = CONFIG / "terminal-patterns.yaml"


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
def eval_settings() -> dict:
    """Wagi funkcji celu GT<->runtime (zadanie 020)."""
    return _load_yaml(
        EVAL_CFG,
        {
            "eval_weights": {
                "components": 0.30,
                "lines": 0.25,
                "connections": 0.35,
                "tags": 0.10,
            },
            "line_match_tol": 8,
        },
    )


def eval_weights() -> dict:
    return dict(eval_settings().get("eval_weights") or {})


def line_match_tol() -> float:
    return float(eval_settings().get("line_match_tol", 8))


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
            "terminal_tol_contact_frac": 0.012,
            "terminal_tol_contact_min": 12.0,
            "terminal_tol_join_frac": 0.012,
            "terminal_tol_join_min": 12.0,
            "terminal_tol_pattern_frac": 0.008,
            "terminal_tol_pattern_min": 8.0,
            # Progi Hough (LineTracer) — frac wzgledem max(W,H) + floory.
            "hough_min_len_frac": 0.02,
            "hough_gap_frac": 0.0015,
            "hough_min_len_floor": 20,
            "hough_threshold_floor": 50,
            "hough_gap_floor": 4,
            # Drugi przebieg Hough pod kolka wezlow (szyna listwy) — linie osiowe.
            "hough_second_pass": True,
            "hough_bus_min_len_frac": 0.01,
            "hough_bus_gap_frac": 0.004,
            "hough_bus_axis_tol_deg": 6.0,
            "wire_axis_only": True,
            "wire_axis_tol_deg": 6.0,
            "wire_join_orthogonal_only": True,
            "wire_join_angle_tol_deg": 8.0,
            # Strict: Connection tylko gdy oba konce trafiaja w terminal.
            "connection_require_terminal": False,
            # Warstwa relacji (RelationResolver)
            "relations": {
                "tag_proximity_frac": 0.02,
                "wire_label_proximity_frac": 0.012,
                "potential_arrow_classes": [
                    "strzalka_potencjalu_wejsciowa",
                    "strzalka_potencjalu_wyjsciowa",
                ],
                "merge_potential_arrows_by_tag": True,
            },
            "yolo_runtime_exclude_classes": [],
            "arrow_supplement": {
                "enabled": True,
                "min_score": 0.88,
                "downscale": 0.5,
                "scales": [1.0],
                "max_templates_per_class": 12,
                "roi_top_frac": 0.93,
                "nms_iou": 0.4,
            },
        },
    )


@lru_cache(maxsize=1)
def yolo_runtime_exclude_classes() -> frozenset[str]:
    """Klasy odrzucane po inferencji YOLO (nie trafiaja do SchemaModel.components)."""
    raw = runtime_settings().get("yolo_runtime_exclude_classes") or []
    if isinstance(raw, list):
        return frozenset(str(c) for c in raw if c)
    return frozenset()


_RELATIONS_DEFAULTS = {
    "tag_proximity_frac": 0.02,
    "wire_label_proximity_frac": 0.012,
    "potential_arrow_classes": [
        "strzalka_potencjalu_wejsciowa",
        "strzalka_potencjalu_wyjsciowa",
    ],
    "merge_potential_arrows_by_tag": True,
}


@lru_cache(maxsize=1)
def relations_settings() -> dict:
    raw = runtime_settings().get("relations") or {}
    out = dict(_RELATIONS_DEFAULTS)
    if isinstance(raw, dict):
        out.update(raw)
    classes = out.get("potential_arrow_classes")
    if isinstance(classes, list):
        out["potential_arrow_classes"] = classes
    return out


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


def yolo_tiled() -> bool:
    """Inferencja przesuwnym oknem (modele trenowane na oknach/tiling)."""
    return bool(runtime_settings().get("yolo_tiled", False))


def yolo_tile_win() -> int:
    return int(runtime_settings().get("yolo_tile_win", 1536))


def yolo_tile_overlap() -> float:
    return float(runtime_settings().get("yolo_tile_overlap", 0.2))


def roi_bottom_cut_frac() -> float:
    """Ulamek wysokosci: linie w calosci ponizej sa pomijane. Clamp do (0, 1]."""
    val = float(runtime_settings()["roi_bottom_cut_frac"])
    if val <= 0.0 or val > 1.0:
        return 1.0
    return val


def terminal_tol_frac() -> float:
    return float(runtime_settings().get("terminal_tol_contact_frac", runtime_settings()["terminal_tol_frac"]))


def terminal_tol_min() -> float:
    return float(runtime_settings().get("terminal_tol_contact_min", runtime_settings()["terminal_tol_min"]))


def terminal_tol_contact_frac() -> float:
    s = runtime_settings()
    return float(s.get("terminal_tol_contact_frac", s.get("terminal_tol_frac", 0.012)))


def terminal_tol_contact_min() -> float:
    s = runtime_settings()
    return float(s.get("terminal_tol_contact_min", s.get("terminal_tol_min", 12.0)))


def terminal_tol_join_frac() -> float:
    s = runtime_settings()
    return float(s.get("terminal_tol_join_frac", s.get("terminal_tol_frac", 0.012)))


def terminal_tol_join_min() -> float:
    s = runtime_settings()
    return float(s.get("terminal_tol_join_min", s.get("terminal_tol_min", 12.0)))


def terminal_tol_pattern_frac() -> float:
    s = runtime_settings()
    return float(s.get("terminal_tol_pattern_frac", 0.008))


def terminal_tol_pattern_min() -> float:
    s = runtime_settings()
    return float(s.get("terminal_tol_pattern_min", 8.0))


@lru_cache(maxsize=1)
def terminal_patterns() -> dict[str, dict]:
    """Wzorce terminali per klasa z config/terminal-patterns.yaml."""
    defaults: dict = {"version": 1, "classes": {}}
    data = _load_yaml(TERMINAL_PATTERNS_CFG, defaults)
    classes = data.get("classes") or {}
    if isinstance(classes, dict):
        return {str(k): dict(v) for k, v in classes.items() if isinstance(v, dict)}
    return {}


def connection_require_terminal() -> bool:
    """True -> Connection tylko gdy oba konce trafiaja w terminal (comp:terminal)."""
    return bool(runtime_settings()["connection_require_terminal"])


_ARROW_SUPPLEMENT_DEFAULTS = {
    "enabled": True,
    "min_score": 0.88,
    "coarse_min_score": 0.55,
    "downscale": 0.5,
    "scales": [1.0],
    "max_templates_per_class": 12,
    "roi_top_frac": 0.93,
    "nms_iou": 0.4,
    "min_yolo_conf_gate": 0.5,
    "refine_enabled": True,
    "refine_min_score": 0.65,
    "refine_roi_margin": 0.25,
}


@lru_cache(maxsize=1)
def arrow_supplement_settings() -> dict:
    raw = runtime_settings().get("arrow_supplement") or {}
    out = dict(_ARROW_SUPPLEMENT_DEFAULTS)
    if isinstance(raw, dict):
        out.update(raw)
    return out


def hough_params() -> dict:
    """Progi Hough z configu (frac wzgledem max(W,H) + floory)."""
    s = runtime_settings()
    return {
        "min_len_frac": float(s["hough_min_len_frac"]),
        "gap_frac": float(s["hough_gap_frac"]),
        "min_len_floor": int(s["hough_min_len_floor"]),
        "threshold_floor": int(s["hough_threshold_floor"]),
        "gap_floor": int(s["hough_gap_floor"]),
        "second_pass": bool(s.get("hough_second_pass", False)),
        "bus_min_len_frac": float(s.get("hough_bus_min_len_frac", 0.01)),
            "bus_gap_frac": float(s.get("hough_bus_gap_frac", 0.004)),
            "bus_axis_tol_deg": float(s.get("hough_bus_axis_tol_deg", 6.0)),
            "wire_axis_only": bool(s.get("wire_axis_only", True)),
            "wire_axis_tol_deg": float(s.get("wire_axis_tol_deg", s.get("hough_bus_axis_tol_deg", 6.0))),
            "wire_join_orthogonal_only": bool(s.get("wire_join_orthogonal_only", True)),
            "wire_join_angle_tol_deg": float(s.get("wire_join_angle_tol_deg", 8.0)),
        }
