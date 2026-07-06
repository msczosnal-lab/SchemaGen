"""Walidacja SchematicGraph v2 — reguły wspólne GT (i docelowo runtime)."""

from __future__ import annotations

import math
from dataclasses import dataclass, field

from backend.models.schematic_graph import GraphLine, GraphSymbol, SchematicGraph


@dataclass
class GraphValidationResult:
    valid: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


def graph_rules() -> dict:
    """Progi ortho/snap/tol z runtime.yaml (GET /api/graph-rules)."""
    try:
        from backend.runtime_config import (
            runtime_settings,
            terminal_tol_pattern_frac,
            terminal_tol_pattern_min,
        )

        s = runtime_settings()
        return {
            "snap_tol_frac": terminal_tol_pattern_frac(),
            "snap_tol_min": terminal_tol_pattern_min(),
            "wire_axis_tol_deg": float(
                s.get("wire_axis_tol_deg", s.get("hough_bus_axis_tol_deg", 6.0))
            ),
            "wire_join_angle_tol_deg": float(s.get("wire_join_angle_tol_deg", 8.0)),
            "terminal_edge_frac": 0.05,
        }
    except Exception:
        return {
            "snap_tol_frac": 0.008,
            "snap_tol_min": 8.0,
            "wire_axis_tol_deg": 6.0,
            "wire_join_angle_tol_deg": 8.0,
            "terminal_edge_frac": 0.05,
        }


def validate_graph(
    graph: SchematicGraph,
    rules: dict | None = None,
) -> GraphValidationResult:
    """Walidacja grafu przed zapisem."""
    r = rules or graph_rules()
    errors: list[str] = []
    warnings: list[str] = []

    if graph.version != 2:
        errors.append(f"version={graph.version}, oczekiwane 2")
    if graph.image_width <= 0 or graph.image_height <= 0:
        errors.append("image_width/image_height musza byc > 0")

    page_max = max(graph.image_width, graph.image_height, 1)
    snap_tol_px = max(
        float(r["snap_tol_min"]),
        float(r["snap_tol_frac"]) * page_max,
    )
    axis_tol = float(r["wire_axis_tol_deg"])
    join_tol = float(r["wire_join_angle_tol_deg"])
    edge_frac = float(r.get("terminal_edge_frac", 0.05))

    sym_by_id: dict[str, GraphSymbol] = {}
    for sym in graph.symbols:
        if sym.id in sym_by_id:
            errors.append(f"duplikat symbol.id: {sym.id}")
        sym_by_id[sym.id] = sym
        _validate_symbol(sym, edge_frac, errors)

    term_index = _terminal_index(sym_by_id)
    line_ids: set[str] = set()
    for ln in graph.lines:
        if ln.id in line_ids:
            errors.append(f"duplikat line.id: {ln.id}")
        line_ids.add(ln.id)
        _validate_line(
            ln,
            sym_by_id,
            term_index,
            snap_tol_px,
            axis_tol,
            join_tol,
            errors,
        )

    return GraphValidationResult(valid=not errors, errors=errors, warnings=warnings)


def _validate_symbol(sym: GraphSymbol, edge_frac: float, errors: list[str]) -> None:
    bb = sym.bbox
    if len(bb) < 4:
        errors.append(f"{sym.id}: bbox wymaga 4 wspolrzednych")
        return
    x1, y1, x2, y2 = bb[:4]
    if x2 <= x1 or y2 <= y1:
        errors.append(f"{sym.id}: bbox nieprawidlowy ({x1},{y1})-({x2},{y2})")
    term_ids: set[str] = set()
    for t in sym.terminals:
        if t.id in term_ids:
            errors.append(f"{sym.id}: duplikat terminal.id {t.id}")
        term_ids.add(t.id)
        if not _terminal_on_edge(t.x, t.y, edge_frac):
            errors.append(
                f"{sym.id}:{t.id}: terminal poza obrysem bbox "
                f"({t.x:.3f},{t.y:.3f})"
            )


def _terminal_on_edge(x: float, y: float, frac_tol: float) -> bool:
    on_x = x <= frac_tol or x >= 1.0 - frac_tol
    on_y = y <= frac_tol or y >= 1.0 - frac_tol
    return on_x or on_y


def _terminal_index(symbols: dict[str, GraphSymbol]) -> dict[str, tuple[str, str]]:
    """ref 'sym:term' -> (sym_id, term_id)."""
    out: dict[str, tuple[str, str]] = {}
    for sym_id, sym in symbols.items():
        for t in sym.terminals:
            out[f"{sym_id}:{t.id}"] = (sym_id, t.id)
    return out


