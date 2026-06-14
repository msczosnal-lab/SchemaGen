"""Paleta haseł typów symboli — picker labelera (bez atlasu QET)."""

from __future__ import annotations

import yaml

from backend.paths import CONFIG

SYMBOL_PALETTE_PATH = CONFIG / "symbol-palette.yaml"


def load_symbol_palette() -> dict:
    if not SYMBOL_PALETTE_PATH.exists():
        return {"meta": {"version": 1}, "symbols": []}
    data = yaml.safe_load(SYMBOL_PALETTE_PATH.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        return {"meta": {"version": 1}, "symbols": []}
    data.setdefault("symbols", [])
    return data


def list_palette_entries() -> list[dict]:
    return [s for s in load_symbol_palette().get("symbols", []) if isinstance(s, dict)]


def _entry_text(entry: dict) -> str:
    parts = [str(entry.get("id", "")), str(entry.get("label_pl", ""))]
    aliases = entry.get("aliases") or []
    if isinstance(aliases, list):
        parts.extend(str(a) for a in aliases)
    return " ".join(parts).casefold()


def search_palette(query: str, limit: int = 30) -> list[dict]:
    entries = list_palette_entries()
    q = query.strip().casefold()
    if not q:
        return entries[:limit]
    matched = [e for e in entries if q in _entry_text(e)]
    return matched[:limit]
