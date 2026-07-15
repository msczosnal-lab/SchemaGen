"""Wspólna geometria emisji connections: łańcuch rail + pary segmentów."""

from __future__ import annotations

import math

from backend.models.schema import Component, GraphicLine

RAIL_TYPES = frozenset(
    {
        "zlaczka",
        "mostek",
        "zwarta_listwa_zlaczek",
        "listwa_zlaczek",
        "zacisk",
    }
)


def parse_ref(ref: str) -> tuple[str, str | None]:
    if ":" in ref:
        s, t = ref.split(":", 1)
        return s, t or None
    return ref, None


def ref_center(ref: str, comp_by_id: dict[str, Component]) -> tuple[float, float] | None:
    sym_id, _ = parse_ref(ref)
    comp = comp_by_id.get(sym_id)
    if comp is None or len(comp.bbox) < 4:
        return None
    x1, y1, x2, y2 = comp.bbox[:4]
    return ((x1 + x2) / 2, (y1 + y2) / 2)


def is_rail_component(comp: Component | None) -> bool:
    if comp is None:
        return False
    typ = (comp.type or "").lower()
    return typ in RAIL_TYPES or "zlacz" in typ or typ == "mostek"


def is_rail_node(node_id: str, comp_by_id: dict[str, Component]) -> bool:
    sym_id, _ = parse_ref(node_id)
    return is_rail_component(comp_by_id.get(sym_id))


def sort_nodes_collinear(
    node_ids: list[str], comp_by_id: dict[str, Component]
) -> list[str]:
    pts = [(n, ref_center(n, comp_by_id)) for n in node_ids]
    pts = [(n, p) for n, p in pts if p is not None]
    if len(pts) < 2:
        return list(node_ids)
    xs = [p[0] for _, p in pts]
    ys = [p[1] for _, p in pts]
    span_x = max(xs) - min(xs)
    span_y = max(ys) - min(ys)
    if span_x >= span_y:
        pts.sort(key=lambda x: x[1][0])
    else:
        pts.sort(key=lambda x: x[1][1])
    return [n for n, _ in pts]


def segment_endpoint_pairs(
    net: list[GraphicLine],
    components: list[Component],
    tol: float,
    require_terminal: bool,
    *,
    resolve_node,
) -> list[tuple[str, str]]:
    """Pary węzłów z końców każdego segmentu linii w necie."""
    pairs: list[tuple[str, str]] = []
    seen: set[tuple[str, str]] = set()
    for line in net:
        if len(line.points) < 2:
            continue
        ends = (line.points[0], line.points[-1])
        resolved: list[str] = []
        for ep in ends:
            res = resolve_node(ep, components, tol, require_terminal)
            if res is not None:
                resolved.append(res[0])
        if len(resolved) == 2 and resolved[0] != resolved[1]:
            key = tuple(sorted(resolved))
            if key not in seen:
                seen.add(key)
                pairs.append((resolved[0], resolved[1]))
    return pairs


def chain_adjacent_pairs(ordered: list[str]) -> list[tuple[str, str]]:
    return [(ordered[i], ordered[i + 1]) for i in range(len(ordered) - 1)]
