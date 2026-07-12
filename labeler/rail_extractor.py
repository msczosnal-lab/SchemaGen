"""RailExtractor v0 — net star (net_builder) → łańcuch link GT v2."""

from __future__ import annotations

import math

from backend.models.schema import Component, Connection, SchemaModel

_RAIL_TYPES = frozenset(
    {
        "zlaczka",
        "mostek",
        "zwarta_listwa_zlaczek",
        "listwa_zlaczek",
        "zacisk",
    }
)


def _parse_ref(ref: str) -> tuple[str, str | None]:
    if ":" in ref:
        s, t = ref.split(":", 1)
        return s, t or None
    return ref, None


def _ref_center(ref: str, comp_by_id: dict[str, Component]) -> tuple[float, float] | None:
    sym_id, _ = _parse_ref(ref)
    comp = comp_by_id.get(sym_id)
    if comp is None or len(comp.bbox) < 4:
        return None
    x1, y1, x2, y2 = comp.bbox[:4]
    return ((x1 + x2) / 2, (y1 + y2) / 2)


def _is_rail_ref(ref: str, comp_by_id: dict[str, Component]) -> bool:
    sym_id, _ = _parse_ref(ref)
    comp = comp_by_id.get(sym_id)
    if comp is None:
        return False
    typ = (comp.type or "").lower()
    return typ in _RAIL_TYPES or "zlacz" in typ or typ == "mostek"


def _sort_collinear(refs: list[str], comp_by_id: dict[str, Component]) -> list[str]:
    pts = [(r, _ref_center(r, comp_by_id)) for r in refs]
    pts = [(r, p) for r, p in pts if p is not None]
    if len(pts) < 2:
        return refs
    xs = [p[0] for _, p in pts]
    ys = [p[1] for _, p in pts]
    span_x = max(xs) - min(xs)
    span_y = max(ys) - min(ys)
    if span_x >= span_y:
        pts.sort(key=lambda x: x[1][0])
    else:
        pts.sort(key=lambda x: x[1][1])
    return [r for r, _ in pts]


def _conn_key(c: Connection) -> tuple[str, str, str]:
    a, b = sorted([str(c.from_ref), str(c.to)])
    return (a, b, c.kind or "power")


def expand_rail_connections(schema: SchemaModel) -> list[Connection]:
    """Zamienia gwiazdy net_* miedzy zlaczkami/mostkami na lancuch link."""
    comp_by_id = {c.id: c for c in schema.components}
    original = list(schema.connections)
    by_pot: dict[str, list[Connection]] = {}
    for c in original:
        pot = (c.potential or "").strip()
        if pot.startswith("net_"):
            by_pot.setdefault(pot, []).append(c)

    remove_keys: set[tuple[str, str, str]] = set()
    extra: list[Connection] = []

    for pot, group in by_pot.items():
        refs: set[str] = set()
        for c in group:
            refs.add(str(c.from_ref))
            refs.add(str(c.to))
        rail_refs = sorted({r for r in refs if _is_rail_ref(r, comp_by_id)})
        if len(rail_refs) < 3:
            continue
        ordered = _sort_collinear(rail_refs, comp_by_id)
        if len(ordered) < 2:
            continue
        rail_set = set(rail_refs)
        for c in group:
            a, b = str(c.from_ref), str(c.to)
            if a in rail_set and b in rail_set:
                remove_keys.add(_conn_key(c))
        for i in range(len(ordered) - 1):
            a, b = ordered[i], ordered[i + 1]
            extra.append(
                Connection.model_validate(
                    {"from": a, "to": b, "kind": "link", "potential": pot}
                )
            )

    out: list[Connection] = []
    seen: set[tuple[str, str, str]] = set()
    for c in original:
        k = _conn_key(c)
        if k in remove_keys:
            continue
        if k in seen:
            continue
        seen.add(k)
        out.append(c)
    for c in extra:
        k = _conn_key(c)
        if k in seen:
            continue
        seen.add(k)
        out.append(c)
    return out
