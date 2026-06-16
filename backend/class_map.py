"""Budowa mapy klas YOLO z pola `tag` adnotacji (multi-class).

Typ elementu jest oznaczany w labelerze w polu `tag` (haslo z palety lub wolny
tekst), NIE w `class_name` (ktore zostaje "element"). Ten modul tlumaczy tag ->
kanoniczna nazwa klasy i buduje mape nazwa->id ze WSZYSTKICH klas obecnych w
danych. Paleta (config/symbol-palette.yaml) daje kanoniczne id i kolejnosc.
"""

from __future__ import annotations

import re
import unicodedata
from collections import Counter
from typing import Iterable

import yaml

from backend.paths import SYMBOL_PALETTE


def _ascii(text: str) -> str:
    return (
        unicodedata.normalize("NFKD", text or "")
        .encode("ascii", "ignore")
        .decode("ascii")
    )


def normalize_tag(text: str) -> str:
    """Do dopasowania: bez akcentow, lower, scisniete spacje."""
    return re.sub(r"\s+", " ", _ascii(text).strip().lower())


def slugify(text: str) -> str:
    """Nazwa klasy z wolnego tagu: ascii, [a-z0-9_]."""
    slug = re.sub(r"[^a-z0-9]+", "_", _ascii(text).lower()).strip("_")
    return slug or "inny"


def _palette_raw() -> list[dict]:
    if not SYMBOL_PALETTE.exists():
        return []
    data = yaml.safe_load(SYMBOL_PALETTE.read_text(encoding="utf-8")) or {}
    return data.get("symbols", []) or []


def load_palette_map() -> dict[str, str]:
    """Znormalizowane label_pl / aliasy / id -> kanoniczne id klasy."""
    m: dict[str, str] = {}
    for sym in _palette_raw():
        cid = sym.get("id")
        if not cid:
            continue
        names = [sym.get("label_pl"), cid, *(sym.get("aliases") or [])]
        for name in names:
            if name:
                m[normalize_tag(name)] = cid
    return m


def palette_order() -> list[str]:
    return [s.get("id") for s in _palette_raw() if s.get("id")]


def tag_to_class(tag: str, palette_map: dict[str, str] | None = None) -> str | None:
    """Tag -> kanoniczna nazwa klasy. Pusty tag -> None (pomijany w treningu)."""
    pmap = palette_map if palette_map is not None else load_palette_map()
    norm = normalize_tag(tag)
    if not norm:
        return None
    if norm in pmap:
        return pmap[norm]
    return slugify(tag)


def class_distribution(records: Iterable, palette_map: dict[str, str] | None = None) -> Counter:
    pmap = palette_map if palette_map is not None else load_palette_map()
    dist: Counter = Counter()
    for rec in records:
        for b in rec.bboxes:
            cls = tag_to_class(b.tag, pmap)
            if cls:
                dist[cls] += 1
    return dist


def build_class_map(
    records: Iterable,
    min_count: int = 1,
    other_class: str = "inny",
) -> tuple[dict[str, int], Counter]:
    """Mapa nazwa->id ze WSZYSTKICH klas w danych.

    Kolejnosc: klasy z palety (te obecne) w kolejnosci palety, potem reszta
    alfabetycznie. Klasy z liczba < min_count trafiaja do `other_class`.
    """
    pmap = load_palette_map()
    records = list(records)
    dist = class_distribution(records, pmap)

    kept = {c: n for c, n in dist.items() if n >= min_count}
    rare = {c: n for c, n in dist.items() if n < min_count}

    order = [c for c in palette_order() if c in kept]
    extras = sorted(c for c in kept if c not in set(order))
    names = order + extras
    if rare:
        names.append(other_class)

    class_map = {name: idx for idx, name in enumerate(names)}
    return class_map, dist


def resolve_class_id(
    tag: str,
    class_map: dict[str, int],
    palette_map: dict[str, str] | None = None,
    other_class: str = "inny",
) -> int | None:
    """Id klasy dla bboxa wg jego tagu. None = pomin (bez tagu / klasa odfiltrowana)."""
    cls = tag_to_class(tag, palette_map)
    if cls is None:
        return None
    if cls in class_map:
        return class_map[cls]
    if other_class in class_map:
        return class_map[other_class]
    return None
