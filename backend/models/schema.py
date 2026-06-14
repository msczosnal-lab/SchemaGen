"""SchemaModel — centralny kontrakt JSON."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class SchemaMeta(BaseModel):
    source: str = ""
    page: int = 0
    model_version: str = ""
    pages: int = 1


class UserIntent(BaseModel):
    drive_type: str = ""
    power_kw: float | None = None
    control: str = ""


class Component(BaseModel):
    id: str
    type: str
    tag: str = ""
    bbox: list[float] = Field(default_factory=list)
    confidence: float | None = None
    source: Literal["yolo", "ocr", "manual", "block"] = "manual"
    page: int = 0


class Connection(BaseModel):
    from_ref: str = Field(alias="from")
    to: str
    potential: str = ""
    kind: Literal["power", "signal", "pe", "control", "other"] = "power"

    model_config = {"populate_by_name": True}


class SchemaModel(BaseModel):
    meta: SchemaMeta = Field(default_factory=SchemaMeta)
    components: list[Component] = Field(default_factory=list)
    connections: list[Connection] = Field(default_factory=list)
    potentials: list[str] = Field(default_factory=list)
    blocks: list[str] = Field(default_factory=list)
    annotations: list[str] = Field(default_factory=list)
    user_intent: UserIntent | None = None


class ValidationReport(BaseModel):
    approved: bool
    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    suggestions: list[str] = Field(default_factory=list)
    ground_truth_diff: list[str] = Field(default_factory=list)
