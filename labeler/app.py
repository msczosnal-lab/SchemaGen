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
from backend.db import (
    init_db,
    list_pages,
    load_annotation,
    load_schematic_graph,
    save_annotation,
    save_schematic_graph,
    upsert_page,
)
from backend.geometry.bbox_layout import enrich_label_record
from backend.class_map import component_type_from_bbox
from backend.paths import RAW, SYMBOL_CLASSES, ensure_data_dirs
from backend.tag_usage import record_tag_usage
from backend.type_picker import list_type_picker
from labeler.export import export_all, write_data_yaml
from labeler.runtime_draft import image_size_for_page, schema_to_label_record
from labeler.graph_validate import graph_rules, validate_graph
from labeler.graph_serialize import graph_to_dump
from labeler.graph_prefill import prefill_graph
from backend.models.label import LabelRecord
from backend.models.schema import Component, GraphicLine
from backend.models.schematic_graph import SchematicGraph
from backend.recognize.net_builder import derive_auto_terminals
from backend.recognize.terminal_patterns_io import build_pattern_from_bboxes, save_class_pattern
from backend.recognize.pipeline import recognize_file

STATIC_DIR = Path(__file__).resolve().parent / "static"

app = FastAPI(title="SchemaGen Labeler", version="0.1.0")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.on_event("startup")
def startup() -> None:
    ensure_data_dirs()
    init_db()
    for png in sorted(RAW.glob("*.png")):
        upsert_page(png.stem, png.name)


_NO_CACHE_HEADERS = {"Cache-Control": "no-cache, no-store, must-revalidate"}


@app.get("/")
def graph_ui() -> FileResponse:
    return FileResponse(STATIC_DIR / "graph.html", headers=_NO_CACHE_HEADERS)


@app.get("/legacy")
def legacy_ui() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


class PageListItem(BaseModel):
    id: str
    filename: str
    status: str
    graph_updated_at: str | None = None
    annotation_updated_at: str | None = None


@app.get("/api/pages")
def api_pages() -> list[PageListItem]:
    for png in sorted(RAW.glob("*.png")):
        upsert_page(png.stem, png.name)
    return [PageListItem.model_validate(row) for row in list_pages()]


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
    merge_tol: float | None = None


@app.get("/api/terminal-config")
def api_terminal_config() -> dict:
    """Progi terminali z config/runtime.yaml (labeler = runtime)."""
    from backend.runtime_config import (
        terminal_tol_contact_frac,
        terminal_tol_contact_min,
        terminal_tol_join_min,
    )

    return {
        "contact_tol_frac": terminal_tol_contact_frac(),
        "contact_tol_min": terminal_tol_contact_min(),
        "merge_tol_min": terminal_tol_join_min(),
        "merge_tol_cap": 15.0,
    }


def _effective_merge_tol(contact_tol: float, merge_tol: float | None) -> float:
    if merge_tol is not None:
        return merge_tol
    return min(contact_tol, 15.0)


def _gt_line_role(raw: str) -> str:
    """GT labelera moze miec role bus (legacy) — dla auto-zaciskow traktuj jak wire."""
    role = raw or "wire"
    return "wire" if role == "bus" else role


@app.post("/api/derive-terminals")
def post_derive_terminals(body: DeriveTerminalsPayload) -> dict:
    """Auto-zaciski z kontaktu linia<->krawedz (ten sam algorytm co runtime)."""
    comp = Component(id="_", type="_", bbox=body.bbox)
    lines = [
        GraphicLine(
            id=str(i),
            points=ln.get("points", []),
            role=_gt_line_role(ln.get("role", "wire")),
        )
        for i, ln in enumerate(body.lines)
    ]
    terms = derive_auto_terminals(
        comp, lines, body.tol, merge_tol=_effective_merge_tol(body.tol, body.merge_tol)
    )
    return {"terminals": [{"id": t.id, "x": t.x, "y": t.y} for t in terms]}


class BboxDeriveItem(BaseModel):
    id: str
    bbox: list[float]  # [x1, y1, x2, y2]


