"""SchemaModel (runtime) → SchematicGraph v2 — most auto-draft GT."""

from __future__ import annotations

import math

from backend.models.schema import Component, Connection, ConnectionKind, GraphicLine, SchemaModel
from backend.models.schematic_graph import GraphLine, GraphSymbol, SchematicGraph

_VALID_KINDS = frozenset({"power", "signal", "pe", "control", "link", "other"})


def schema_to_graph(
    schema: SchemaModel,
    page_id: str,
    image_width: int,
    image_height: int,
) -> SchematicGraph:
    """Konwertuj wynik GraphBuilder na GT v2 (symbole + linie terminal→terminal)."""
    comp_by_id = {c.id: c for c in schema.components}
    symbols = [_component_to_symbol(c) for c in schema.components]
    sym_by_id = {s.id: s for s in symbols}

    lines: list[GraphLine] = []
    seen: set[tuple[str, str, str]] = set()
    for idx, conn in enumerate(schema.connections):
        line = _connection_to_line(conn, idx, comp_by_id, sym_by_id, schema.graphic_lines)
        if line is None:
            continue
        key = _line_key(line)
        if key in seen:
            continue
        seen.add(key)
        lines.append(line)

    return SchematicGraph(
        page_id=page_id,
        image_width=max(1, image_width),
        image_height=max(1, image_height),
        symbols=symbols,
        lines=lines,
    )


def _component_to_symbol(comp: Component) -> GraphSymbol:
    return GraphSymbol(
        id=comp.id,
        type=comp.type or "element",
        tag=comp.tag or "",
        listwa="",
        bbox=list(comp.bbox),
        terminals=list(comp.terminals),
    )


def _parse_ref(ref: str) -> tuple[str, str | None]:
    if ":" in ref:
        sym, term = ref.split(":", 1)
        return sym, term or None
    return ref, None


def _terminal_abs(comp: Component, term_id: str) -> tuple[float, float] | None:
    if len(comp.bbox) < 4:
        return None
    x1, y1, x2, y2 = comp.bbox[:4]
    w = (x2 - x1) or 1.0
    h = (y2 - y1) or 1.0
    for t in comp.terminals:
        if t.id == term_id:
            return (x1 + t.x * w, y1 + t.y * h)
    return None


def _nearest_terminal_ref(comp: Component, pt: tuple[float, float]) -> str | None:
    if not comp.terminals:
        return None
    if len(comp.bbox) < 4:
        return None
    best_id: str | None = None
    best_d = float("inf")
    for t in comp.terminals:
        abs_pt = _terminal_abs(comp, t.id)
        if abs_pt is None:
            continue
        d = math.hypot(abs_pt[0] - pt[0], abs_pt[1] - pt[1])
        if d < best_d:
            best_d = d
            best_id = t.id
    if best_id is None:
        return None
    return f"{comp.id}:{best_id}"


def _resolve_ref(
    ref: str,
    comp_by_id: dict[str, Component],
    graphic_lines: list[GraphicLine],
    other_ref: str | None = None,
) -> str | None:
    sym_id, term_id = _parse_ref(ref)
    comp = comp_by_id.get(sym_id)
    if comp is None:
        return None
    if term_id and any(t.id == term_id for t in comp.terminals):
        return f"{sym_id}:{term_id}"
    if term_id is None and comp.terminals:
        if len(comp.terminals) == 1:
            return f"{sym_id}:{comp.terminals[0].id}"
        pt = _infer_endpoint_near(comp, graphic_lines, other_ref, comp_by_id)
        if pt is not None:
            return _nearest_terminal_ref(comp, pt)
    return None


def _infer_endpoint_near(
    comp: Component,
    graphic_lines: list[GraphicLine],
    other_ref: str | None,
    comp_by_id: dict[str, Component],
) -> tuple[float, float] | None:
    if len(comp.bbox) < 4:
        return None
    cx = (comp.bbox[0] + comp.bbox[2]) / 2
    cy = (comp.bbox[1] + comp.bbox[3]) / 2
    other_pt: tuple[float, float] | None = None
    if other_ref:
        osym, oterm = _parse_ref(other_ref)
        oc = comp_by_id.get(osym)
        if oc and oterm:
            other_pt = _terminal_abs(oc, oterm)
    best: tuple[float, float] | None = None
    best_d = float("inf")
    for gl in graphic_lines:
        if gl.role != "wire":
            continue
        for p in gl.points:
            if len(p) < 2:
                continue
            px, py = float(p[0]), float(p[1])
            if not _point_near_bbox(px, py, comp.bbox, margin=24.0):
                continue
            d = math.hypot(px - cx, py - cy)
            if other_pt is not None:
                d += 0.25 * math.hypot(px - other_pt[0], py - other_pt[1])
            if d < best_d:
                best_d = d
                best = (px, py)
    return best


