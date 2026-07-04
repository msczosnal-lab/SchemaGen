"""Adnotacje labelera."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

LineRole = Literal[
    "wire",
    "bus",  # DEPRECATED (ADR connection-model): szyna = wire + potential
    "device_stroke",
    "frame",
    "dash",
    "crossing",
    "leader",
    "cable_marker",  # przerywana opisujaca kabel (nazwa/typ/srednica) — adnotacja
    "other",
]
LineStyle = Literal["solid", "dashed", "dotted"]


class Terminal(BaseModel):
    """Zacisk na obrysie komponentu (ADR connection-model, etap 2). x,y wzgledne [0,1]."""

    id: str
    x: float
    y: float
    name: str = ""


class BboxAnnotation(BaseModel):
    id: str
    class_name: str
    x: float
    y: float
    width: float
    height: float
    tag: str = ""
    seq: int = 0
    semantic_group: str = ""
    color_ref: str = ""
    parent_id: str = ""
    depth: int = 0
    rel_bbox: list[float] = Field(default_factory=list)  # [rx, ry, rw, rh] wzgledem rodzica
    terminals: list[Terminal] = Field(default_factory=list)


class SpatialRelation(BaseModel):
    from_id: str
    to_id: str
    relation: Literal["contains", "left_of", "right_of", "above", "below"]


class TextAnnotation(BaseModel):
    id: str
    text: str
    x: float
    y: float
    width: float
    height: float
    inherits_color_from: str | None = None


class LineAnnotation(BaseModel):
    id: str
    points: list[list[float]] = Field(default_factory=list)
    role: LineRole = "wire"
    style: LineStyle = "solid"
    semantic_group: str = ""
    color_ref: str = ""


class ConnectionAnnotation(BaseModel):
    id: str
    from_ref: str = Field(alias="from")
    to: str
    kind: str = "power"

    model_config = {"populate_by_name": True}


class LabelRecord(BaseModel):
    page_id: str
    image_path: str
    image_width: int = 0
    image_height: int = 0
    bboxes: list[BboxAnnotation] = Field(default_factory=list)
    lines: list[LineAnnotation] = Field(default_factory=list)
    texts: list[TextAnnotation] = Field(default_factory=list)
    connections: list[ConnectionAnnotation] = Field(default_factory=list)
    spatial_relations: list[SpatialRelation] = Field(default_factory=list)