class DeriveTerminalsPagePayload(BaseModel):
    bboxes: list[BboxDeriveItem] = []
    lines: list[dict] = []
    tol: float = 12.0
    merge_tol: float | None = None


def _graphic_lines_from_payload(raw_lines: list[dict]) -> list[GraphicLine]:
    return [
        GraphicLine(
            id=str(i),
            points=ln.get("points", []),
            role=_gt_line_role(ln.get("role", "wire")),
        )
        for i, ln in enumerate(raw_lines)
    ]


@app.post("/api/derive-terminals-page")
def post_derive_terminals_page(body: DeriveTerminalsPagePayload) -> dict:
    """Auto-zaciski dla wszystkich bboxow strony (batch)."""
    lines = _graphic_lines_from_payload(body.lines)
    results: dict[str, list[dict[str, float | str]]] = {}
    merge = _effective_merge_tol(body.tol, body.merge_tol)
    for item in body.bboxes:
        comp = Component(id=item.id, type="_", bbox=item.bbox)
        terms = derive_auto_terminals(comp, lines, body.tol, merge_tol=merge)
        results[item.id] = [{"id": t.id, "x": t.x, "y": t.y} for t in terms]
    with_terms = sum(1 for v in results.values() if v)
    return {
        "results": results,
        "with_terminals": with_terms,
        "total": len(results),
    }


class SaveTerminalPatternPayload(BaseModel):
    class_name: str = ""
    page_id: str = ""
    bbox_id: str = ""
    method: str = "line-contact"
    frac_tol: float = 0.15
    bboxes: list[dict] = []


@app.post("/api/save-terminal-pattern")
def post_save_terminal_pattern(body: SaveTerminalPatternPayload) -> dict:
    """Uśrednij terminale GT bboxow klasy -> zapis do terminal-patterns.yaml."""
    class_name = (body.class_name or "").strip()
    samples: list[dict] = []

    if body.page_id:
        data = load_annotation(body.page_id)
        if not data:
            raise HTTPException(404, f"Brak adnotacji: {body.page_id}")
        raw_bboxes = data.get("bboxes") or []
        if not class_name and body.bbox_id:
            for b in raw_bboxes:
                if str(b.get("id")) == body.bbox_id:
                    class_name = component_type_from_bbox(
                        str(b.get("class_name") or ""), str(b.get("tag") or "")
                    )
                    break
        for b in raw_bboxes:
            cls = component_type_from_bbox(
                str(b.get("class_name") or ""), str(b.get("tag") or "")
            )
            if cls != class_name:
                continue
            terms = b.get("terminals") or []
            if terms:
                samples.append({"terminals": terms})
    elif body.bboxes:
        for b in body.bboxes:
            cls = component_type_from_bbox(
                str(b.get("class_name") or ""), str(b.get("tag") or "")
            )
            if class_name and cls != class_name:
                continue
            if not class_name:
                class_name = cls
            terms = b.get("terminals") or []
            if terms:
                samples.append({"terminals": terms})
    else:
        raise HTTPException(400, "Podaj page_id lub bboxes")

    if not class_name:
        raise HTTPException(400, "Nie udało się ustalić class_name")
    if not samples:
        raise HTTPException(400, f"Brak bboxow z terminalami dla klasy {class_name}")

    pattern = build_pattern_from_bboxes(
        samples, method=body.method, frac_tol=body.frac_tol
    )
    save_class_pattern(class_name, pattern)
    return {
        "status": "saved",
        "class_name": class_name,
        "sample_count": len(samples),
        "pattern": pattern,
    }


@app.post("/api/import-runtime-draft/{page_id}")
def post_import_runtime_draft(page_id: str, force: bool = False) -> dict:
    """Draft GT z recognize_file → SQLite (status draft)."""
    if not force:
        existing = load_annotation(page_id)
        if existing and existing.get("bboxes"):
            raise HTTPException(
                409,
                f"Strona {page_id} ma juz bboxy — uzyj ?force=true",
            )
    path = None
    for ext in (".png", ".jpg", ".jpeg"):
        candidate = RAW / f"{page_id}{ext}"
        if candidate.exists():
            path = candidate
            break
    if path is None:
        raise HTTPException(404, f"Brak obrazu: {page_id}")
    schema = recognize_file(str(path))
    w, h = image_size_for_page(page_id)
    record = schema_to_label_record(page_id, schema, w, h)
    save_annotation(page_id, record.model_dump())
    upsert_page(page_id, f"{page_id}{path.suffix}", status="draft")
    return {
        "status": "draft",
        "page_id": page_id,
        "bbox_count": len(record.bboxes),
        "line_count": len(record.lines),
        "connection_count": len(record.connections),
        "terminal_count": sum(len(b.terminals) for b in record.bboxes),
    }


