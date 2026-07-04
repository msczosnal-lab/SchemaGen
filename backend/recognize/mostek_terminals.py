"""Auto-terminale mostka z geometrii tuszu na obwodzie cropa bbox.

Mostek ma 3 stuby na krawedzi bboxa. W przeciwienstwie do listwy (derive_auto_terminals
z koncow wire), stub mostka czesto nie lezy na krawedzi od zewnetrznego przewodu
w tym samym miejscu co terminal GT — wiec skanujemy obwod binarized cropa (logika
z train/mostek_orient.count_edge_crossings, ale ze wspolrzednymi rel 0..1).
"""

from __future__ import annotations

import cv2
import numpy as np

from backend.models.schema import Component, Terminal
from backend.recognize.mostek_orient_map import is_mostek_class
from train.mostek_orient import binarize

_MOSTEK_STUB_COUNT = 3


def derive_mostek_terminals(
    component: Component,
    image_bgr: np.ndarray,
    *,
    pad_px: int = 2,
) -> list[Terminal]:
    """3 terminale z pozycji tuszu na obwodzie cropa mostka. Pusty gdy nie mostek/brak obrazu."""
    if not is_mostek_class(component.type):
        return []
    b = component.bbox
    if len(b) < 4:
        return []
    h_img, w_img = image_bgr.shape[:2]
    x1 = max(0, int(b[0]) - pad_px)
    y1 = max(0, int(b[1]) - pad_px)
    x2 = min(w_img, int(b[2]) + pad_px)
    y2 = min(h_img, int(b[3]) + pad_px)
    if x2 <= x1 or y2 <= y1:
        return []
    crop = image_bgr[y1:y2, x1:x2]
    rel = _stub_rel_positions(binarize(crop))
    if len(rel) != _MOSTEK_STUB_COUNT:
        return []
    rel.sort(key=lambda p: (round(p[1], 2), round(p[0], 2)))
    return [
        Terminal(id=str(i + 1), x=round(u, 4), y=round(v, 4))
        for i, (u, v) in enumerate(rel)
    ]


def _stub_rel_positions(binary: np.ndarray) -> list[tuple[float, float]]:
    """Srodki segmentow tuszu na obwodzie cropa -> (u,v) wzgledem bbox 0..1."""
    h, w = binary.shape
    if h < 3 or w < 3:
        return []
    top = binary[0, :]
    right = binary[:, -1]
    bottom = binary[-1, ::-1]
    left = binary[::-1, 0]
    ring = np.concatenate([top, right[1:], bottom[1:], left[1:-1]])
    per = len(ring)
    if per == 0:
        return []

    segments: list[float] = []
    i = 0
    while i < per:
        if ring[i] < 0.5:
            i += 1
            continue
        j = i
        while j < per and ring[j] >= 0.5:
            j += 1
        segments.append((i + j - 1) / 2.0)
        i = j

    return [_ring_index_to_uv(mid, h, w) for mid in segments]


def _ring_index_to_uv(t: float, h: int, w: int) -> tuple[float, float]:
    """Indeks na obwodzie prostokata h x w -> wspolrzedne wzgledne (u,v)."""
    wm = max(w - 1, 1)
    hm = max(h - 1, 1)
    if t < w:
        return (t / wm, 0.0)
    t -= w
    if t < h - 1:
        return (1.0, (t + 1) / hm)
    t -= h - 1
    if t < w - 1:
        return (1.0 - (t + 1) / wm, 1.0)
    t -= w - 1
    return (0.0, 1.0 - (t + 1) / hm)


def load_bgr(image_path: str) -> np.ndarray | None:
    """Best-effort wczytanie strony (uzywane w graph_builder)."""
    img = cv2.imread(str(image_path))
    return img
