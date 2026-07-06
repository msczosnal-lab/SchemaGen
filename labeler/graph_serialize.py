"""Dump tekstowy SchematicGraph v2 (lista Filipa)."""

from __future__ import annotations

from backend.models.schematic_graph import SchematicGraph


def graph_to_dump(graph: SchematicGraph) -> str:
    lines_out: list[str] = []
    term_to_lines: dict[str, list[str]] = {}
    for ln in graph.lines:
        for ref in (ln.from_ref, ln.to):
            term_to_lines.setdefault(ref, []).append(ln.id)

    for sym in graph.symbols:
        tag_part = f" [{sym.tag}]" if sym.tag else ""
        lines_out.append(f"bbox: {sym.type}{tag_part}")
        for t in sym.terminals:
            ref = f"{sym.id}:{t.id}"
            linked = term_to_lines.get(ref, [])
            link_str = f" → {','.join(linked)}" if linked else ""
            lines_out.append(
                f"  terminal_{t.id} @ ({t.x:.3f},{t.y:.3f}){link_str}"
            )

    for ln in graph.lines:
        verts = ln.vertices
        if verts:
            parts = "→".join(f"({int(v[0])},{int(v[1])})" for v in verts if len(v) >= 2)
            fold_str = f"; załamania: {parts}"
        else:
            fold_str = ""
        lines_out.append(
            f"line: {ln.id} OD {ln.from_ref} DO {ln.to}{fold_str}; kind={ln.kind}"
        )

    return "\n".join(lines_out)
