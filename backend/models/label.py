"""Adnotacje labelera."""

from __future__ import annotations

from pydantic import BaseModel, Field


class BboxAnnotation(BaseModel):
    id: str
    class_name: str
    x: float
    y: float
    width: float
    height: float
    tag: str = ""


class TextAnnotation(BaseModel):
    id: str
    text: str
    x: float
    y: float
    width: float
    height: float


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
    texts: list[TextAnnotation] = Field(default_factory=list)
    connections: list[ConnectionAnnotation] = Field(default_factory=list)
