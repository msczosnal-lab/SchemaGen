"""Budowa mapy klas YOLO (multi-class).

Prompt 027 v2: klasa treningowa = `type` (GT v2, `bbox_class`/`class_name`),
`tag` jest oznaczeniem z rysunku i nie wchodzi do YOLO. Fallback: rekordy v1
(SQLite) nie maja `type` — `class_name` zostaje tam zawsze "element", wiec
klasa jest wyprowadzana ze starego pola `tag` (haslo z palety lub wolny
tekst) przez `tag_to_class`. Paleta (config/symbol-palette.yaml) daje
kanoniczne id i kolejnosc.
"""

from __future__ import annotations

import re
import unicodedata
from collections import Counter
from typing import Iterable

import yaml

from functools import lru_cache
from typing import Literal

from backend.paths import CONFIG, SYMBOL_PALETTE, TRAIN_CLASSES

TrainRole = Literal["atomic", "contextual", "anchor"]


_PL = str.maketrans({"\u0142": "l", "\u0141": "L"})  # l z kreska -> l (NFKD go nie rozklada)


def _ascii(text: str) -> str:
    return (
        unicodedata.normalize("NFKD", (text or "").translate(_PL))
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


CLASS_GROUPS = CONFIG / "class-groups.yaml"
CLASS_ALIASES = CONFIG / "class-aliases.yaml"


@lru_cache(maxsize=1)
def load_class_aliases() -> dict[str, str]:
    """Znormalizowany alias -> kanoniczna nazwa klasy (config/class-aliases.yaml)."""
    if not CLASS_ALIASES.exists():
        return {}
    data = yaml.safe_load(CLASS_ALIASES.read_text(encoding="utf-8")) or {}
    raw = data.get("aliases") or {}
    m: dict[str, str] = {}
    for alias, canonical in raw.items():
        if alias and canonical:
            m[normalize_tag(str(alias))] = str(canonical)
    return m


def apply_class_alias(cls: str | None) -> str | None:
    """Ostatni krok kanonizacji: alias EN/PL lub duplikat -> nazwa docelowa."""
    if cls is None:
        return None
    amap = load_class_aliases()
    return amap.get(normalize_tag(cls), cls)


@lru_cache(maxsize=1)
def load_train_roles() -> dict[str, frozenset[str]]:
    """Role klas z config/train-classes.yaml."""
    empty: frozenset[str] = frozenset()
    if not TRAIN_CLASSES.exists():
        return {"atomic": empty, "contextual": empty, "anchor": empty}
    data = yaml.safe_load(TRAIN_CLASSES.read_text(encoding="utf-8")) or {}
    roles = data.get("roles") or {}
    contextual = frozenset(roles.get("contextual") or data.get("contextual") or [])
    return {
        "atomic": frozenset(roles.get("atomic") or []),
        "contextual": contextual,
        "anchor": frozenset(roles.get("anchor") or []),
    }


def class_train_role(
    cls: str,
    roles: dict[str, frozenset[str]] | None = None,
) -> TrainRole:
    r = roles if roles is not None else load_train_roles()
    if cls in r["contextual"]:
        return "contextual"
    if cls in r["anchor"]:
        return "anchor"
    return "atomic"


@lru_cache(maxsize=1)
def load_yolo_exclude_classes() -> frozenset[str]:
    """Klasy bez eksportu YOLO = contextual + anchor."""
    r = load_train_roles()
    return r["contextual"] | r["anchor"]


def is_yolo_exportable(
    tag: str,
    palette_map: dict[str, str] | None = None,
) -> bool:
    """Czy bbox z tym tagiem trafia do eksportu/treningu YOLO."""
    cls = tag_to_class(tag, palette_map)
    if cls is None:
        return False
    roles = load_train_roles()
    role = class_train_role(cls, roles)
    if role != "atomic":
        return False
    if roles["atomic"]:
        return cls in roles["atomic"]
    return True


@lru_cache(maxsize=1)
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


@lru_cache(maxsize=1)
def load_group_map() -> dict[str, str]:
    """member (kanoniczna klasa) -> nazwa grupy (scalanie wizualnie podobnych)."""
    if not CLASS_GROUPS.exists():
        return {}
    data = yaml.safe_load(CLASS_GROUPS.read_text(encoding="utf-8")) or {}
    m: dict[str, str] = {}
    for group, members in (data.get("groups") or {}).items():
        for mem in members or []:
            m[mem] = group
    return m


def component_type_from_bbox(class_name: str, tag: str) -> str:
    """Typ komponentu do SchemaModel / diff GT.

  W labelerze `class_name` zostaje czesto generyczne ``element``; rzeczywisty
  symbol jest w polu ``tag`` (label_pl z palety). Runtime YOLO uzywa kanonicznych
  id z palety — ten helper mapuje GT na ta sama przestrzen nazw.
    """
    if class_name and class_name != "element":
        return class_name
    return tag_to_class(tag) or class_name or "element"


def tag_to_class(
    tag: str,
    palette_map: dict[str, str] | None = None,
    group_map: dict[str, str] | None = None,
) -> str | None:
    """Tag -> kanoniczna nazwa klasy (z ew. scaleniem w grupe). Pusty tag -> None."""
    pmap = palette_map if palette_map is not None else load_palette_map()
    gmap = group_map if group_map is not None else load_group_map()
    norm = normalize_tag(tag)
    if not norm:
        return None
    cls = pmap[norm] if norm in pmap else slugify(tag)
    cls = gmap.get(cls, cls)
    return apply_class_alias(cls)


def bbox_class(
    class_name: str,
    tag: str,
    palette_map: dict[str, str] | None = None,
    group_map: dict[str, str] | None = None,
) -> str | None:
    """Kanoniczna klasa treningowa bboxa — prompt 027 v2 (eksport po `type`, nie `tag`).

    GT v2 (`gt/*.json`) ma `class_name` = kanoniczny `type` symbolu
    (`load_graph_v2_records`). GT v1 (SQLite) ma `class_name == "element"`
    zawsze — dla tych rekordow fallback na `tag_to_class(tag)` jak dotad
    (`tag` to oznaczenie z rysunku typu "6"/"BN", NIE klasa).

    `type` normalizowany przez `slugify` (ascii-fold), zeby
    `custom_urządzenie`/`custom_urzadzenie` (niespojne diakrytyki w GT) scalily
    sie w jedna klase.
    """
    gmap = group_map if group_map is not None else load_group_map()
    norm_type = normalize_tag(class_name)
    if norm_type and norm_type != "element":
        cls = slugify(class_name)
        cls = gmap.get(cls, cls)
        return apply_class_alias(cls)
    return tag_to_class(tag, palette_map, gmap)


def class_distribution(
    records: Iterable,
    palette_map: dict[str, str] | None = None,
    *,
    yolo_only: bool = False,
) -> Counter:
    pmap = palette_map if palette_map is not None else load_palette_map()
    exclude = load_yolo_exclude_classes() if yolo_only else frozenset()
    dist: Counter = Counter()
    for rec in records:
        for b in rec.bboxes:
            cls = bbox_class(b.class_name, b.tag, pmap)
            if cls and cls not in exclude:
                dist[cls] += 1
    return dist


def build_class_map(
    records: Iterable,
    min_count: int = 1,
    other_class: str = "inny",
    bucket_rare: bool = True,
) -> tuple[dict[str, int], Counter]:
    """Mapa nazwa->id z klas w danych.

    Kolejnosc: klasy z palety (te obecne) w kolejnosci palety, potem reszta
    alfabetycznie. Klasy z liczba < min_count:
      - bucket_rare=True  -> wpadaja do `other_class` ("inny"),
      - bucket_rare=False -> sa WYKLUCZONE (bboxy pomijane w treningu).
    """
    pmap = load_palette_map()
    records = list(records)
    dist = class_distribution(records, pmap, yolo_only=True)

    kept = {c: n for c, n in dist.items() if n >= min_count}
    rare = {c: n for c, n in dist.items() if n < min_count}

    order = [c for c in palette_order() if c in kept]
    extras = sorted(c for c in kept if c not in set(order))
    names = order + extras
    if rare and bucket_rare:
        names.append(other_class)

    class_map = {name: idx for idx, name in enumerate(names)}
    return class_map, dist


def resolve_class_id(
    tag: str,
    class_map: dict[str, int],
    palette_map: dict[str, str] | None = None,
    other_class: str = "inny",
    class_name: str = "",
) -> int | None:
    """Id klasy dla bboxa. `class_name` (=`type` w GT v2) ma pierwszenstwo nad
    `tag` — patrz `bbox_class`. Domyslne `class_name=""` = stare zachowanie
    (klasa wylacznie z tagu), dla kompatybilnosci wstecznej wywolan bez GT v2.
    None = pomin (bez tagu/typu / klasa odfiltrowana)."""
    cls = bbox_class(class_name, tag, palette_map)
    if cls is None or cls in load_yolo_exclude_classes():
        return None
    if cls in class_map:
        return class_map[cls]
    if other_class in class_map:
        return class_map[other_class]
    return None
