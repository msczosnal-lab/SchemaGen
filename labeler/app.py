"""FastAPI labeler — http://localhost:8765"""

from __future__ import annotations

from pathlib import Path

import yaml
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from backend.catalog import list_element_labels, register_labels
from backend.db import init_db, list_pages, load_annotation, save_annotation, upsert_page
from backend.paths import RAW, SYMBOL_CLASSES, ensure_data_dirs
from labeler.export import export_all, write_data_yaml
from backend.models.label import LabelRecord

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
    return {"labels": list_element_labels()}


@app.get("/api/annotations/{page_id}")
def get_annotations(page_id: str) -> dict:
    data = load_annotation(page_id)
    return data or {"page_id": page_id, "bboxes": [], "texts": [], "connections": []}


class AnnotationPayload(BaseModel):
    record: LabelRecord


@app.post("/api/annotations")
def post_annotations(body: AnnotationPayload) -> dict:
    record = body.record
    save_annotation(record.page_id, record.model_dump())
    upsert_page(record.page_id, record.image_path, status="labeled")
    tags = [b.tag for b in record.bboxes if b.tag.strip()]
    added = 0
    try:
        added = register_labels(tags)
    except OSError:
        pass
    return {
        "status": "saved",
        "page_id": record.page_id,
        "catalog_added": added,
        "bbox_count": len(record.bboxes),
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
