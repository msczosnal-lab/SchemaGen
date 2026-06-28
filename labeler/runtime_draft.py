"""Konwersja SchemaModel (runtime) → LabelRecord (draft GT labelera)."""

from __future__ import annotations

from pathlib import Path

import cv2

from backend.models.label import (
    BboxAnnotation,
    ConnectionAnnotation,
    LabelRecord,
    LineAnnotation,
    Terminal,
)
from backend.models.schema import SchemaModel
from backend.paths import RAW


def image_size_for_page(page_id: str) -> tuple[int, int]:
    for ext in (".png", ".jpg", ".jpeg"):
        path = RAW / f"{page_id}{ext}"
        if path.exists():
            img = cv2.imread(str(path))
            if img is not None:
                return int(img.shape[1]), int(img.shape[0])
    return 0, 0


def schema_to_label_record(
    page_id: str,
    schema: SchemaModel,
    image_width: int = 0,
    image_height: int = 0,
) -> LabelRecord:
    """Mapuj wynik recognize_file / GraphBuilder na rekord labelera."""
    w, h = image_width, image_height
    if w <= 0 or h <= 0:
        w, h = image_size_for_page(page_id)

    bboxes: list[BboxAnnotation] = []
    for i, c in enumerate(schema.components):
        if len(c.bbox) < 4:
            continue
        x1, y1, x2, y2 = c.bbox[0], c.bbox[1], c.bbox[2], c.bbox[3]
        bboxes.append(
            BboxAnnotation(
                id=c.id,
                class_name=c.type or "element",
                x=float(x1),
                y=float(y1),
                width=float(max(x2 - x1, 1)),
                height=float(max(y2 - y1, 1)),
                tag=(c.tag or c.type or "").strip(),
                seq=i + 1,
                semantic_group=c.semantic_group or "",
                color_ref=c.color_ref or "",
                parent_id=c.parent_id or "",
                depth=c.depth or 0,
                rel_bbox=list(c.rel_bbox),
                terminals=[
                    Terminal(id=t.id, x=t.x, y=t.y, name=t.name or "")
                    for t in c.terminals
                ],
            )
        )

    lines = [
        LineAnnotation(
            id=ln.id,
            points=[list(p) for p in ln.points],
            role=ln.role,
            style=ln.style,
            semantic_group=ln.semantic_group or "",
            color_ref=ln.color_ref or "",
        )
        for ln in schema.graphic_lines
    ]

    connections = [
        ConnectionAnnotation(
            id=conn.id or f"conn_{i}",
            from_ref=conn.from_ref,
            to=conn.to,
            kind=conn.kind,
        )
        for i, conn in enumerate(schema.connections)
    ]

    return LabelRecord(
        page_id=page_id,
        image_path=f"{page_id}.png",
        image_width=w,
        image_height=h,
        bboxes=bboxes,
        lines=lines,
        texts=[],
        connections=connections,
        spatial_relations=list(schema.spatial_relations),
    )
