"""Budowa sieci (nets) z linii wire/bus -> Connection (Warstwa 1, czysta geometria).

Pomysl: pofragmentowane segmenty przewodu to jeden wezel elektryczny (net).
1. Union-find linii: lacz te, ktorych KONIEC dotyka innej linii (zalamanie 90 / odczep T).
   Skrzyzowania w polowie segmentu (bez konca) -> NIE lacz (brak kropki = brak polaczenia).
2. Do netu przypnij symbole, ktorych bbox jest blisko konca linii netu (terminal).
3. Emisja:
   - net z 2 symbolami -> 1 Connection,
   - net z >2 symbolami (szyna/odczepy) -> wspolny potential (net_k), gwiazda do kotwicy.

Bez GPU/OCR. Wejscie: graphic_lines PO sicie/ROI (tylko wire/bus sa kandydatami).
"""

from __future__ import annotations

import math

from backend.models.schema import Component, Connection, GraphicLine
from backend.recognize.line_classifier import LineClassifier

# semantic_group -> ConnectionKind (PE wykrywany po nazwie grupy)
_PE_GROUPS = frozenset({"pe", "pe_wire", "ground", "earth"})


def build_connections(
    lines: list[GraphicLine],
    components: list[Component],
    *,
    join_tol: float,
    terminal_tol: float,
) -> tuple[list[Connection], list[str]]:
    """Zwraca (connections, potentials). Connection tylko z nets wire/bus."""
    candidates = [ln for ln in lines if LineClassifier.is_connection_candidate(ln)]
    candidates = [ln for ln in candidates if len(ln.points) >= 2]
    nets = _group_into_nets(candidates, join_tol)

    connections: list[Connection] = []
    potentials: list[str] = []
    seen: set[tuple[str, str, str]] = set()
    net_idx = 0

    for net in nets:
        # node_id -> component_id wlasciciela (node = "comp" albo "comp:terminal")
        nodes = _nodes_on_net(net, components, terminal_tol)
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
            anchor = node_ids[0]
            for nid in node_ids[1:]:
                kind = "link" if nodes[nid] == nodes[anchor] else base_kind
                _add(connections, seen, nid, anchor, kind, net_id)
    return connections, potentials


# ----------------------------------------------------------------- union-find
def _group_into_nets(lines: list[GraphicLine], tol: float) -> list[list[GraphicLine]]:
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
            if _lines_joined(lines[i], lines[j], tol):
                union(i, j)

    groups: dict[int, list[GraphicLine]] = {}
    for i in range(n):
        groups.setdefault(find(i), []).append(lines[i])
    return list(groups.values())


def _lines_joined(a: GraphicLine, b: GraphicLine, tol: float) -> bool:
    """True gdy KONIEC jednej linii lezy na sciezce drugiej (zalamanie/odczep)."""
    for ep in (a.points[0], a.points[-1]):
        if _endpoint_touches(ep, b, tol):
            return True
    for ep in (b.points[0], b.points[-1]):
        if _endpoint_touches(ep, a, tol):
            return True
    return False


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
    net: list[GraphicLine], components: list[Component], tol: float
) -> dict[str, str]:
    """Mapa node_id -> component_id. node = "comp" lub "comp:terminal" (gdy terminale)."""
    nodes: dict[str, str] = {}
    for line in net:
        for ep in (line.points[0], line.points[-1]):
            res = _resolve_node(ep, components, tol)
            if res is not None:
                node_id, comp_id = res
                nodes[node_id] = comp_id
    return nodes


def _resolve_node(
    point: list[float], components: list[Component], tol: float
) -> tuple[str, str] | None:
    """Koniec linii -> (node_id, component_id). Z terminalami: 'comp:term'; bez: 'comp'."""
    c = _nearest_component(point, components, tol)
    if c is None:
        return None
    if c.terminals:
        t = _nearest_terminal(point, c, tol)
        if t is not None:
            return (f"{c.id}:{t.id}", c.id)
    return (c.id, c.id)


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
    key = tuple(sorted((a, b))) + (kind,)
    if key in seen:
        return
    seen.add(key)
    connections.append(Connection(from_ref=a, to=b, potential=potential, kind=kind))
