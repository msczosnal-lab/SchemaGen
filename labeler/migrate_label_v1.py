"""Migracja LabelRecord v1 → SchematicGraph v2 (tylko bbox + terminale, bez linii)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

from backend.class_map import component_type_from_bbox
from backend.db import has_schematic_graph, load_annotation, save_schematic_graph
from backend.models.label import LabelRecord
from backend.models.schema import Terminal
from backend.models.schematic_graph import GraphSymbol, SchematicGraph
from labeler.runtime_draft import image_size_for_page

MigrateStatus = Literal["ok", "skipped", "error"]


@dataclass
class MigrateReport:
    page_id: str
    status: MigrateStatus
    reason: str = ""
    symbols: int = 0
    terminals: int = 0
    lines: int = 0
    symbols_without_terminals: list[str] = field(default_factory=list)


def label_record_to_graph(record: LabelRecord) -> SchematicGraph:
    """Bboxy i terminale z v1; linie zawsze puste (rysujesz je w labelerze v2)."""
    w = record.image_width
    h = record.image_height
    if w <= 0 or h <= 0:
        w, h = image_size_for_page(record.page_id)
    if w <= 0 or h <= 0:
        raise ValueError(f"Brak rozmiaru obrazu dla {record.page_id}")

    symbols: list[GraphSymbol] = []
    for b in record.bboxes:
        symbols.append(
            GraphSymbol(
                id=b.id,
                type=component_type_from_bbox(b.class_name, b.tag),
                tag=b.tag or "",
                bbox=[b.x, b.y, b.x + b.width, b.y + b.height],
                terminals=[
                    Terminal(id=t.id, x=t.x, y=t.y, name=t.name or "")
                    for t in b.terminals
                ],
            )
        )

    return SchematicGraph(
        page_id=record.page_id,
        image_width=w,
        image_height=h,
        symbols=symbols,
        lines=[],
    )


def migrate_page(
    page_id: str,
    *,
    force: bool = False,
    dry_run: bool = False,
) -> MigrateReport:
    """Migruj jedną stronę. Bez linii — tylko symbole i terminale z adnotacji v1."""
    if not force and has_schematic_graph(page_id):
        return MigrateReport(
            page_id=page_id,
            status="skipped",
            reason="graf v2 już istnieje (użyj force=True)",
        )

    data = load_annotation(page_id)
    if not data:
        return MigrateReport(
            page_id=page_id,
            status="skipped",
            reason="brak adnotacji v1",
        )

    record = LabelRecord.model_validate(data)
    if not record.bboxes:
        return MigrateReport(
            page_id=page_id,
            status="skipped",
            reason="adnotacja v1 bez bboxów",
        )

    try:
        graph = label_record_to_graph(record)
    except ValueError as exc:
        return MigrateReport(page_id=page_id, status="error", reason=str(exc))

    without_terminals = [s.id for s in graph.symbols if not s.terminals]
    terminal_count = sum(len(s.terminals) for s in graph.symbols)

    if not dry_run:
        save_schematic_graph(page_id, graph.model_dump(mode="json", by_alias=True))

    return MigrateReport(
        page_id=page_id,
        status="ok",
        reason="dry-run" if dry_run else "zapisano",
        symbols=len(graph.symbols),
        terminals=terminal_count,
        lines=0,
        symbols_without_terminals=without_terminals,
    )
