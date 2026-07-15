"""Budowa sieci (nets) z linii wire/bus -> Connection (Warstwa 1, czysta geometria).

Pomysl: pofragmentowane segmenty przewodu to jeden wezel elektryczny (net).
1. Union-find linii: lacz te, ktorych KONIEC dotyka innej linii (zalamanie 90 / odczep T).
   Skrzyzowania w polowie segmentu (bez konca) -> NIE lacz (brak kropki = brak polaczenia).
2. Do netu przypnij symbole, ktorych bbox jest blisko konca linii netu (terminal).
3. Emisja:
   - net z 2 symbolami -> 1 Connection,
   - net z >2: lancuch rail (link), pary koncow segmentow, fallback gwiazda net_k.

Bez GPU/OCR. Wejscie: graphic_lines PO sicie/ROI (tylko wire/bus sa kandydatami).
"""

from __future__ import annotations

import math

from backend.models.schema import Component, Connection, GraphicLine, Terminal
from backend.recognize.connection_path import (
    chain_adjacent_pairs,
    is_rail_node,
    parse_ref,
    segment_endpoint_pairs,
    sort_nodes_collinear,
)
from backend.recognize.line_classifier import LineClassifier

# semantic_group -> ConnectionKind (PE wykrywany po nazwie grupy)
_PE_GROUPS = frozenset({"pe", "pe_wire", "ground", "earth"})
_JOIN_ANGLE_TOL_DEG = 8.0


def _hough_wire_cfg() -> dict:
    try:
        from backend.runtime_config import hough_params
        return hough_params()
    except Exception:
        return {
            "wire_join_orthogonal_only": True,
            "wire_join_angle_tol_deg": _JOIN_ANGLE_TOL_DEG,
        }


def build_connections(
    lines: list[GraphicLine],
    components: list[Component],
    *,
    join_tol: float,
    terminal_tol: float,
    require_terminal: bool = False,
) -> tuple[list[Connection], list[str]]:
    """Zwraca (connections, potentials). Connection tylko z nets wire/bus.

    require_terminal=True: wezel powstaje TYLKO gdy koniec linii trafia w konkretny
    terminal (adres comp:terminal). Koniec ocierajacy sie o bbox bez terminala NIE
    tworzy wezla -> znikaja falszywe polaczenia 'od srodka symbolu'.
    """
    candidates = [ln for ln in lines if LineClassifier.is_connection_candidate(ln)]
    candidates = [ln for ln in candidates if len(ln.points) >= 2]
    nets = _group_into_nets(candidates, join_tol, components, terminal_tol)

    connections: list[Connection] = []
    potentials: list[str] = []
    seen: set[tuple[str, str, str]] = set()
    net_idx = 0

    for net in nets:
        # node_id -> component_id wlasciciela (node = "comp" albo "comp:terminal")
        nodes = _nodes_on_net(net, components, terminal_tol, require_terminal)
        node_ids = sorted(nodes)
        if len(node_ids) < 2:
            continue
        base_kind = _kind_for_net(net)
        if len(node_ids) == 2:
            a, b = node_ids
            # ten sam komponent (dwa jego terminale) = mostek (terminal-link)
            kind = "link" if nodes[a] == nodes[b] else base_kind
            _add(connections, seen, a, b, kind, "")
        else:
            net_id = f"net_{net_idx}"
            net_idx += 1
            potentials.append(net_id)
            _emit_multi_node(
                net,
                node_ids,
                nodes,
                components,
                base_kind,
                net_id,
                terminal_tol=terminal_tol,
                require_terminal=require_terminal,
                connections=connections,
                seen=seen,
            )
    return connections, potentials


