"""SchemaModel — centralny kontrakt JSON."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

LineRole = Literal[
    "wire",
    "bus",  # DEPRECATED (ADR connection-model): klasyfikator nie nadaje; szyna = wire + potential
    "device_stroke",
    "frame",
    "dash",
    "crossing",
    "leader",
    "cable_marker",  # przerywana przecinajaca kable + etykieta (nazwa/typ/srednica) — adnotacja, nie Connection
    "other",
]
LineStyle = Literal["solid", "dashed", "dotted"]
# "link" = mostek/zworka zlaczka<->zlaczka w listwie (terminal-link); rozne od kabla device<->device
ConnectionKind = Literal["power", "signal", "pe", "control", "link", "other"]
ComponentSource = Literal["yolo", "ocr", "manual", "block"]


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
    source: ComponentSource = "manual"
    page: int = 0
    semantic_group: str = ""
    color_ref: str = ""
    parent_id: str = ""
    depth: int = 0
    rel_bbox: list[float] = Field(default_factory=list)


class SpatialRelation(BaseModel):
    from_id: str
    to_id: str
    relation: Literal["contains", "left_of", "right_of", "above", "below"]


class ContextAssignment(BaseModel):
    """Przypisanie kontekstowe bboxa w wierszu (GT / resolver)."""

    bbox_id: str
    role: str
    row_index: int
    anchor_id: str | None = None
    strip_kind: str | None = None


class GraphicLine(BaseModel):
    """Linia graficzna na schemacie — niekoniecznie polaczenie elektryczne."""

    id: str
    points: list[list[float]] = Field(default_factory=list)
    role: LineRole = "wire"
    style: LineStyle = "solid"
    semantic_group: str = ""
    color_ref: str = ""
    detected_color: str = ""
    page: int = 0


class Connection(BaseModel):
    """Polaczenie logiczne (graf) — pochodzi z linii wire/bus + topologii terminali."""

    from_ref: str = Field(alias="from")
    to: str
    potential: str = ""
    kind: ConnectionKind = "power"

    model_config = {"populate_by_name": True}


class SchemaModel(BaseModel):
    meta: SchemaMeta = Field(default_factory=SchemaMeta)
    components: list[Component] = Field(default_factory=list)
    graphic_lines: list[GraphicLine] = Field(default_factory=list)
    connections: list[Connection] = Field(default_factory=list)
    spatial_relations: list[SpatialRelation] = Field(default_factory=list)
    context_assignments: list[ContextAssignment] = Field(default_factory=list)
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
