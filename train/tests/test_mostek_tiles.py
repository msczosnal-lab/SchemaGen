"""Testy integracji orientacji mostka: ekspansja tagow + kafelki."""

from __future__ import annotations

import numpy as np

from train.mostek_orient import CLASS_NAMES, D4
from train.mostek_tiles import (
    MostekLog,
    crop_bbox,
    expand_mostek_orientations,
    generate_tiles,
    resolve_orientation,
    write_tiles,
)


def _mostek_glyph(size: int = 30) -> np.ndarray:
    """Crop z DOKLADNIE 3 stubami do krawedzi + chiralnym wnetrzem."""
    img = np.full((size, size), 255, dtype=np.uint8)
    c = size // 2
    img[c, 0:c] = 0            # stub w lewo (1)
    img[0:c, c] = 0            # stub w gore (2)
    img[c:size, c + 4] = 0     # stub w dol, przesuniety = chiralnosc (3)
    img[c, c] = 0
    img[3, 3] = 0              # marker chiralny
    return img


def _templates() -> list[np.ndarray]:
    base = _mostek_glyph()
    return [D4[g].apply_image(base) for g in range(8)]


class _Bbox:
    def __init__(self, x, y, w, h, tag):
        self.x, self.y, self.width, self.height, self.tag = x, y, w, h, tag


class _Rec:
    def __init__(self, page_id, bboxes):
        self.page_id = page_id
        self.bboxes = bboxes


def _page_with_glyph(elem_idx: int, size: int = 200, at=(40, 50)) -> tuple[np.ndarray, tuple]:
    page = np.full((size, size), 250, dtype=np.uint8)
    g = D4[elem_idx].apply_image(_mostek_glyph())
    gh, gw = g.shape
    x, y = at
    page[y : y + gh, x : x + gw] = g
    return page, (x, y, gw, gh)


# --- resolve --------------------------------------------------------------

def test_resolve_orientation_matches_placed_class():
    tpl = _templates()
    for elem_idx in range(8):
        page, (x, y, w, h) = _page_with_glyph(elem_idx)
        crop = crop_bbox(page, x, y, w, h)
        name, score, crossings = resolve_orientation(crop, tpl)
        assert crossings == 3
        assert name == CLASS_NAMES[elem_idx]
        assert score > 0.9


def test_resolve_always_assigns_and_reports_crossings():
    # nowa semantyka: zawsze przypisz najlepsza klase; crossings tylko diagnostyka
    tpl = _templates()
    bad = np.full((30, 30), 255, dtype=np.uint8)
    bad[15, :] = 0  # 2 stuby (lewo+prawo) -> crossings != 3, ale przypisanie jest
    name, _s, crossings = resolve_orientation(bad, tpl)
    assert name in CLASS_NAMES
    assert crossings != 3


# --- ekspansja tagow ------------------------------------------------------

def test_expand_rewrites_tag_to_orientation():
    tpl = _templates()
    page, (x, y, w, h) = _page_with_glyph(3)  # r270
    rec = _Rec("p001", [_Bbox(x, y, w, h, "mostek")])
    log = expand_mostek_orientations([rec], {"p001": page}, tpl)
    assert rec.bboxes[0].tag == "mostek_r270"
    assert log.resolved.get("mostek_r270") == 1


def test_expand_always_assigns_orientation():
    # nowa semantyka: nawet niepewny crop dostaje orientacje (nie gubimy mostkow)
    tpl = _templates()
    page = np.full((200, 200), 250, dtype=np.uint8)
    page[100, 20:60] = 0
    rec = _Rec("p001", [_Bbox(20, 90, 40, 20, "mostek")])
    log = expand_mostek_orientations([rec], {"p001": page}, tpl)
    assert rec.bboxes[0].tag in CLASS_NAMES
    assert sum(log.resolved.values()) == 1


def test_expand_ignores_non_mostek_tags():
    tpl = _templates()
    page, (x, y, w, h) = _page_with_glyph(0)
    rec = _Rec("p001", [_Bbox(x, y, w, h, "relay")])
    expand_mostek_orientations([rec], {"p001": page}, tpl)
    assert rec.bboxes[0].tag == "relay"


# --- kafelki --------------------------------------------------------------

def test_generate_tiles_balanced_eight_per_bbox():
    tpl = _templates()
    page, (x, y, w, h) = _page_with_glyph(1)
    tiles = generate_tiles(page, [(x, y, w, h)], tpl)
    assert len(tiles) == 8
    classes = sorted(cls for _, cls, _ in tiles)
    assert classes == list(range(8))  # pelna, zbalansowana orbita


def test_generate_tiles_bbox_in_range():
    tpl = _templates()
    page, box = _page_with_glyph(2)
    tiles = generate_tiles(page, [box], tpl, tile_size=96)
    for _, _, (cx, cy, bw, bh) in tiles:
        assert 0 < cx < 1 and 0 < cy < 1
        assert 0 < bw <= 1 and 0 < bh <= 1


def test_write_tiles_creates_files(tmp_path):
    tpl = _templates()
    page, box = _page_with_glyph(0)
    tiles = generate_tiles(page, [box], tpl)
    n = write_tiles(tiles, tmp_path / "img", tmp_path / "lbl", "mostek_tile_p001")
    assert n == 8
    assert len(list((tmp_path / "img").glob("*.png"))) == 8
    lbls = list((tmp_path / "lbl").glob("*.txt"))
    assert len(lbls) == 8
    parts = lbls[0].read_text().split()
    assert len(parts) == 5 and 0 <= int(parts[0]) < 8