def _parse_ref(ref: str) -> tuple[str, str] | None:
    if ":" not in ref:
        return None
    sym_id, term_id = ref.split(":", 1)
    if not sym_id or not term_id:
        return None
    return sym_id, term_id


def _terminal_abs(sym: GraphSymbol, term_id: str) -> tuple[float, float] | None:
    if len(sym.bbox) < 4:
        return None
    x1, y1, x2, y2 = sym.bbox[:4]
    w = (x2 - x1) or 1.0
    h = (y2 - y1) or 1.0
    for t in sym.terminals:
        if t.id == term_id:
            return (x1 + t.x * w, y1 + t.y * h)
    return None


def _validate_line(
    ln: GraphLine,
    sym_by_id: dict[str, GraphSymbol],
    term_index: dict[str, tuple[str, str]],
    snap_tol_px: float,
    axis_tol_deg: float,
    join_tol_deg: float,
    errors: list[str],
) -> None:
    for label, ref in (("from", ln.from_ref), ("to", ln.to)):
        parsed = _parse_ref(ref)
        if parsed is None:
            errors.append(f"{ln.id}: {label} '{ref}' — wymagany format sym_id:terminal_id")
            continue
        sym_id, term_id = parsed
        if sym_id not in sym_by_id:
            errors.append(f"{ln.id}: {label} — nieznany symbol {sym_id}")
        elif ref not in term_index:
            errors.append(f"{ln.id}: {label} — nieznany terminal {ref}")

    if not ln.vertices:
        return

    pts = [p for p in ln.vertices if len(p) >= 2]
    if len(pts) < 2:
        errors.append(f"{ln.id}: vertices wymagaja co najmniej 2 punktow")
        return

    for i in range(len(pts) - 1):
        if not _segment_axis_aligned(pts[i], pts[i + 1], axis_tol_deg):
            errors.append(f"{ln.id}: segment {i} nie jest osiowy H/V")

    for i in range(1, len(pts) - 1):
        if not _join_is_orthogonal(pts[i - 1], pts[i], pts[i + 1], join_tol_deg):
            errors.append(f"{ln.id}: zlamanie {i} nie pod katem prostym")

    from_parsed = _parse_ref(ln.from_ref)
    to_parsed = _parse_ref(ln.to)
    if from_parsed and from_parsed[0] in sym_by_id:
        pos = _terminal_abs(sym_by_id[from_parsed[0]], from_parsed[1])
        if pos and _dist(pts[0], pos) > snap_tol_px:
            errors.append(f"{ln.id}: poczatek vertices nie przy terminalu from ({snap_tol_px:.0f}px)")
    if to_parsed and to_parsed[0] in sym_by_id:
        pos = _terminal_abs(sym_by_id[to_parsed[0]], to_parsed[1])
        if pos and _dist(pts[-1], pos) > snap_tol_px:
            errors.append(f"{ln.id}: koniec vertices nie przy terminalu to ({snap_tol_px:.0f}px)")


def _dist(a: list[float], b: tuple[float, float]) -> float:
    return math.hypot(float(a[0]) - b[0], float(a[1]) - b[1])


def _segment_axis_aligned(p0: list[float], p1: list[float], tol_deg: float) -> bool:
    dx = abs(float(p1[0]) - float(p0[0]))
    dy = abs(float(p1[1]) - float(p0[1]))
    if dx < 1e-6 and dy < 1e-6:
        return True
    ang = math.degrees(math.atan2(dy, dx))
    return ang <= tol_deg or ang >= 90.0 - tol_deg


def _join_is_orthogonal(
    p0: list[float],
    p1: list[float],
    p2: list[float],
    tol_deg: float,
) -> bool:
    v1 = (float(p1[0]) - float(p0[0]), float(p1[1]) - float(p0[1]))
    v2 = (float(p2[0]) - float(p1[0]), float(p2[1]) - float(p1[1]))
    len1 = math.hypot(v1[0], v1[1])
    len2 = math.hypot(v2[0], v2[1])
    if len1 < 1e-6 or len2 < 1e-6:
        return True
    dot = abs(v1[0] * v2[0] + v1[1] * v2[1])
    cos_a = min(1.0, dot / (len1 * len2))
    ang = math.degrees(math.acos(cos_a))
    return abs(ang - 90.0) <= tol_deg
