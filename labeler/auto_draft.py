"""Auto-draft GT v2: runtime → SchematicGraph + raport diff vs GT."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from backend.db import load_schematic_graph, save_schematic_graph
from backend.models.schematic_graph import SchematicGraph
from backend.paths import RAW, resolve_page_id
from backend.recognize.pipeline import recognize_file
from backend.validate.diff_metrics import diff_graph
from backend.validate.line_failure_analysis import analyze_line_failures
from labeler.gt_loader import load_gt_schema
from labeler.runtime_draft import image_size_for_page
from labeler.schema_to_graph import schema_to_graph


def build_auto_draft(
    page_id: str, progress=None
) -> tuple[SchematicGraph, dict[str, Any]]:
    """Pełny pipeline rozpoznawania → draft SchematicGraph v2."""
    pid = resolve_page_id(page_id)
    img = RAW / f"{pid}.png"
    if not img.exists():
        for ext in (".jpg", ".jpeg"):
            alt = RAW / f"{pid}{ext}"
            if alt.exists():
                img = alt
                break
    if not img.exists():
        raise FileNotFoundError(f"Brak obrazu RAW: {pid}")

    w, h = image_size_for_page(pid)
    if w <= 0 or h <= 0:
        raise FileNotFoundError(f"Brak rozmiaru obrazu dla {pid}")

    schema = recognize_file(str(img), progress=progress)
    graph = schema_to_graph(schema, pid, w, h)

    report: dict[str, Any] = {
        "page_id": pid,
        "image": str(img),
        "draft": {
            "symbols": len(graph.symbols),
            "lines": len(graph.lines),
        },
        "runtime": {
            "components": len(schema.components),
            "graphic_lines": len(schema.graphic_lines),
            "connections": len(schema.connections),
        },
    }

    gt_raw = load_schematic_graph(pid)
    if gt_raw:
        gt_graph = SchematicGraph.model_validate(gt_raw)
        report["diff"] = diff_graph(gt_graph, graph)
        report["line_failures"] = analyze_line_failures(gt_graph, graph)
        report["gt"] = {
            "symbols": len(gt_graph.symbols),
            "lines": len(gt_graph.lines),
        }
    else:
        gt_schema = load_gt_schema(pid)
        if gt_schema and gt_schema.components:
            compiled = schema_to_graph(gt_schema, pid, w, h)
            report["diff"] = diff_graph(compiled, graph)
            report["line_failures"] = analyze_line_failures(compiled, graph)
            report["gt"] = {
                "symbols": len(compiled.symbols),
                "lines": len(compiled.lines),
                "source": "label_v1",
            }

    return graph, report


def save_auto_draft(
    page_id: str,
    *,
    force: bool = False,
    allow_empty: bool = True,
    progress=None,
) -> dict[str, Any]:
    """Zbuduj draft, zapisz do gt/ + cache, zwróć raport."""
    pid = resolve_page_id(page_id)
    if not force:
        existing = load_schematic_graph(pid)
        if existing:
            ex = SchematicGraph.model_validate(existing)
            if ex.symbols or ex.lines:
                return {
                    "status": "skipped_existing",
                    "page_id": pid,
                    "symbol_count": len(ex.symbols),
                    "line_count": len(ex.lines),
                    "message": "GT niepusty — użyj force=true",
                }

    graph, report = build_auto_draft(pid, progress=progress)
    save_schematic_graph(
        pid,
        graph.model_dump(mode="json", by_alias=True),
        allow_empty=allow_empty,
    )
    out = {
        "status": "draft",
        "page_id": pid,
        "symbol_count": len(graph.symbols),
        "line_count": len(graph.lines),
        "report": report,
    }
    if "diff" in report:
        d = report["diff"]
        out["symbols_match"] = d.get("symbols", {}).get("match")
        out["symbols_gt"] = d.get("symbols", {}).get("gt_count")
        out["lines_match"] = d.get("lines", {}).get("match")
        out["lines_gt"] = d.get("lines", {}).get("gt_count")
    return out
