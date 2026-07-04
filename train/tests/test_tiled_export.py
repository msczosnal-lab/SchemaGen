"""Testy geometrii tilingu (okna, przyciecie bbox, NMS, tile_page)."""
from __future__ import annotations

import numpy as np

from train.tiled_export import clip_bbox, nms, tile_page, windows


def test_windows_cover_and_overlap():
    ws = windows(3000, 2000, win=1536, overlap=0.2)
    assert all(x1 - x0 == 1536 and y1 - y0 == 1536 for x0, y0, x1, y1 in ws)
    # pokrycie prawego/dolnego brzegu (ostatnie okno dosuniete)
    assert max(x1 for _x0, _y0, x1, _y1 in ws) == 3000
    assert max(y1 for _x0, _y0, _x1, y1 in ws) == 2000


def test_windows_small_image_single():
    assert windows(500, 400, win=1536) == [(0, 0, 1536, 1536)]


def test_clip_inside():
    # bbox w calosci w oknie -> wsp. lokalne
    assert clip_bbox(100, 100, 40, 20, (50, 50, 1586, 1586)) == (50, 50, 40, 20)


def test_clip_partial_kept_and_dropped():
    win = (0, 0, 100, 100)
    # 60% widoczne (szer 50, w oknie 30) -> zalezy od progu
    assert clip_bbox(80, 10, 50, 20, win, min_visible=0.3) == (80, 10, 20, 20)
    # tylko 10% widoczne -> None
    assert clip_bbox(95, 10, 50, 20, win, min_visible=0.5) is None
    # calkowicie poza
    assert clip_bbox(200, 200, 10, 10, win) is None


def test_nms_removes_overlap():
    boxes = [(0, 0, 10, 10), (1, 1, 10, 10), (100, 100, 10, 10)]
    keep = nms(boxes, [0.9, 0.8, 0.7], iou_thr=0.45)
    assert set(keep) == {0, 2}  # drugi (nachodzi na pierwszy) odrzucony


def test_tile_page_only_windows_with_boxes():
    page = np.full((2000, 3000), 255, np.uint8)
    bxs = [(100, 100, 40, 20, 5), (2900, 1900, 30, 30, 7)]  # rogi
    tiles = tile_page(page, bxs, win=1536, overlap=0.2, min_visible=0.35)
    assert len(tiles) >= 2
    # kazdy zwrocony kafelek ma >=1 label, wsp. lokalne w zakresie okna
    for wimg, labels in tiles:
        assert labels
        for (x, y, w, h, cid) in labels:
            assert 0 <= x < wimg.shape[1] and 0 <= y < wimg.shape[0]
            assert cid in (5, 7)
