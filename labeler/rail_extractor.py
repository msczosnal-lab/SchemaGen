"""RailExtractor v0 — net star (net_builder) → łańcuch link GT v2."""

from __future__ import annotations

from backend.models.schema import Component, Connection, SchemaModel
from backend.recognize.connection_path import (
    chain_adjacent_pairs,
    is_rail_node,
    sort_nodes_collinear,
)


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
        rail_refs = sorted({r for r in refs if is_rail_node(r, comp_by_id)})
        if len(rail_refs) < 3:
            continue
        ordered = sort_nodes_collinear(rail_refs, comp_by_id)
        if len(ordered) < 2:
            continue
        rail_set = set(rail_refs)
        for c in group:
            a, b = str(c.from_ref), str(c.to)
            if a in rail_set and b in rail_set:
                remove_keys.add(_conn_key(c))
        for a, b in chain_adjacent_pairs(ordered):
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
