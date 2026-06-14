"""Wynik detekcji symbolu."""

from pydantic import BaseModel


class SymbolDetection(BaseModel):
    class_id: int
    class_name: str
    confidence: float
    x: float
    y: float
    width: float
    height: float
