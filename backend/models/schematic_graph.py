"""SchematicGraph v2 — GT jako jawny graf OD-DO (symbole + linie terminal→terminal)."""

from __future__ import annotations

from pydantic import BaseModel, Field

from backend.models.schema import ConnectionKind, Terminal


class GraphSymbol(BaseModel):
    id: str
    type: str
    tag: str = ""
    listwa: str = ""  # nazwa potencjału / toru (np. S24VDC) — gł. złączka
    bbox: list[float] = Field(default_factory=list)  # [x1, y1, x2, y2] px absolutne
    terminals: list[Terminal] = Field(default_factory=list)


class GraphLine(BaseModel):
    id: str
    from_ref: str = Field(alias="from")  # {symbol_id}:{terminal_id}
    to: str
    vertices: list[list[float]] = Field(default_factory=list)  # ortho H/V, px absolutne
    kind: ConnectionKind = "power"
    rail: str = ""  # nazwa listwy (kind=link), np. -X1

    model_config = {"populate_by_name": True}


class SchematicGraph(BaseModel):
    version: int = 2
    page_id: str
    image_width: int
    image_height: int
    symbols: list[GraphSymbol] = Field(default_factory=list)
    lines: list[GraphLine] = Field(default_factory=list)