@app.get("/api/annotations/{page_id}")
def get_annotations(page_id: str) -> dict:
    """DEPRECATED v1 — użyj GET /api/graph/{page_id} dla GT grafowego."""
    data = load_annotation(page_id)
    if not data:
        return {"page_id": page_id, "bboxes": [], "texts": [], "lines": [], "connections": []}
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
    """DEPRECATED v1 — użyj POST /api/graph/{page_id} dla GT grafowego."""
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


# --- SchematicGraph v2 (prompt 022) ---


def _empty_graph(page_id: str) -> SchematicGraph:
    w, h = image_size_for_page(page_id)
    return SchematicGraph(
        page_id=page_id,
        image_width=max(w, 1),
        image_height=max(h, 1),
        symbols=[],
        lines=[],
    )


@app.get("/api/graph-rules")
def api_graph_rules() -> dict:
    return graph_rules()


@app.post("/api/graph/validate")
def post_graph_validate(body: SchematicGraph) -> dict:
    result = validate_graph(body)
    return {
        "valid": result.valid,
        "errors": result.errors,
        "warnings": result.warnings,
    }


@app.get("/api/graph/{page_id}")
def get_graph(page_id: str) -> dict:
    data = load_schematic_graph(page_id)
    if not data:
        return _empty_graph(page_id).model_dump(mode="json", by_alias=True)
    graph = SchematicGraph.model_validate(data)
    return graph.model_dump(mode="json", by_alias=True)


@app.post("/api/graph/{page_id}")
def post_graph(page_id: str, body: SchematicGraph) -> dict:
    if body.page_id and body.page_id != page_id:
        raise HTTPException(400, "page_id w body nie zgadza sie z URL")
    graph = body.model_copy(update={"page_id": page_id})
    result = validate_graph(graph)
    if not result.valid:
        raise HTTPException(422, detail={"errors": result.errors})
    save_schematic_graph(page_id, graph.model_dump(mode="json", by_alias=True))
    upsert_page(page_id, f"{page_id}.png", status="labeled")
    out = {
        "status": "saved",
        "page_id": page_id,
        "symbol_count": len(graph.symbols),
        "line_count": len(graph.lines),
    }
    if result.warnings:
        out["warnings"] = result.warnings
    return out


@app.get("/api/graph/{page_id}/dump")
def get_graph_dump(page_id: str) -> dict:
    data = load_schematic_graph(page_id)
    if not data:
        raise HTTPException(404, f"Brak grafu v2: {page_id}")
    graph = SchematicGraph.model_validate(data)
    return {"page_id": page_id, "dump": graph_to_dump(graph)}


@app.post("/api/graph/{page_id}/prefill")
def post_graph_prefill(page_id: str, force: bool = False) -> dict:
    try:
        graph = prefill_graph(page_id, force=force)
    except FileExistsError as exc:
        raise HTTPException(409, str(exc)) from exc
    except FileNotFoundError as exc:
        raise HTTPException(404, str(exc)) from exc
    save_schematic_graph(
        page_id, graph.model_dump(mode="json", by_alias=True)
    )
    upsert_page(page_id, f"{page_id}.png", status="draft")
    return {
        "status": "draft",
        "page_id": page_id,
        "symbol_count": len(graph.symbols),
        "line_count": len(graph.lines),
        "terminal_count": sum(len(s.terminals) for s in graph.symbols),
    }


def run(host: str = "127.0.0.1", port: int = 8765) -> None:
    import uvicorn

    uvicorn.run("labeler.app:app", host=host, port=port, reload=False)


if __name__ == "__main__":
    run()
