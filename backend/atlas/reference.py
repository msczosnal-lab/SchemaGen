"""Loader i lookup dla config/symbol-reference.yaml."""

from __future__ import annotations

from pathlib import Path

import yaml

from backend.paths import CONFIG

REFERENCE_PATH = CONFIG / "symbol-reference.yaml"


def load_symbol_reference(path: Path | None = None) -> dict:
    """Laduje YAML. Zwraca dict z kluczami 'meta' i 'symbols'."""
    p = path or REFERENCE_PATH
    if not p.exists():
        return {"meta": {}, "symbols": []}
    data = yaml.safe_load(p.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        return {"meta": {}, "symbols": []}
    data.setdefault("meta", {})
    data.setdefault("symbols", [])
    return data


def lookup_by_id(symbol_id: str, path: Path | None = None) -> dict | None:
    """Zwraca wpis po dokładnym 'id'. None jesli nie znaleziono."""
    for sym in load_symbol_reference(path)["symbols"]:
        if sym.get("id") == symbol_id:
            return sym
    return None


def lookup_by_alias(alias: str, path: Path | None = None) -> dict | None:
    """Case-insensitive wyszukiwanie po id lub aliases_pl."""
    alias_lower = alias.strip().lower()
    for sym in load_symbol_reference(path)["symbols"]:
        if sym.get("id", "").lower() == alias_lower:
            return sym
        for a in sym.get("aliases_pl", []):
            if str(a).lower() == alias_lower:
                return sym
    return None
