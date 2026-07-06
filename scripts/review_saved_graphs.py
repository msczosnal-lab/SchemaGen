"""Przegląd zapisanych grafów GT v2 w SQLite."""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from backend.models.schematic_graph import SchematicGraph
from backend.paths import DB_PATH
from labeler.graph_serialize import graph_to_dump
from labeler.graph_validate import validate_graph


def main() -> None:
    out = Path(__file__).resolve().parents[1] / "sync" / "review-graphs.txt"
    conn = sqlite3.connect(DB_PATH)
    pages = [
        r[0]
        for r in conn.execute(
            "SELECT page_id FROM schematic_graph ORDER BY updated_at DESC"
        ).fetchall()
    ]
    lines_out: list[str] = []
    for pid in pages:
        raw = json.loads(
            conn.execute(
                "SELECT payload_json FROM schematic_graph WHERE page_id=?", (pid,)
            ).fetchone()[0]
        )
        g = SchematicGraph.model_validate(raw)
        v = validate_graph(g)
        term_refs = {
            f"{s.id}:{t.id}" for s in g.symbols for t in s.terminals
        }
        lines_out.append("=" * 60)
        lines_out.append(pid)
        n_term = sum(len(s.terminals) for s in g.symbols)
        lines_out.append(
            f"symbols={len(g.symbols)} lines={len(g.lines)} terminals={n_term}"
        )
        lines_out.append(f"valid={v.valid}")
        if v.errors:
            lines_out.append(f"errors: {v.errors}")
        if v.warnings:
            lines_out.append(f"warnings: {v.warnings}")
        lines_out.append("--- lines ---")
        for ln in g.lines:
            issues: list[str] = []
            if ln.from_ref not in term_refs:
                issues.append("from missing")
            if ln.to not in term_refs:
                issues.append("to missing")
            if ln.from_ref == ln.to:
                issues.append("self-loop")
            dup = [
                x
                for x in g.lines
                if x.id != ln.id and x.from_ref == ln.from_ref and x.to == ln.to
            ]
            if dup:
                issues.append("duplicate OD-DO")
            extra = f"  !! {issues}" if issues else ""
            lines_out.append(
                f"  {ln.id}: {ln.from_ref} -> {ln.to} [{ln.kind}]{extra}"
            )
        lines_out.append("--- symbols ---")
        for i, s in enumerate(g.symbols, 1):
            terms = ",".join(t.id for t in s.terminals) or "-"
            tag = s.tag or ""
            lines_out.append(f"  #{i} {s.id} {s.type} tag={tag} terms=[{terms}]")
        no_term = [s.id for s in g.symbols if not s.terminals]
        if no_term:
            lines_out.append(f"bez terminali: {no_term}")
        lines_out.append("--- dump ---")
        lines_out.append(graph_to_dump(g))
        lines_out.append("")
    conn.close()
    out.write_text("\n".join(lines_out), encoding="utf-8")
    print(out)


if __name__ == "__main__":
    main()