def _point_near_bbox(x: float, y: float, bbox: list[float], margin: float) -> bool:
    if len(bbox) < 4:
        return False
    x1, y1, x2, y2 = bbox[:4]
    return x1 - margin <= x <= x2 + margin and y1 - margin <= y <= y2 + margin


def _kind_for_connection(conn: Connection, graphic_lines: list[GraphicLine]) -> ConnectionKind:
    # kind Connection jest walidowanym Literalem (Pydantic) — pochodzi z line_classifier
    # w GraphBuilder. Nie zgadujemy z niepowiazanych graphic_lines (bylby losowy kind).
    kind = getattr(conn, "kind", "power") or "power"
    return kind if kind in _VALID_KINDS else "power"  # type: ignore[return-value]


def _vertices_for_endpoints(
    p0: tuple[float, float],
    p1: tuple[float, float],
    graphic_lines: list[GraphicLine],
    tol: float = 16.0,
) -> list[list[float]]:
    best_pts: list[list[float]] | None = None
    best_score = 0.0
    for gl in graphic_lines:
        if gl.role != "wire" or len(gl.points) < 2:
            continue
        pts = [[float(p[0]), float(p[1])] for p in gl.points if len(p) >= 2]
        if len(pts) < 2:
            continue
        d0 = min(math.hypot(pts[0][0] - p0[0], pts[0][1] - p0[1]),
                 math.hypot(pts[-1][0] - p0[0], pts[-1][1] - p0[1]))
        d1 = min(math.hypot(pts[0][0] - p1[0], pts[0][1] - p1[1]),
                 math.hypot(pts[-1][0] - p1[0], pts[-1][1] - p1[1]))
        if d0 > tol or d1 > tol:
            continue
        score = 1.0 / (1.0 + d0 + d1)
        if score > best_score:
            best_score = score
            if math.hypot(pts[0][0] - p0[0], pts[0][1] - p0[1]) > math.hypot(
                pts[-1][0] - p0[0], pts[-1][1] - p0[1]
            ):
                pts = list(reversed(pts))
            best_pts = pts
    return best_pts or []


def _connection_to_line(
    conn: Connection,
    idx: int,
    comp_by_id: dict[str, Component],
    sym_by_id: dict[str, GraphSymbol],
    graphic_lines: list[GraphicLine],
) -> GraphLine | None:
    raw_from = str(conn.from_ref)
    raw_to = str(conn.to)
    from_ref = _resolve_ref(raw_from, comp_by_id, graphic_lines, raw_to)
    to_ref = _resolve_ref(raw_to, comp_by_id, graphic_lines, raw_from)
    if from_ref is None or to_ref is None:
        return None
    fsym, _ = _parse_ref(from_ref)
    tsym, _ = _parse_ref(to_ref)
    if fsym not in sym_by_id or tsym not in sym_by_id:
        return None

    kind = _kind_for_connection(conn, graphic_lines)
    rail = ""
    if kind == "link":
        pot = (getattr(conn, "potential", "") or "").strip()
        if pot and not pot.startswith("net_"):
            rail = pot

    vertices: list[list[float]] = []
    fc = comp_by_id.get(fsym)
    tc = comp_by_id.get(tsym)
    if fc and tc:
        _, fterm = _parse_ref(from_ref)
        _, tterm = _parse_ref(to_ref)
        if fterm and tterm:
            p0 = _terminal_abs(fc, fterm)
            p1 = _terminal_abs(tc, tterm)
            if p0 and p1:
                vertices = _vertices_for_endpoints(p0, p1, graphic_lines)

    return GraphLine(
        id=f"auto_L{idx}",
        from_ref=from_ref,
        to=to_ref,
        vertices=vertices,
        kind=kind,
        rail=rail,
    )


def _line_key(ln: GraphLine) -> tuple[str, str, str]:
    a, b = sorted([ln.from_ref, ln.to])
    return (a, b, ln.kind)
