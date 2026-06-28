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
        symbols = _symbols_on_net(net, components, terminal_tol)
        if len(symbols) < 2:
            continue
        kind = _kind_for_net(net)
        if len(symbols) == 2:
            _add(connections, seen, symbols[0], symbols[1], kind, "")
        else:
            net_id = f"net_{net_idx}"
            net_idx += 1
            potentials.append(net_id)
            anchor = symbols[0]
            for sym in symbols[1:]:
                _add(connections, seen, sym, anchor, kind, net_id)
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


# ------------------------------------------------------------- symbole na net
def _symbols_on_net(
    net: list[GraphicLine], components: list[Component], tol: float
) -> list[str]:
    """Id symboli (sort), ktorych bbox jest blisko konca ktorejs linii netu."""
    found: set[str] = set()
    for line in net:
        for ep in (line.points[0], line.points[-1]):
            c = _nearest_component(ep, components, tol)
            if c is not None:
                found.add(c.id)
    return sorted(found)


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
