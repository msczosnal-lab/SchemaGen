"""FastAPI labeler — http://localhost:8765"""

from __future__ import annotations

from pathlib import Path

import yaml
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from backend.catalog import list_element_labels, register_labels
from backend.colors.palette import load_palette
from backend.db import init_db, list_pages, load_annotation, save_annotation, upsert_page
from backend.geometry.bbox_layout import enrich_label_record
from backend.paths import RAW, SYMBOL_CLASSES, ensure_data_dirs
from backend.tag_usage import record_tag_usage
from backend.type_picker import list_type_picker
from labeler.export import export_all, write_data_yaml
from backend.models.label import LabelRecord
from backend.models.schema import Component, GraphicLine
from backend.recognize.net_builder import derive_auto_terminals

STATIC_DIR = Path(__file__).resolve().parent / "static"

app = FastAPI(title="SchemaGen Labeler", version="0.1.0")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.on_event("startup")
def startup() -> None:
    ensure_data_dirs()
    init_db()
    for png in sorted(RAW.glob("*.png")):
        upsert_page(png.stem, png.name)


@app.get("/")
def index() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/api/pages")
def api_pages() -> list[dict[str, str]]:
    for png in sorted(RAW.glob("*.png")):
        upsert_page(png.stem, png.name)
    return list_pages()


@app.get("/api/pages/{page_id}/image")
def api_page_image(page_id: str):
    for ext in (".png", ".jpg", ".jpeg"):
        path = RAW / f"{page_id}{ext}"
        if path.exists():
            return FileResponse(path)
    raise HTTPException(404, f"Brak obrazu: {page_id}")


@app.get("/api/classes")
def api_classes() -> dict:
    if not SYMBOL_CLASSES.exists():
        return {"classes": []}
    return yaml.safe_load(SYMBOL_CLASSES.read_text(encoding="utf-8"))


@app.get("/api/element-catalog")
def api_element_catalog() -> dict:
    from backend.db import get_tag_usage_map

    usage = get_tag_usage_map()
    items = []
    for label in list_element_labels():
        cf = label.casefold()
        canonical, count = usage.get(cf, (label, 0))
        items.append({"label": canonical, "usage_count": count})
    return {"labels": items}


@app.get("/api/symbol-palette")
def api_symbol_palette(q: str = "", limit: int = 30) -> dict:
    return {"symbols": list_type_picker(q, limit=min(limit, 100))}


@app.get("/api/semantic-groups")
def api_semantic_groups() -> dict:
    """Grupy semantyczne z config/semantic-colors.yaml — do palety linii w labelerze."""
    palette = load_palette()
    groups = []
    for name, group in palette.groups.items():
        groups.append(
            {
                "name": name,
                "description": group.get("description", ""),
                "stroke": group.get("stroke", ""),
                "fill": group.get("fill", ""),
                "style": group.get("style", "solid"),
                "roles": group.get("roles", []),
            }
        )
    return {"groups": groups}


@app.get("/api/match-color")
def api_match_color(hex: str = "") -> dict:
    """Sugestia grupy semantycznej dla podanego koloru (eyedropper w labelerze)."""
    palette = load_palette()
    group = palette.match_color(hex) if hex else None
    out: dict[str, object] = {"hex": hex, "semantic_group": group or ""}
    if group:
        g = palette.groups.get(group, {})
        out["stroke"] = g.get("stroke", "")
        out["style"] = g.get("style", "solid")
        out["roles"] = g.get("roles", [])
    return out


class TagUsagePayload(BaseModel):
    labels: list[str]


@app.post("/api/tag-usage")
def post_tag_usage(body: TagUsagePayload) -> dict:
    stats = record_tag_usage(body.labels)
    return {"status": "ok", **stats}


class DeriveTerminalsPayload(BaseModel):
    bbox: list[float]                 # [x1, y1, x2, y2] w pikselach obrazu
    lines: list[dict] = []            # [{points:[[x,y]...], role}]
    tol: float = 12.0


@app.post("/api/derive-terminals")
def post_derive_terminals(body: DeriveTerminalsPayload) -> dict:
    """Auto-zaciski z kontaktu linia<->krawedz (ten sam algorytm co runtime)."""
    comp = Component(id="_", type="_", bbox=body.bbox)
    lines = [
        GraphicLine(id=str(i), points=ln.get("points", []), role=ln.get("role", "wire"))
        for i, ln in enumerate(body.lines)
    ]
    terms = derive_auto_terminals(comp, lines, body.tol)
    return {"terminals": [{"id": t.id, "x": t.x, "y": t.y} for t in terms]}


@app.get("/api/annotations/{page_id}")
def get_annotations(page_id: str) -> dict:
    data = load_annotation(page_id)
    if not data:
        return {"page_id": page_id, "bboxes": [], "texts": [], "connections": []}
    # Migracja w locie: stare rekordy bez hierarchii dostaja parent_id/depth/rel_bbox.
    has_hierarchy = any(b.get("parent_id") for b in data.get("bboxes", []))
    if data.get("bboxes") and not has_hierarchy and not data.get("spatial_relations"):
        record = enrich_label_record(LabelRecord.model_validate(data))
        return record.model_dump()
    return data


class AnnotationPayload(BaseModel):
    record: LabelRecord


@app.post("/api/annotations")
def post_annotations(body: AnnotationPayload) -> dict:
    record = enrich_label_record(body.record)
    save_annotation(record.page_id, record.model_dump())
    upsert_page(record.page_id, record.image_path, status="labeled")
    tags = [b.tag for b in record.bboxes if b.tag.strip()]
    added = 0
    try:
        added = register_labels(tags)
    except OSError:
        pass
    depth_max = max((b.depth for b in record.bboxes), default=0)
    unassigned = sum(1 for b in record.bboxes if not b.tag.strip())
    return {
        "status": "saved",
        "page_id": record.page_id,
        "catalog_added": added,
        "bbox_count": len(record.bboxes),
        "unassigned_count": unassigned,
        "hierarchy_depth_max": depth_max,
    }


@app.post("/api/export/{page_id}")
def post_export(page_id: str) -> dict[str, str]:
    data = load_annotation(page_id)
    if not data:
        raise HTTPException(404, "Brak adnotacji")
    record = LabelRecord.model_validate(data)
    paths = export_all(record)
    write_data_yaml()
    return paths


def run(host: str = "127.0.0.1", port: int = 8765) -> None:
    import uvicorn

    uvicorn.run("labeler.app:app", host=host, port=port, reload=False)


if __name__ == "__main__":
    run()
