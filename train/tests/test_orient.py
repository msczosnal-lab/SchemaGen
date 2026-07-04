"""Testy silnika orientacji/augmentacji (train/orient.py): tryby augment i split."""
from __future__ import annotations

import numpy as np
from PIL import Image

from train.orient import (
    expand_orientations,
    generate_orient_tiles,
    is_orient_box,
    load_class_gallery,
    parse_orient_tag,
    subclass_names,
)


def _glyph(h=24, w=40):
    im = np.full((h, w), 255, np.uint8)
    im[h // 2, 2:w - 2] = 0
    im[2:h // 2, 8] = 0
    im[h // 2:h - 2, w - 10] = 0
    im[4, 4] = 0
    return im


class _Bbox:
    def __init__(self, x, y, w, h, tag):
        self.x, self.y, self.width, self.height, self.tag = x, y, w, h, tag


class _Rec:
    def __init__(self, page_id, bboxes):
        self.page_id, self.bboxes = page_id, bboxes


def _cfg(base, group, ed, mode):
    return {"classes": {base: {"group": group, "exemplar_dir": str(ed), "mode": mode}},
            "min_score": 0.55, "tile": {"size": 96, "margin": 8}}


def _page_with(glyph, at=(20, 20)):
    page = np.full((200, 200), 250, np.uint8)
    x, y = at
    page[y:y + glyph.shape[0], x:x + glyph.shape[1]] = glyph
    return page, (x, y, glyph.shape[1], glyph.shape[0])


def test_subclass_names_per_group():
    assert subclass_names("x", "C4") == ["x_r0", "x_r90", "x_r180", "x_r270"]
    assert subclass_names("x", "C2") == ["x_r0", "x_r180"]
    assert len(subclass_names("x", "D4")) == 8


# --- AUGMENT (domyslny): 1 klasa, kafelki jako klasa bazowa ---------------

def test_augment_does_not_rewrite_tag(tmp_path):
    cfg = _cfg("wyl", "C4", tmp_path, "augment")
    page, (x, y, w, h) = _page_with(_glyph())
    rec = _Rec("p", [_Bbox(x, y, w, h, "wyl")])
    expand_orientations([rec], {"p": page}, cfg)
    assert rec.bboxes[0].tag == "wyl"  # augment nie rusza tagu


def test_augment_tiles_all_base_class(tmp_path):
    cfg = _cfg("wyl", "C4", tmp_path, "augment")
    page, box = _page_with(_glyph())
    tiles = generate_orient_tiles(page, [(*box, "wyl")], cfg)
    assert len(tiles) == 4  # orbita C4
    assert {n for _t, n, _b in tiles} == {"wyl"}  # wszystkie jako klasa bazowa


def test_augment_no_exemplars_needed(tmp_path):
    # brak eksemplarzy, a augment i tak generuje kafelki
    cfg = _cfg("wyl", "C2", tmp_path, "augment")
    page, box = _page_with(_glyph())
    tiles = generate_orient_tiles(page, [(*box, "wyl")], cfg)
    assert len(tiles) == 2 and {n for _t, n, _b in tiles} == {"wyl"}


# --- SPLIT: podklasy orientacji (wymaga eksemplarzy) ----------------------

def test_split_expands_tag(tmp_path):
    Image.fromarray(_glyph()).save(tmp_path / "wyl_r0.png")
    cfg = _cfg("wyl", "C4", tmp_path, "split")
    base = _glyph()
    names = subclass_names("wyl", "C4")
    for k in range(4):
        g = np.ascontiguousarray(np.rot90(base, k))
        page, (x, y, w, h) = _page_with(g)
        rec = _Rec("p", [_Bbox(x, y, w, h, "wyl")])
        expand_orientations([rec], {"p": page}, cfg)
        assert rec.bboxes[0].tag == names[k], (k, rec.bboxes[0].tag)


def test_split_tiles_subclasses(tmp_path):
    Image.fromarray(_glyph()).save(tmp_path / "wyl_r0.png")
    cfg = _cfg("wyl", "C4", tmp_path, "split")
    page, box = _page_with(_glyph())
    tiles = generate_orient_tiles(page, [(*box, "wyl_r0")], cfg)
    assert {n for _t, n, _b in tiles} == set(subclass_names("wyl", "C4"))


def test_split_gallery_size(tmp_path):
    Image.fromarray(_glyph()).save(tmp_path / "wyl_r0.png")
    gal = load_class_gallery("wyl", {"group": "C4", "exemplar_dir": str(tmp_path)})
    assert gal is not None and len(gal) == 4


def test_is_orient_box(tmp_path):
    cfg = _cfg("wyl", "C4", tmp_path, "augment")
    assert is_orient_box("wyl", cfg)          # augment: tag bazowy
    assert not is_orient_box("relay", cfg)
    cfg2 = _cfg("wyl", "C4", tmp_path, "split")
    assert is_orient_box("wyl_r90", cfg2)     # split: podklasa
