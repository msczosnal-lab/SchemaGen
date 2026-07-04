# COWORK_TASK: sync/prompts/013-orient-classes.md
"""Ogolny silnik orientacji klas (uogolnienie mostka na dowolna klase).

Konfiguracja: config/orient-classes.yaml — klasa -> grupa obrotow (C2/C4/D4) +
katalog eksemplarzy. Dla wpisanej klasy `X`:
  - tag `X` jest rozbijany na podklasy orientacji (`X_r0`, `X_r90`, ...),
  - do treningu dokladane sa kafelki (orbita grupy) dla balansu.

Grupy jako PODGRUPY D4 (indeksy elementow D4, i = m*4 + r):
  D4 -> (0..7)  : 4 obroty + 4 lustra (symbol chiralny),
  C4 -> (0,1,2,3): 4 obroty (bez lustra),
  C2 -> (0,2)    : 0 / 180 (poziom/pion).
Podgrupy sa zamkniete na skladanie -> augmentacja i etykiety spojne.

Rdzen D4/dopasowanie: train/mostek_orient.py.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

from backend.class_map import tag_to_class
from backend.paths import CONFIG, ROOT
from train.mostek_orient import D4, classify_gallery, compose, count_edge_crossings
from train.mostek_tiles import _find_exemplar, _sample_background, crop_bbox

_SUF = ("r0", "r90", "r180", "r270", "m0", "m90", "m180", "m270")
GROUP_ELEMS = {
    "D4": (0, 1, 2, 3, 4, 5, 6, 7),
    "C4": (0, 1, 2, 3),
    "C2": (0, 2),
}


def subclass_names(base: str, group: str) -> list[str]:
    """Nazwy podklas orientacji dla klasy bazowej i grupy (kolejnosc = orbita)."""
    return [f"{base}_{_SUF[i]}" for i in GROUP_ELEMS[group]]


def load_orient_config() -> dict:
    import yaml

    path = CONFIG / "orient-classes.yaml"
    if not path.exists():
        return {"classes": {}, "min_score": 0.55, "tile": {"size": 96, "margin": 8}}
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    data.setdefault("classes", {})
    data.setdefault("min_score", 0.55)
    data.setdefault("tile", {"size": 96, "margin": 8})
    return data


@dataclass
class OrientLog:
    resolved: dict = field(default_factory=dict)
    low_score: int = 0
    no_image: int = 0
    tiles: int = 0
    classes: dict = field(default_factory=dict)  # base -> {group, n_exemplars}

    def as_dict(self) -> dict:
        return {
            "resolved": self.resolved,
            "low_score": self.low_score,
            "no_image": self.no_image,
            "tiles": self.tiles,
            "classes": self.classes,
        }


def _orbit_from_exemplars(r0: np.ndarray, m0: np.ndarray, group: str):
    """(obraz, indeks_globalny_D4) dla elementow grupy — z baz r0/m0."""
    for i in GROUP_ELEMS[group]:
        base = r0 if i // 4 == 0 else m0
        yield np.ascontiguousarray(np.rot90(base, i % 4)), i


def load_class_gallery(base: str, entry: dict):
    """Galeria [(obraz, local_idx)] dla klasy: wykrywa prefiksy `<base>*_r0`
    (wiele stylow), buduje orbite grupy. Brak wzorcow -> None."""
    group = entry.get("group", "C4")
    if group not in GROUP_ELEMS:
        return None
    ed = ROOT / entry.get("exemplar_dir", f"data/{base}_exemplars")
    if not ed.exists():
        return None
    idxs = GROUP_ELEMS[group]
    local_of = {gidx: k for k, gidx in enumerate(idxs)}
    # prefiksy grup stylow: pliki konczace sie na _r0.<ext>
    prefixes = []
    for f in sorted(ed.iterdir()):
        n = f.name.lower()
        for ext in (".png", ".jpg", ".jpeg"):
            if n.endswith("_r0" + ext):
                prefixes.append(f.name[: -len("_r0" + ext)])
    gallery: list = []
    for pref in prefixes:
        r0 = _find_exemplar(ed, f"{pref}_r0")
        if r0 is None:
            continue
        m0 = _find_exemplar(ed, f"{pref}_m0")
        if m0 is None:
            m0 = np.fliplr(r0)
        for img, gidx in _orbit_from_exemplars(r0, m0, group):
            gallery.append((img, local_of[gidx]))
    return gallery or None


def build_galleries(config: dict | None = None) -> dict:
    """base -> (group, gallery) dla klas z eksemplarzami."""
    cfg = config or load_orient_config()
    out = {}
    for base, entry in (cfg.get("classes") or {}).items():
        g = load_class_gallery(base, entry)
        if g:
            out[base] = (entry.get("group", "C4"), g)
    return out


def expand_orientations(records, images_by_page, config=None, log=None):
    """Przepisz tagi klas z configu na podklasy orientacji (dopasowanie wzorcem).
    ZAWSZE przypisuje najlepsza (nie gubi obiektow); niska pewnosc w logu."""
    cfg = config or load_orient_config()
    min_score = float(cfg.get("min_score", 0.55))
    galleries = build_galleries(cfg)
    log = log or OrientLog()
    for base, (group, gal) in galleries.items():
        log.classes[base] = {"group": group, "n_exemplars": len(gal)}
    for rec in records:
        page = images_by_page.get(rec.page_id)
        for b in rec.bboxes:
            base = tag_to_class(b.tag or "")  # kanoniczna klasa (label -> class)
            if base not in galleries:
                continue
            if page is None:
                log.no_image += 1
                continue
            crop = crop_bbox(page, b.x, b.y, b.width, b.height)
            if crop.size == 0:
                log.no_image += 1
                continue
            group, gal = galleries[base]
            local, score = classify_gallery(crop, gal)
            name = subclass_names(base, group)[local]
            b.tag = name
            log.resolved[name] = log.resolved.get(name, 0) + 1
            if score < min_score:
                log.low_score += 1
    return log


def parse_orient_tag(tag: str, config=None):
    """`X_r90` -> (base, group, local_idx) jesli X jest klasa orientowana; inaczej None."""
    cfg = config or load_orient_config()
    for base, entry in (cfg.get("classes") or {}).items():
        group = entry.get("group", "C4")
        names = subclass_names(base, group)
        if tag in names:
            return base, group, names.index(tag)
    return None


def _paste(page, crop, tile_size, margin):
    tile = _sample_background(page, tile_size)
    gray = crop if crop.ndim == 2 else crop[..., :3].mean(axis=2)
    th, tw = gray.shape[:2]
    max_in = tile_size - 2 * margin
    if th > max_in or tw > max_in:
        from PIL import Image

        sc = max_in / max(th, tw)
        nh, nw = max(1, int(th * sc)), max(1, int(tw * sc))
        gray = np.asarray(Image.fromarray(gray.astype(np.uint8)).resize((nw, nh), Image.NEAREST))
        th, tw = nh, nw
    oy, ox = (tile_size - th) // 2, (tile_size - tw) // 2
    tile[oy:oy + th, ox:ox + tw] = gray.astype(np.uint8)
    cx, cy = (ox + tw / 2) / tile_size, (oy + th / 2) / tile_size
    return tile, (cx, cy, tw / tile_size, th / tile_size)


def generate_orient_tiles(page, boxes, config=None, log=None):
    """boxes: [(x,y,w,h,tag)] gdzie tag = podklasa orientacji.
    Zwraca [(tile, class_name, bbox_norm)] — orbita grupy dla kazdego boxa."""
    cfg = config or load_orient_config()
    tile_cfg = cfg.get("tile", {}) or {}
    size, margin = int(tile_cfg.get("size", 96)), int(tile_cfg.get("margin", 8))
    log = log or OrientLog()
    out = []
    for (x, y, w, h, tag) in boxes:
        parsed = parse_orient_tag(tag, cfg)
        if parsed is None:
            continue
        base, group, src_local = parsed
        gsrc = GROUP_ELEMS[group][src_local]
        crop = crop_bbox(page, x, y, w, h)
        if crop.size == 0:
            continue
        names = subclass_names(base, group)
        for i in GROUP_ELEMS[group]:
            timg = D4[i].apply_image(crop)
            new_global = compose(i, gsrc)
            new_local = GROUP_ELEMS[group].index(new_global)
            tile, bbox = _paste(page, timg, size, margin)
            out.append((tile, names[new_local], bbox))
            log.tiles += 1
    return out
