"""Kompilacja SchematicGraph v2 → SchemaModel (deterministyczna)."""

from __future__ import annotations

from backend.models.schema import (
    Component,
    Connection,
    GraphicLine,
    SchemaMeta,
    SchemaModel,
    Terminal,
)
from backend.models.schematic_graph import GraphLine, GraphSymbol, SchematicGraph


def graph_to_schema(graph: SchematicGraph) -> SchemaModel:
    """SchematicGraph → SchemaModel: symbole, linie wire, connections, potencjały z link."""
    sym_by_id = {s.id: s for s in graph.symbols}
    components = [_symbol_to_component(s) for s in graph.symbols]

    graphic_lines: list[GraphicLine] = []
    connections: list[Connection] = []

    for ln in graph.lines:
        p0, p1 = _line_endpoints(ln, sym_by_id)
        points = _line_points(ln, p0, p1)
        graphic_lines.append(
            GraphicLine(id=ln.id, points=points, role="wire")
        )
        connections.append(
            Connection.model_validate(
                {"from": ln.from_ref, "to": ln.to, "kind": ln.kind}
            )
        )

    potentials = _assign_potentials(graph, connections)

    return SchemaModel(
        meta=SchemaMeta(source=graph.page_id, page=0),
        components=components,
        graphic_lines=graphic_lines,
        connections=connections,
        potentials=potentials,
    )


def _symbol_to_component(sym: GraphSymbol) -> Component:
    return Component(
        id=sym.id,
        type=sym.type,
        tag=sym.tag,
        bbox=list(sym.bbox),
        source="manual",
        terminals=[
            Terminal(id=t.id, x=t.x, y=t.y, name=t.name) for t in sym.terminals
        ],
    )


def _parse_ref(ref: str) -> tuple[str, str] | None:
    if ":" not in ref:
        return None
    sym_id, term_id = ref.split(":", 1)
    if not sym_id or not term_id:
        return None
    return sym_id, term_id


def _terminal_abs(sym: GraphSymbol, term_id: str) -> tuple[float, float]:
    if len(sym.bbox) < 4:
        raise ValueError(f"{sym.id}: brak bbox dla terminala {term_id}")
    x1, y1, x2, y2 = sym.bbox[:4]
    w = (x2 - x1) or 1.0
    h = (y2 - y1) or 1.0
    for t in sym.terminals:
        if t.id == term_id:
            return (x1 + t.x * w, y1 + t.y * h)
    raise ValueError(f"{sym.id}: nieznany terminal {term_id}")


def _line_endpoints(
    ln: GraphLine, sym_by_id: dict[str, GraphSymbol]
) -> tuple[tuple[float, float], tuple[float, float]]:
    from_p = _parse_ref(ln.from_ref)
    to_p = _parse_ref(ln.to)
    if from_p is None or to_p is None:
        raise ValueError(f"{ln.id}: from/to wymagaja formatu sym_id:terminal_id")
    sym_f, term_f = from_p
    sym_t, term_t = to_p
    if sym_f not in sym_by_id or sym_t not in sym_by_id:
        raise ValueError(f"{ln.id}: nieznany symbol w from/to")
    return (
        _terminal_abs(sym_by_id[sym_f], term_f),
        _terminal_abs(sym_by_id[sym_t], term_t),
    )


def _line_points(
    ln: GraphLine,
    p0: tuple[float, float],
    p1: tuple[float, float],
) -> list[list[float]]:
    if ln.vertices:
        return [[float(v[0]), float(v[1])] for v in ln.vertices if len(v) >= 2]
    return _auto_route(p0, p1)


def _auto_route(
    p0: tuple[float, float], p1: tuple[float, float]
) -> list[list[float]]:
    """Ortho L-kształt między terminalami (deterministyczny)."""
    x1, y1 = p0
    x2, y2 = p1
    if abs(x1 - x2) < 1e-6 or abs(y1 - y2) < 1e-6:
        return [[x1, y1], [x2, y2]]
    if abs(x2 - x1) >= abs(y2 - y1):
        return [[x1, y1], [x2, y1], [x2, y2]]
    return [[x1, y1], [x1, y2], [x2, y2]]


class _UnionFind:
    def __init__(self) -> None:
        self._parent: dict[str, str] = {}

    def find(self, x: str) -> str:
        if x not in self._parent:
            self._parent[x] = x
        while self._parent[x] != x:
            self._parent[x] = self._parent[self._parent[x]]
            x = self._parent[x]
        return x

    def union(self, a: str, b: str) -> None:
        ra, rb = self.find(a), self.find(b)
        if ra != rb:
            self._parent[rb] = ra

    def groups(self) -> dict[str, set[str]]:
        out: dict[str, set[str]] = {}
        for x in self._parent:
            root = self.find(x)
            out.setdefault(root, set()).add(x)
        return out


def _assign_potentials(
    graph: SchematicGraph, connections: list[Connection]
) -> list[str]:
    """Domknięcie przechodnie po kind=link → wspólny potential (≥2 symbole)."""
    uf = _UnionFind()
    _union_rail_terminals(graph, uf)
    for ln in graph.lines:
        if ln.kind != "link":
            continue
        uf.union(ln.from_ref, ln.to)

    groups = uf.groups()
    ref_to_pot: dict[str, str] = {}
    potentials: list[str] = []
    pot_idx = 0

    for _root, members in sorted(groups.items(), key=lambda kv: sorted(kv[1])[0]):
        sym_ids = {m.split(":", 1)[0] for m in members}
        if len(sym_ids) < 2:
            continue
        name = _potential_name(members, graph.symbols, graph.lines, pot_idx)
        pot_idx += 1
        potentials.append(name)
        for ref in members:
            ref_to_pot[ref] = name

    for conn in connections:
        pot_f = ref_to_pot.get(conn.from_ref)
        pot_t = ref_to_pot.get(conn.to)
        if pot_f and pot_f == pot_t:
            conn.potential = pot_f

    return potentials


def _union_rail_terminals(graph: SchematicGraph, uf: _UnionFind) -> None:
    """L/R na obrysie złączki = ten sam węzeł toru szyny (domknięcie)."""
    edge_frac = 0.05
    for sym in graph.symbols:
        if sym.type != "zlaczka":
            continue
        left: list[str] = []
        right: list[str] = []
        for t in sym.terminals:
            ref = f"{sym.id}:{t.id}"
            if t.x <= edge_frac:
                left.append(ref)
            if t.x >= 1.0 - edge_frac:
                right.append(ref)
        for lref in left:
            for rref in right:
                uf.union(lref, rref)


def _potential_name(
    members: set[str], symbols: list[GraphSymbol], lines: list[GraphLine], idx: int
) -> str:
    member_set = set(members)
    rails: set[str] = set()
    for ln in lines:
        if ln.kind != "link":
            continue
        rail = (ln.rail or "").strip()
        if not rail:
            continue
        if ln.from_ref in member_set or ln.to in member_set:
            rails.add(rail)
    if len(rails) == 1:
        return next(iter(rails))
    if len(rails) > 1:
        return sorted(rails)[0]

    sym_by_id = {s.id: s for s in symbols}
    sym_ids = {m.split(":", 1)[0] for m in members}
    ordered = sorted(
        (sym_by_id[sid] for sid in sym_ids if sid in sym_by_id),
        key=lambda s: (s.bbox[0] + s.bbox[2]) / 2 if len(s.bbox) >= 4 else 0.0,
    )
    for sym in (ordered[0], ordered[-1]) if ordered else ():
        tag = (sym.tag or "").strip()
        if tag:
            return tag
    return f"POT_{idx}"
