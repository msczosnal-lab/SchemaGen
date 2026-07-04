# COWORK_TASK: sync/prompts/013-orient-classes.md
"""Silnik orientacji/augmentacji klas (konfig: config/orient-classes.yaml).

Per klasa `mode`:
  augment (DOMYSLNY) — klasa uczona jako JEDNA (detekcja), a do treningu dokladane
    sa OBROCONE kopie (kafelki) etykietowane ta sama klasa bazowa -> odpornosc na
    obrot, bez rozrzedzania danych. NIE wymaga eksemplarzy.
  split — klasa rozbijana na podklasy orientacji `X_r0/_r90/...` (detektor zwraca
    orientacje). Wymaga eksemplarzy (dopasowanie wzorcem). Uzyj tylko gdy naprawde
    potrzebujesz orientacji z sieci.

group (zakres obrotow / lustra): D4 (8), C4 (4 obroty), C2 (0/180).
Rdzen D4: train/mostek_orient.py.
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
DEFAULT_MODE = "augment"


def subclass_names(base: str, group: str) -> list[str]:
    return [f"{base}_{_SUF[i]}" for i in GROUP_ELEMS[group]]


def load_orient_config() -> dict:
    import yaml

    path = CONFIG / "orient-classes.yaml"
    if not path.exists():
        return {"classes": {}, "min_score": 0.55, "tile": {"size": 96, "margin": 8}}
    try:
        text = path.read_text(encoding="utf-8").replace("\x00", "")  # mount-safe
        data = yaml.safe_load(text) or {}
    except Exception:
        data = {}
    if not isinstance(data, dict):
        data = {}
    data.setdefault("classes", {})
    data.setdefault("min_score", 0.55)
    data.setdefault("tile", {"size": 96, "margin": 8})
    return data


def _entry(cfg: dict, base: str) -> dict | None:
    return (cfg.get("classes") or {}).get(base)


def _mode(entry: dict) -> str:
    return (entry or {}).get("mode", DEFAULT_MODE)


def _group(entry: dict) -> str:
    return (entry or {}).get("group", "C4")


@dataclass
class OrientLog:
    resolved: dict = field(default_factory=dict)
    low_score: int = 0
    no_image: int = 0
    tiles: int = 0
    classes: dict = field(default_factory=dict)

    def as_dict(self) -> dict:
        return {
            "resolved": self.resolved,
            "low_score": self.low_score,
            "no_image": self.no_image,
            "tiles": self.tiles,
            "classes": self.classes,
        }


# --- galerie wzorcow (tylko tryb split) -----------------------------------

def load_class_gallery(base: str, entry: dict):
    group = _group(entry)
    if group not in GROUP_ELEMS:
        return None
    ed = ROOT / entry.get("exemplar_dir", f"data/{base}_exemplars")
    if not ed.exists():
        return None
    idxs = GROUP_ELEMS[group]
    local_of = {g: k for k, g in enumerate(idxs)}
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
        for i in idxs:
            src = r0 if i // 4 == 0 else m0
            gallery.append((np.ascontiguousarray(np.rot90(src, i % 4)), local_of[i]))
    return gallery or None


def build_galleries(config: dict | None = None) -> dict:
    """base -> (group, gallery) TYLKO dla klas split z eksemplarzami."""
    cfg = config or load_orient_config()
    out = {}
    for base, entry in (cfg.get("classes") or {}).items():
        if _mode(entry) != "split":
            continue
        g = load_class_gallery(base, entry)
        if g:
            out[base] = (_group(entry), g)
    return out


def expand_orientations(records, images_by_page, config=None, log=None):
    """Tryb SPLIT: przepisz tag klasy na podklase orientacji. Tryb augment: nie
    rusza tagow (klasa zostaje bazowa)."""
    cfg = config or load_orient_config()
    min_score = float(cfg.get("min_score", 0.55))
    galleries = build_galleries(cfg)
    log = log or OrientLog()
    for base, entry in (cfg.get("classes") or {}).items():
        log.classes[base] = {"group": _group(entry), "mode": _mode(entry)}
    for rec in records:
        page = images_by_page.get(rec.page_id)
        for b in rec.bboxes:
            base = tag_to_class(b.tag or "")
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
    """`X_r90` -> (base, group, local_idx) dla klasy split; inaczej None."""
    cfg = config or load_orient_config()
    for base, entry in (cfg.get("classes") or {}).items():
        if _mode(entry) != "split":
            continue
        names = subclass_names(base, _group(entry))
        if tag in names:
            return base, _group(entry), names.index(tag)
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


def is_orient_box(tag: str, config=None) -> bool:
    """Czy bbox nalezy do klasy orientowanej/augmentowanej (do zbierania kafelkow)."""
    cfg = config or load_orient_config()
    if parse_orient_tag(tag, cfg):
        return True
    return _entry(cfg, tag_to_class(tag or "")) is not None


def generate_orient_tiles(page, boxes, config=None, log=None):
    """boxes: [(x,y,w,h,tag)]. Zwraca [(tile, class_name, bbox_norm)].
      augment -> obroty cropa etykietowane KLASA BAZOWA,
      split   -> orbita z etykietami podklas."""
    cfg = config or load_orient_config()
    tile_cfg = cfg.get("tile", {}) or {}
    size, margin = int(tile_cfg.get("size", 96)), int(tile_cfg.get("margin", 8))
    log = log or OrientLog()
    out = []
    for (x, y, w, h, tag) in boxes:
        parsed = parse_orient_tag(tag, cfg)  # tag = podklasa (split, po ekspansji)
        if parsed is not None:
            base, group, src_local = parsed
            mode = "split"
        else:
            base = tag_to_class(tag or "")
            entry = _entry(cfg, base)
            if entry is None or _mode(entry) != "augment":
                continue
            group, mode = _group(entry), "augment"
        crop = crop_bbox(page, x, y, w, h)
        if crop.size == 0:
            continue
        if mode == "augment":
            for i in GROUP_ELEMS[group]:
                tile, bbox = _paste(page, D4[i].apply_image(crop), size, margin)
                out.append((tile, base, bbox))
                log.tiles += 1
        else:
            gsrc = GROUP_ELEMS[group][src_local]
            names = subclass_names(base, group)
            for i in GROUP_ELEMS[group]:
                nl = GROUP_ELEMS[group].index(compose(i, gsrc))
                tile, bbox = _paste(page, D4[i].apply_image(crop), size, margin)
                out.append((tile, names[nl], bbox))
                log.tiles += 1
    return out
