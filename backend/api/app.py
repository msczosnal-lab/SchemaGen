"""FastAPI — localhost API."""

from __future__ import annotations

from fastapi import FastAPI
from pydantic import BaseModel

from backend.generate.composer import BlockComposer
from backend.generate.svg_renderer import SvgRenderer
from backend.models.schema import SchemaModel, ValidationReport
from backend.recognize.pipeline import recognize_file
from backend.validate.rules_engine import RulesEngine

app = FastAPI(title="SchemaGen API", version="0.1.0")


class ValidateRequest(BaseModel):
    model: SchemaModel
    ground_truth: SchemaModel | None = None


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/recognize")
def api_recognize(path: str) -> SchemaModel:
    return recognize_file(path)


@app.post("/validate")
def api_validate(body: ValidateRequest) -> ValidationReport:
    return RulesEngine().validate(body.model, body.ground_truth)


@app.post("/generate")
def api_generate(config_path: str | None = None) -> SchemaModel:
    return BlockComposer().compose_from_config(config_path)


@app.post("/render")
def api_render(model: SchemaModel, output_path: str = "data/output.svg") -> dict[str, str]:
    SvgRenderer().render(model, output_path)
    return {"output": output_path}
