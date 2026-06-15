"""Lista typow w pickerze labelera — paleta + wyjatki z katalogu, sortowanie po uzyciu."""

from __future__ import annotations

from backend.catalog import list_element_labels
from backend.db import get_tag_usage_map
from backend.symbol_palette import list_palette_entries


def _entry_text(entry: dict) -> str:
    parts = [str(entry.get("id", "")), str(entry.get("label_pl", ""))]
    aliases = entry.get("aliases") or []
    if isinstance(aliases, list):
        parts.extend(str(a) for a in aliases)
    return " ".join(parts).casefold()


def list_type_picker(query: str, limit: int = 30) -> list[dict]:
    """Paleta IEC + wolne hasla z katalogu. Bez filtra: najczesciej uzywane na gorze."""
    usage_map = get_tag_usage_map()
    entries: list[dict] = []
    seen: set[str] = set()

    for sym in list_palette_entries():
        label = str(sym.get("label_pl") or sym.get("id") or "").strip()
        if not label:
            continue
        key = label.casefold()
        if key in seen:
            continue
        seen.add(key)
        canonical, count = usage_map.get(key, (label, 0))
        entries.append(
            {
                "id": str(sym.get("id", key)),
                "label_pl": canonical,
                "tag_prefix": sym.get("tag_prefix") or "",
                "usage_count": count,
                "custom": False,
            }
        )

    for label in list_element_labels():
        key = label.casefold()
        if key in seen:
            for entry in entries:
                if entry["label_pl"].casefold() == key:
                    entry["custom"] = True
                    break
            continue
        seen.add(key)
        canonical, count = usage_map.get(key, (label, 0))
        entries.append(
            {
                "id": f"custom_{key.replace(' ', '_')[:48]}",
                "label_pl": canonical,
                "tag_prefix": "",
                "usage_count": count,
                "custom": True,
            }
        )

    q = query.strip().casefold()
    if q:
        entries = [e for e in entries if q in _entry_text(e)]

    entries.sort(key=lambda e: (-e["usage_count"], e["label_pl"].casefold()))
    return entries[:limit]
