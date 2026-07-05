"""TerminalResolver — terminale z wzorca klasy (config/terminal-patterns.yaml).

Fallback: derive_auto_terminals gdy brak patternu lub metoda line-contact bez kandydatow.
Mostek: delegacja do derive_mostek_terminals (wynik bajt-w-bajt).
"""

from __future__ import annotations

import math
from typing import Any

import numpy as np

from backend.models.schema import Component, GraphicLine, Terminal
from backend.recognize.line_classifier import LineClassifier
from backend.recognize.mostek_orient_map import is_mostek_class
from backend.recognize.mostek_terminals import derive_mostek_terminals
from backend.recognize.net_builder import derive_auto_terminals
from backend.recognize.terminal_geometry import (
    line_bbox_edge_contacts,
    perimeter_ink_contacts,
)


def resolve(
    component: Component,
    lines: list[GraphicLine],
    image_bgr: np.ndarray | None,
    patterns: dict[str, dict],
    *,
    contact_tol: float,
    pattern_tol: float,
    merge_tol: float | None = None,
) -> list[Terminal]:
    """Terminale komponentu wg wzorca klasy lub fallbacku."""
    if component.terminals:
        return list(component.terminals)

    pattern = patterns.get(component.type or "")
    if not pattern:
        return derive_auto_terminals(
            component, lines, contact_tol, merge_tol=merge_tol
        )

    method = str(pattern.get("method") or "line-contact")
    if method == "delegate":
        if is_mostek_class(component.type) and image_bgr is not None:
            return derive_mostek_terminals(component, image_bgr)
        return derive_auto_terminals(
            component, lines, contact_tol, merge_tol=merge_tol
        )

    candidates = line_bbox_edge_contacts(
        component, lines, contact_tol, merge_tol=merge_tol
    )
    if method in ("perimeter", "perimeter-line") and image_bgr is not None:
        ink = perimeter_ink_contacts(component, image_bgr)
        candidates = _merge_candidates(candidates, ink, pattern_tol)

    return _match_pattern(component, candidates, pattern, pattern_tol)


def _line_contact_candidates(
    component: Component,
    lines: list[GraphicLine],
    contact_tol: float,
    *,
    merge_tol: float | None,
) -> list[tuple[float, float]]:
    """Kandydaci: przeciecie wire z krawedzia bbox (abs xy)."""
    return line_bbox_edge_contacts(
        component, lines, contact_tol, merge_tol=merge_tol
    )


def _perimeter_ink_candidates(
    component: Component, image_bgr: np.ndarray
) -> list[tuple[float, float]]:
    return perimeter_ink_contacts(component, image_bgr)


def _merge_candidates(
    a: list[tuple[float, float]],
    b: list[tuple[float, float]],
    dedup_tol: float,
) -> list[tuple[float, float]]:
    out = list(a)
    for p in b:
        if not any(math.hypot(p[0] - q[0], p[1] - q[1]) <= dedup_tol for q in out):
            out.append(p)
    return out


def _match_pattern(
    component: Component,
    candidates: list[tuple[float, float]],
    pattern: dict[str, Any],
    pattern_tol: float,
) -> list[Terminal]:
    """Dopasuj kandydatow do slotow patternu. Bez kandydata slot NIE powstaje."""
    b = component.bbox
    if len(b) < 4:
        return []
    x1, y1, x2, y2 = b[0], b[1], b[2], b[3]
    w = (x2 - x1) or 1.0
    h = (y2 - y1) or 1.0
    frac_tol = float(pattern.get("frac_tol", 0.15))
    expected: list[dict] = list(pattern.get("expected") or [])

    used: set[int] = set()
    slots: list[tuple[str, float, float, bool]] = []

    for spec in expected:
        edge = str(spec.get("edge") or "left")
        frac = float(spec.get("frac", 0.5))
        required = bool(spec.get("required", False))
        slot_abs = _edge_frac_to_abs(x1, y1, x2, y2, edge, frac)
        best_i = None
        best_d = pattern_tol
        for i, cand in enumerate(candidates):
            if i in used:
                continue
            d = math.hypot(cand[0] - slot_abs[0], cand[1] - slot_abs[1])
            if d <= best_d and _candidate_on_edge(cand, x1, y1, x2, y2, edge, frac_tol):
                best_d = d
                best_i = i
        if best_i is not None:
            used.add(best_i)
            cx, cy = candidates[best_i]
        else:
            continue  # brak przeciecia/tuszu — nie tworz nominalnego terminala
        rx = round((cx - x1) / w, 4)
        ry = round((cy - y1) / h, 4)
        slots.append((edge, rx, ry, required))

    if not slots and candidates:
        out_fb: list[Terminal] = []
        for i, (cx, cy) in enumerate(candidates):
            rx = round((cx - x1) / w, 4)
            ry = round((cy - y1) / h, 4)
            out_fb.append(Terminal(id=str(i + 1), x=rx, y=ry))
        return out_fb

    # dedup bliskich slotow (anty-sasiad)
    out: list[Terminal] = []
    for i, (_edge, rx, ry, _req) in enumerate(slots):
        if any(
            math.hypot(rx - t.x, ry - t.y) * min(w, h) <= pattern_tol * 0.5
            for t in out
        ):
            continue
        out.append(Terminal(id=str(len(out) + 1), x=rx, y=ry))
    return out


def _edge_frac_to_abs(
    x1: float, y1: float, x2: float, y2: float, edge: str, frac: float
) -> tuple[float, float]:
    frac = max(0.0, min(1.0, frac))
    if edge == "left":
        return (x1, y1 + frac * (y2 - y1))
    if edge == "right":
        return (x2, y1 + frac * (y2 - y1))
    if edge == "top":
        return (x1 + frac * (x2 - x1), y1)
    if edge == "bottom":
        return (x1 + frac * (x2 - x1), y2)
    return ((x1 + x2) / 2, (y1 + y2) / 2)


def _candidate_on_edge(
    cand: tuple[float, float],
    x1: float,
    y1: float,
    x2: float,
    y2: float,
    edge: str,
    frac_tol: float,
) -> bool:
    """Kandydat lezy przy oczekiwanej krawedzi (anty-pozyczenie od sasiedniego symbolu)."""
    cx, cy = cand
    tol = frac_tol * max(x2 - x1, y2 - y1, 1.0)
    if edge == "left":
        return abs(cx - x1) <= tol
    if edge == "right":
        return abs(cx - x2) <= tol
    if edge == "top":
        return abs(cy - y1) <= tol
    if edge == "bottom":
        return abs(cy - y2) <= tol
    return True


def terminal_abs_positions(component: Component) -> list[tuple[str, float, float]]:
    """Lista (terminal_id, abs_x, abs_y) dla komponentu."""
    b = component.bbox
    if len(b) < 4:
        return []
    x1, y1, x2, y2 = b[0], b[1], b[2], b[3]
    w = (x2 - x1) or 1.0
    h = (y2 - y1) or 1.0
    return [
        (t.id, x1 + t.x * w, y1 + t.y * h)
        for t in component.terminals
    ]
