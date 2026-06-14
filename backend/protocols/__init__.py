"""Protokoły modułów — kontrakt MVP = final."""

from backend.protocols.exporter import LabelExporterProtocol
from backend.protocols.recognizer import RecognizerProtocol, SymbolDetectorProtocol
from backend.protocols.renderer import RendererProtocol
from backend.protocols.validator import ValidatorProtocol

__all__ = [
    "LabelExporterProtocol",
    "RecognizerProtocol",
    "RendererProtocol",
    "SymbolDetectorProtocol",
    "ValidatorProtocol",
]
