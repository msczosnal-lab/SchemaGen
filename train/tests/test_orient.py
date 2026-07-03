"""Testy ogolnego silnika orientacji (train/orient.py) dla grup C2/C4/D4."""
from __future__ import annotations

import numpy as np
from PIL import Image

from train.orient import (
    GROUP_ELEMS,
    expand_orientations,
    generate_orient_tiles,
    load_class_gallery,
    parse_orient_tag,
    subclass_names,
)


def _glyph(h=24, w=40):
    im = np.full((h, w), 255, np.uint8)
    im[h // 2, 2:w - 2] = 0     # trzon poziomy (lamie symetrie obrotu)
    im[2:h // 2, 8] = 0         # stub w gore po lewej
    im[h // 2:h - 2, w - 10] = 0
    im[4, 4] = 0
    return im


class _Bbox:
    def __init__(self, x, y, w, h, tag):
        self.x, self.y, self.width, self.height, self.tag = x, y, w, h, tag


class _Rec:
    def __init__(self, page_id, bboxes):
        self.page_id, self.bboxes = page_id, bboxes


def test_subclass_names_per_group():
    assert subclass_names("x", "C4") == ["x_r0", "x_r90", "x_r180", "x_r270"]
    assert subclass_names("x", "C2") == ["x_r0", "x_r180"]
    assert len(subclass_names("x", "D4")) == 8


def test_c4_gallery_size(tmp_path):
    Image.fromarray(_glyph()).save(tmp_path / "wyl_r0.png")
    gal = load_class_gallery("wyl", {"group": "C4", "exemplar_dir": str(tmp_path)})
    assert gal is not None and len(gal) == 4
    assert sorted(loc for _img, loc in gal) == [0, 1, 2, 3]


def _cfg(base, group, ed):
    return {"classes": {base: {"group": group, "exemplar_dir": str(ed)}},
            "min_score": 0.55, "tile": {"size": 96, "margin": 8}}


def test_c4_expand_assigns_rotation(tmp_path):
    base = _glyph()
    Image.fromarray(base).save(tmp_path / "wyl_r0.png")
    cfg = _cfg("wyl", "C4", tmp_path)
    names = subclass_names("wyl", "C4")
    for k in range(4):  # umiesc glif obrocony o k*90 -> oczekuj wyl_r{90k}
        g = np.ascontiguousarray(np.rot90(base, k))
        page = np.full((200, 200), 250, np.uint8)
        page[20:20 + g.shape[0], 20:20 + g.shape[1]] = g
        rec = _Rec("p", [_Bbox(20, 20, g.shape[1], g.shape[0], "wyl")])
        expand_orientations([rec], {"p": page}, cfg)
        assert rec.bboxes[0].tag == names[k], (k, rec.bboxes[0].tag)


def test_c4_tiles_balanced(tmp_path):
    base = _glyph()
    Image.fromarray(base).save(tmp_path / "wyl_r0.png")
    cfg = _cfg("wyl", "C4", tmp_path)
    page = np.full((200, 200), 250, np.uint8)
    page[20:44, 20:60] = base
    tiles = generate_orient_tiles(page, [(20, 20, 40, 24, "wyl_r0")], cfg)
    assert len(tiles) == 4
    assert {n for _t, n, _b in tiles} == set(subclass_names("wyl", "C4"))


def test_c2_two_orientations(tmp_path):
    base = _glyph()
    Image.fromarray(base).save(tmp_path / "wyl_r0.png")
    cfg = _cfg("wyl", "C2", tmp_path)
    page = np.full((200, 200), 250, np.uint8)
    page[20:44, 20:60] = base
    tiles = generate_orient_tiles(page, [(20, 20, 40, 24, "wyl_r0")], cfg)
    assert {n for _t, n, _b in tiles} == {"wyl_r0", "wyl_r180"}


def test_parse_orient_tag(tmp_path):
    cfg = _cfg("wyl", "C4", tmp_path)
    assert parse_orient_tag("wyl_r90", cfg) == ("wyl", "C4", 1)
    assert parse_orient_tag("relay", cfg) is None
