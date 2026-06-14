"""Eksport LabelRecord -> YOLO + SchemaModel ground truth."""

from __future__ import annotations

import json
from pathlib import Path

import yaml

from backend.geometry.bbox_layout import enrich_label_record
from backend.models.label import LabelRecord
from backend.models.schema import (
    Component,
    Connection,
    GraphicLine,
    SchemaMeta,
    SchemaModel,
    SpatialRelation,
)
from backend.paths import CONFIG, LABELED


def load_class_map() -> dict[str, int]:
    path = CONFIG / "symbol-classes.yaml"
    if not path.exists():
        return {}
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    classes = data.get("classes", [])
    return {name: idx for idx, name in enumerate(classes)}


def label_to_schema(record: LabelRecord) -> SchemaModel:
    # Hierarchia/relacje moga byc puste w starych rekordach — przelicz w locie.
    if not record.spatial_relations:
        record = enrich_label_record(record)
    components = [
        Component(
            id=b.id,
            type=b.class_name,
            tag=b.tag,
            bbox=[b.x, b.y, b.x + b.width, b.y + b.height],
            source="manual",
            semantic_group=b.semantic_group,
            color_ref=b.color_ref,
            parent_id=b.parent_id,
            depth=b.depth,
            rel_bbox=b.rel_bbox,
        )
        for b in record.bboxes
    ]
    spatial_relations = [
        SpatialRelation(from_id=r.from_id, to_id=r.to_id, relation=r.relation)
        for r in record.spatial_relations
    ]
    graphic_lines = [
        GraphicLine(
            id=line.id,
            points=line.points,
            role=line.role,
            style=line.style,
            semantic_group=line.semantic_group,
            color_ref=line.color_ref,
        )
        for line in record.lines
    ]
    connections = [
        Connection.model_validate({"from": c.from_ref, "to": c.to, "kind": c.kind})
        for c in record.connections
    ]
    annotations = [t.text for t in record.texts]
    return SchemaModel(
        meta=SchemaMeta(source=record.page_id, page=0),
        components=components,
        graphic_lines=graphic_lines,
        connections=connections,
        annotations=annotations,
    )


def export_yolo(record: LabelRecord, output_dir: Path | None = None) -> Path:
    out = output_dir or LABELED
    labels_dir = out / "labels"
    images_dir = out / "images"
    labels_dir.mkdir(parents=True, exist_ok=True)
    images_dir.mkdir(parents=True, exist_ok=True)

    class_map = load_class_map()
    w = record.image_width or 1
    h = record.image_height or 1
    lines: list[str] = []
    for b in record.bboxes:
        cls_id = class_map.get(b.class_name, 0)
        cx = (b.x + b.width / 2) / w
        cy = (b.y + b.height / 2) / h
        bw = b.width / w
        bh = b.height / h
        lines.append(f"{cls_id} {cx:.6f} {cy:.6f} {bw:.6f} {bh:.6f}")

    label_file = labels_dir / f"{record.page_id}.txt"
    label_file.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")
    return label_file


def export_all(record: LabelRecord, output_dir: Path | None = None) -> dict[str, str]:
    out = output_dir or LABELED
    out.mkdir(parents=True, exist_ok=True)
    yolo_path = export_yolo(record, out)
    schema = label_to_schema(record)
    schema_path = out / f"{record.page_id}.schema.json"
    schema_path.write_text(schema.model_dump_json(by_alias=True, indent=2), encoding="utf-8")
    raw_path = out / f"{record.page_id}.label.json"
    raw_path.write_text(record.model_dump_json(indent=2), encoding="utf-8")
    return {
        "yolo": str(yolo_path),
        "schema": str(schema_path),
        "label": str(raw_path),
    }


def write_data_yaml(output_dir: Path | None = None) -> Path:
    out = output_dir or LABELED
    class_map = load_class_map()
    data = {
        "path": str(out.resolve()),
        "train": "images",
        "val": "images",
        "names": {idx: name for name, idx in class_map.items()},
    }
    dest = out / "data.yaml"
    dest.write_text(yaml.dump(data, allow_unicode=True), encoding="utf-8")
    return dest
