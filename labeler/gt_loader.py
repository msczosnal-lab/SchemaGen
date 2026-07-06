"""Jednolity loader GT → SchemaModel (graph v2 priorytet, label v1 fallback)."""

from __future__ import annotations

from backend.db import load_annotation, load_schematic_graph
from backend.models.label import LabelRecord
from backend.models.schema import SchemaModel
from labeler.export import label_to_schema
from labeler.graph_compile import graph_to_schema
from backend.models.schematic_graph import SchematicGraph


def gt_source(page_id: str) -> str | None:
    if load_schematic_graph(page_id):
        return "graph_v2"
    if load_annotation(page_id):
        return "label_v1"
    return None


def load_gt_schema(page_id: str) -> SchemaModel | None:
    raw = load_schematic_graph(page_id)
    if raw:
        graph = SchematicGraph.model_validate(raw)
        return graph_to_schema(graph)

    data = load_annotation(page_id)
    if not data:
        return None
    rec = LabelRecord.model_validate(data)
    return label_to_schema(rec)