def _emit_multi_node(
    net: list[GraphicLine],
    node_ids: list[str],
    nodes: dict[str, str],
    components: list[Component],
    base_kind: str,
    net_id: str,
    *,
    terminal_tol: float,
    require_terminal: bool,
    connections: list[Connection],
    seen: set[tuple[str, str, str]],
) -> None:
    """Emisja netu >=3 wezlow: rail chain + pary segmentow + fallback gwiazda."""
    comp_by_id = {c.id: c for c in components}
    covered: set[str] = set()
    node_set = set(node_ids)

    rail_refs = [n for n in node_ids if is_rail_node(n, comp_by_id)]
    if len(rail_refs) >= 3:
        ordered = sort_nodes_collinear(rail_refs, comp_by_id)
        for a, b in chain_adjacent_pairs(ordered):
            if parse_ref(a)[0] == parse_ref(b)[0]:
                continue
            _add(connections, seen, a, b, "link", net_id)
            covered.update((a, b))

    for a, b in segment_endpoint_pairs(
        net,
        components,
        terminal_tol,
        require_terminal,
        resolve_node=_resolve_node,
    ):
        if a not in node_set or b not in node_set:
            continue
        kind = "link" if nodes[a] == nodes[b] else base_kind
        _add(connections, seen, a, b, kind, net_id)
        covered.update((a, b))

    uncovered = node_set - covered
    if not uncovered:
        return

    anchor = node_ids[0]
    for nid in node_ids[1:]:
        kind = "link" if nodes[nid] == nodes[anchor] else base_kind
        _add(connections, seen, nid, anchor, kind, net_id)


# ----------------------------------------------------------------- union-find
def _group_into_nets(
    lines: list[GraphicLine],
    tol: float,
    components: list[Component] | None = None,
    node_tol: float = 0.0,
) -> list[list[GraphicLine]]:
    n = len(lines)
    parent = list(range(n))

    def find(i: int) -> int:
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    def union(i: int, j: int) -> None:
        parent[find(i)] = find(j)

    for i in range(n):
        for j in range(i + 1, n):
            if _lines_joined(lines[i], lines[j], tol, components, node_tol):
                union(i, j)

    groups: dict[int, list[GraphicLine]] = {}
    for i in range(n):
        groups.setdefault(find(i), []).append(lines[i])
    return list(groups.values())


def _lines_joined(
    a: GraphicLine,
    b: GraphicLine,
    tol: float,
    components: list[Component] | None = None,
    node_tol: float = 0.0,
) -> bool:
    """True gdy KONIEC jednej linii lezy na sciezce drugiej (zalamanie 90 / odczep T).

    NIE scalamy, gdy styk wypada na wezle (terminal/komponent) — terminal to granica, na
    ktorej przewody sie KONCZA, a nie przechodza. Dwa przewody na tej samej zlaczce = dwa
    polaczenia do niej, nie jeden net (regula 'jedna linia != dwa polaczenia').

    Schemat elektryczny: zlaczenia tylko pod katem prostym (h+v) lub kolinearne (przedluzenie).
    """
    cfg = _hough_wire_cfg()
    ortho_only = bool(cfg.get("wire_join_orthogonal_only", True))
    angle_tol = float(cfg.get("wire_join_angle_tol_deg", _JOIN_ANGLE_TOL_DEG))
    for ep in (a.points[0], a.points[-1]):
        if _endpoint_touches(ep, b, tol) and not _point_at_node(ep, components, node_tol):
            if not ortho_only or _orthogonal_join_at(a, b, ep, tol, angle_tol):
                return True
    for ep in (b.points[0], b.points[-1]):
        if _endpoint_touches(ep, a, tol) and not _point_at_node(ep, components, node_tol):
            if not ortho_only or _orthogonal_join_at(a, b, ep, tol, angle_tol):
                return True
    return False


def _segment_orientation(
    line: GraphicLine, *, axis_tol: float = 1.0
) -> str | None:
    """'h' / 'v' / None — segment osiowy (poziom/pion)."""
    if len(line.points) < 2:
        return None
    p, q = line.points[0], line.points[-1]
    dx, dy = abs(q[0] - p[0]), abs(q[1] - p[1])
    if dy <= axis_tol and dx > axis_tol:
        return "h"
    if dx <= axis_tol and dy > axis_tol:
        return "v"
    return None


