"""Prefill SchematicGraph v2 — bbox YOLO + terminale nominalne z wzorców klas."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np

from backend.models.detection import SymbolDetection
from backend.models.schema import Component, Terminal
from backend.models.schematic_graph import GraphSymbol, SchematicGraph
from backend.paths import RAW
from backend.recognize.mostek_orient_map import is_mostek_class
from backend.recognize.mostek_terminals import derive_mostek_terminals
from backend.recognize.symbol_detector import OnnxSymbolDetector
from backend.recognize.terminal_patterns_io import load_patterns
from labeler.runtime_draft import image_size_for_page


def nominal_terminals_from_pattern(
    bbox: list[float], pattern: dict[str, Any]
) -> list[Terminal]:
    """Terminale na slotach required wzorca (edge+frac), bez linii wire."""
    if len(bbox) < 4:
        return []
    x1, y1, x2, y2 = bbox[:4]
    w = (x2 - x1) or 1.0
    h = (y2 - y1) or 1.0
    out: list[Terminal] = []
    for spec in pattern.get("expected") or []:
        if not bool(spec.get("required", False)):
            continue
        edge = str(spec.get("edge") or "left")
        frac = float(spec.get("frac", 0.5))
        rx, ry = _edge_frac_to_rel(edge, frac)
        tid = _slot_id(edge, len(out))
        out.append(Terminal(id=tid, x=round(rx, 4), y=round(ry, 4)))
    return out


def _slot_id(edge: str, idx: int) -> str:
    mapping = {"left": "L", "right": "R", "top": "T", "bottom": "B"}
    return mapping.get(edge, str(idx + 1))


def _edge_frac_to_rel(edge: str, frac: float) -> tuple[float, float]:
    frac = max(0.0, min(1.0, frac))
    if edge == "left":
        return (0.0, frac)
    if edge == "right":
        return (1.0, frac)
    if edge == "top":
        return (frac, 0.0)
    if edge == "bottom":
        return (frac, 1.0)
    return (0.5, 0.5)


def _terminals_for_symbol(
    sym: GraphSymbol,
    patterns: dict[str, dict],
    image_bgr: np.ndarray | None,
) -> list[Terminal]:
    pattern = patterns.get(sym.type or "")
    if pattern:
        method = str(pattern.get("method") or "line-contact")
        if method == "delegate" and is_mostek_class(sym.type) and image_bgr is not None:
            comp = Component(id=sym.id, type=sym.type, bbox=list(sym.bbox))
            return derive_mostek_terminals(comp, image_bgr)
        return nominal_terminals_from_pattern(sym.bbox, pattern)
    return []


def _detection_to_symbol(det: SymbolDetection, sym_id: str) -> GraphSymbol:
    return GraphSymbol(
        id=sym_id,
        type=det.class_name,
        tag="",
        bbox=[det.x, det.y, det.x + det.width, det.y + det.height],
        terminals=[],
    )


def _sort_key(det: SymbolDetection) -> tuple[float, float]:
    cy = det.y + det.height / 2
    cx = det.x + det.width / 2
    return (cy, cx)


def prefill_graph(
    page_id: str,
    *,
    force: bool = False,
    detector: OnnxSymbolDetector | None = None,
) -> SchematicGraph:
    """Draft grafu: symbole YOLO + terminale wzorcowe, lines=[]."""
    from backend.db import has_schematic_graph

    if not force and has_schematic_graph(page_id):
        raise FileExistsError(f"Graf v2 istnieje dla {page_id} — użyj force=true")

    image_path = _resolve_image(page_id)
    w, h = image_size_for_page(page_id)
    if w <= 0 or h <= 0:
        raise FileNotFoundError(f"Brak obrazu lub rozmiaru dla {page_id}")

    det = detector or OnnxSymbolDetector()
    detections = sorted(det.detect(str(image_path)), key=_sort_key)

    image_bgr = None
    try:
        import cv2

        image_bgr = cv2.imread(str(image_path))
    except Exception:
        image_bgr = None

    patterns = load_patterns().get("classes") or {}
    symbols: list[GraphSymbol] = []
    for i, d in enumerate(detections):
        sym = _detection_to_symbol(d, f"sym_{i}")
        sym.terminals = _terminals_for_symbol(sym, patterns, image_bgr)
        symbols.append(sym)

    return SchematicGraph(
        page_id=page_id,
        image_width=w,
        image_height=h,
        symbols=symbols,
        lines=[],
    )


def _resolve_image(page_id: str) -> Path:
    for ext in (".png", ".jpg", ".jpeg"):
        path = RAW / f"{page_id}{ext}"
        if path.exists():
            return path
    raise FileNotFoundError(f"Brak obrazu: {page_id}")