def _orthogonal_join_at(
    a: GraphicLine,
    b: GraphicLine,
    junction: list[float],
    join_tol: float,
    angle_tol_deg: float,
) -> bool:
    """True gdy zlaczenie w `junction` jest osiowe: h+v (90°) lub kolinearne (przedluzenie)."""
    oa = _segment_orientation(a, axis_tol=join_tol * 0.1)
    ob = _segment_orientation(b, axis_tol=join_tol * 0.1)
    if oa is None or ob is None:
        return False
    if oa != ob:
        return True  # poziom + pion = kat prosty
    return _collinear_same_axis(a, b, oa, join_tol)


def _collinear_same_axis(
    a: GraphicLine, b: GraphicLine, axis: str, tol: float
) -> bool:
    """Dwie rownolegle osiowe linie na tej samej osi (przedluzenie / T na szynie)."""
    pts = a.points + b.points
    if axis == "h":
        ys = [p[1] for p in pts]
        return max(ys) - min(ys) <= tol
    xs = [p[0] for p in pts]
    return max(xs) - min(xs) <= tol


def _point_at_node(
    point: list[float], components: list[Component] | None, node_tol: float
) -> bool:
    """True gdy punkt lezy na komponencie/terminalu (granica scalania netow)."""
    if not components or node_tol <= 0:
        return False
    return _nearest_component(point, components, node_tol) is not None


def _endpoint_touches(pt: list[float], line: GraphicLine, tol: float) -> bool:
    pts = line.points
    for i in range(len(pts) - 1):
        if _pt_seg_dist(pt, pts[i], pts[i + 1]) <= tol:
            return True
    return False


def _pt_seg_dist(p: list[float], a: list[float], b: list[float]) -> float:
    ax, ay = a[0], a[1]
    bx, by = b[0], b[1]
    px, py = p[0], p[1]
    dx, dy = bx - ax, by - ay
    if dx == 0.0 and dy == 0.0:
        return math.hypot(px - ax, py - ay)
    t = ((px - ax) * dx + (py - ay) * dy) / (dx * dx + dy * dy)
    t = max(0.0, min(1.0, t))
    cx, cy = ax + t * dx, ay + t * dy
    return math.hypot(px - cx, py - cy)


# ------------------------------------------------------------- wezly na net
def _nodes_on_net(
    net: list[GraphicLine],
    components: list[Component],
    tol: float,
    require_terminal: bool = False,
) -> dict[str, str]:
    """Mapa node_id -> component_id. node = "comp" lub "comp:terminal" (gdy terminale)."""
    nodes: dict[str, str] = {}
    for line in net:
        for ep in (line.points[0], line.points[-1]):
            res = _resolve_node(ep, components, tol, require_terminal)
            if res is not None:
                node_id, comp_id = res
                nodes[node_id] = comp_id
        # Terminale lezace NA sciezce linii (szyna przez rzad zlaczek), nie tylko na koncach
        for c in components:
            if not c.terminals or len(c.bbox) < 4:
                continue
            x1, y1, x2, y2 = c.bbox[0], c.bbox[1], c.bbox[2], c.bbox[3]
            w = (x2 - x1) or 1.0
            h = (y2 - y1) or 1.0
            for t in c.terminals:
                ax = x1 + t.x * w
                ay = y1 + t.y * h
                pt = [ax, ay]
                if _point_on_line_path(pt, line, tol):
                    node_id = f"{c.id}:{t.id}"
                    nodes[node_id] = c.id
    return nodes


def _point_on_line_path(point: list[float], line: GraphicLine, tol: float) -> bool:
    """True gdy punkt lezy na dowolnym odcinku polilinii (w granicach tol)."""
    pts = line.points
    if len(pts) < 2:
        return False
    for i in range(len(pts) - 1):
        if _pt_seg_dist(point, pts[i], pts[i + 1]) <= tol:
            return True
    return False


def _resolve_node(
    point: list[float],
    components: list[Component],
    tol: float,
    require_terminal: bool = False,
) -> tuple[str, str] | None:
    """Koniec linii -> (node_id, component_id). Z terminalami: 'comp:term'; bez: 'comp'.

    require_terminal=True: zwroc wezel TYLKO gdy koniec trafia w terminal; inaczej None
    (luzny kontakt z bboxem nie tworzy polaczenia).
    """
    c = _nearest_component(point, components, tol)
    if c is None:
        return None
    if c.terminals:
        t = _nearest_terminal(point, c, tol)
        if t is not None:
            return (f"{c.id}:{t.id}", c.id)
    if require_terminal:
        return None
    return (c.id, c.id)


def derive_auto_terminals(
    component: Component,
    lines: list[GraphicLine],
    tol: float,
    *,
    merge_tol: float | None = None,
) -> list[Terminal]:
    """Terminale TYLKO na przecieciu wire z krawedzia bbox (nie nominalnie na bbox)."""
    from backend.recognize.terminal_geometry import (
        contacts_to_terminals,
        line_bbox_edge_contacts,
    )

    contacts = line_bbox_edge_contacts(
        component, lines, tol, merge_tol=merge_tol
    )
    return contacts_to_terminals(component, contacts)


def _snap_to_edge_abs(point: list[float], b: list[float]) -> tuple[float, float]:
    """Przyciagnij punkt do najblizszej krawedzi bboxa (wsp. bezwzgledne)."""
    x1, y1, x2, y2 = b[0], b[1], b[2], b[3]
    px = min(max(point[0], x1), x2)
    py = min(max(point[1], y1), y2)
    d = {"l": px - x1, "r": x2 - px, "t": py - y1, "b": y2 - py}
    edge = min(d, key=d.get)
    if edge == "l":
        px = x1
    elif edge == "r":
        px = x2
    elif edge == "t":
        py = y1
    else:
        py = y2
    return (px, py)


def _nearest_terminal(point: list[float], comp: Component, tol: float):
    """Najblizszy terminal komponentu (pozycja wzgledna -> bezwzgledna), w granicach tol."""
    b = comp.bbox
    if len(b) < 4:
        return None
    x1, y1, x2, y2 = b[0], b[1], b[2], b[3]
    best = None
    best_d = tol
    for t in comp.terminals:
        ax = x1 + t.x * (x2 - x1)
        ay = y1 + t.y * (y2 - y1)
        d = math.hypot(point[0] - ax, point[1] - ay)
        if d <= best_d:
            best_d = d
            best = t
    return best


def _nearest_component(
    point: list[float], components: list[Component], max_dist: float
) -> Component | None:
    best: Component | None = None
    best_d = max_dist
    for c in components:
        d = _point_bbox_dist(point, c.bbox)
        if d <= best_d:
            best_d = d
            best = c
    return best


def _point_bbox_dist(point: list[float], bbox: list[float]) -> float:
    if len(bbox) < 4:
        return float("inf")
    px, py = point[0], point[1]
    dx = max(bbox[0] - px, 0.0, px - bbox[2])
    dy = max(bbox[1] - py, 0.0, py - bbox[3])
    return (dx * dx + dy * dy) ** 0.5


# --------------------------------------------------------------------- emisja
def _kind_for_net(net: list[GraphicLine]) -> str:
    for line in net:
        group = (line.semantic_group or "").lower()
        if group in _PE_GROUPS or "pe" in group:
            return "pe"
    return "power"


def _add(
    connections: list[Connection],
    seen: set[tuple[str, str, str]],
    a: str,
    b: str,
    kind: str,
    potential: str,
) -> None:
    if a == b:
        return
    key = tuple(sorted((a, b))) + (kind,)
    if key in seen:
        return
    seen.add(key)
    connections.append(Connection(from_ref=a, to=b, potential=potential, kind=kind))
