"""Uzupelnienie detekcji strzalek potencjalu — dopasowanie wzorca z labeled_tiled.

Model tiled (symbols_tiled_v1-2) ma zerowy recall strzalek na p040 mimo GT w val.
YOLO nie zwraca nawet przy conf=0.05; szablony z treningu daja trafienia ~0.99
w miejscach GT. Wolane tylko gdy YOLO nie znalazl danej klasy.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import cv2
import numpy as np

from backend.models.detection import SymbolDetection
from backend.paths import ROOT
from backend.runtime_config import arrow_supplement_settings

_ARROW_CLASSES = (
    "strzalka_potencjalu_wejsciowa",
    "strzalka_potencjalu_wyjsciowa",
)
_CLASS_TO_YOLO_ID = {7: _ARROW_CLASSES[0], 8: _ARROW_CLASSES[1]}


@lru_cache(maxsize=1)
def _template_gallery() -> dict[str, list[np.ndarray]]:
    """Szablony per klasa z data/labeled_tiled (train+val)."""
    cfg = arrow_supplement_settings()
    max_per_class = int(cfg.get("max_templates_per_class", 12))
    base = ROOT / "data" / "labeled_tiled"
    gallery: dict[str, list[np.ndarray]] = {c: [] for c in _ARROW_CLASSES}
    if not base.exists():
        return gallery

    for split in ("train", "val"):
        labels_dir = base / "labels" / split
        images_dir = base / "images" / split
        if not labels_dir.is_dir():
            continue
        for lbl_path in sorted(labels_dir.glob("*.txt")):
            img_path = images_dir / f"{lbl_path.stem}.png"
            if not img_path.exists():
                continue
            tile = cv2.imread(str(img_path), cv2.IMREAD_GRAYSCALE)
            if tile is None:
                continue
            th, tw = tile.shape[:2]
            for line in lbl_path.read_text(encoding="utf-8").splitlines():
                parts = line.split()
                if len(parts) < 5:
                    continue
                cls_id = int(parts[0])
                class_name = _CLASS_TO_YOLO_ID.get(cls_id)
                if class_name is None:
                    continue
                if len(gallery[class_name]) >= max_per_class:
                    continue
                cx, cy, bw, bh = map(float, parts[1:5])
                x1 = int((cx - bw / 2) * tw)
                y1 = int((cy - bh / 2) * th)
                x2 = int((cx + bw / 2) * tw)
                y2 = int((cy + bh / 2) * th)
                crop = tile[y1:y2, x1:x2]
                if crop.size < 100:
                    continue
                gallery[class_name].append(crop)
    return gallery


def supplement_arrow_detections(
    image_bgr: np.ndarray,
    yolo_detections: list[SymbolDetection],
    *,
    missing_classes: frozenset[str] | None = None,
) -> list[SymbolDetection]:
    """Dopisz strzalki z matchTemplate, jesli YOLO ich nie znalazl."""
    cfg = arrow_supplement_settings()
    if not cfg.get("enabled", True):
        return yolo_detections

    gallery = _template_gallery()
    have = {d.class_name for d in yolo_detections}
    want = missing_classes or frozenset(_ARROW_CLASSES)
    need = [c for c in want if c not in have and gallery.get(c)]
    if not need:
        return yolo_detections

    min_score = float(cfg.get("min_score", 0.88))
    coarse_score = float(cfg.get("coarse_min_score", 0.55))
    downscale = float(cfg.get("downscale", 0.5))
    scales = cfg.get("scales") or [1.0]
    roi_frac = float(cfg.get("roi_top_frac", 0.93))

    gray_full = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2GRAY)
    gray = gray_full
    if downscale != 1.0:
        gray = cv2.resize(
            gray, None, fx=downscale, fy=downscale, interpolation=cv2.INTER_AREA
        )
    cutoff = int(roi_frac * gray.shape[0])

    coarse_hits: list[tuple[str, int, int, int, int, float]] = []
    inv = 1.0 / downscale if downscale else 1.0

    for class_name in need:
        for tmpl in gallery[class_name]:
            for sc in scales:
                t = cv2.resize(tmpl, None, fx=sc, fy=sc, interpolation=cv2.INTER_LINEAR)
                th, tw = t.shape[:2]
                if th > gray.shape[0] or tw > gray.shape[1]:
                    continue
                res = cv2.matchTemplate(gray, t, cv2.TM_CCOEFF_NORMED)
                ys, xs = np.where(res >= coarse_score)
                for y, x in zip(ys, xs):
                    if y > cutoff:
                        continue
                    coarse_hits.append(
                        (class_name, int(x), int(y), tw, th, float(res[y, x]))
                    )

    if not coarse_hits:
        return yolo_detections

    extra: list[SymbolDetection] = []
    seen_boxes: list[tuple[float, float, float, float]] = []

    for class_name, x, y, tw, th, coarse in sorted(
        coarse_hits, key=lambda h: h[5], reverse=True
    ):
        fx = int(x * inv)
        fy = int(y * inv)
        fw = max(8, int(tw * inv))
        fh = max(8, int(th * inv))
        key = (fx, fy, fw, fh)
        if any(_iou_boxes(key, b) >= float(cfg.get("nms_iou", 0.4)) for b in seen_boxes):
            continue
        score = _refine_match_score(gray_full, gallery[class_name], fx, fy, fw, fh)
        if score < min_score:
            continue
        seen_boxes.append(key)
        extra.append(
            SymbolDetection(
                class_id=-1,
                class_name=class_name,
                confidence=score,
                x=float(fx),
                y=float(fy),
                width=float(fw),
                height=float(fh),
            )
        )

    if not extra:
        return yolo_detections

    return list(yolo_detections) + extra


def _refine_match_score(
    gray: np.ndarray,
    templates: list[np.ndarray],
    x: int,
    y: int,
    w: int,
    h: int,
) -> float:
    """NCC na pelnej rozdzielczosci — patch vs najlepszy szablon tej klasy."""
    H, W = gray.shape[:2]
    x1, y1 = max(0, x), max(0, y)
    x2, y2 = min(W, x + w), min(H, y + h)
    patch = gray[y1:y2, x1:x2]
    if patch.size < 50:
        return -1.0
    best = -1.0
    for tmpl in templates:
        th, tw = tmpl.shape[:2]
        if th > patch.shape[0] or tw > patch.shape[1]:
            t = cv2.resize(
                tmpl,
                (patch.shape[1], patch.shape[0]),
                interpolation=cv2.INTER_LINEAR,
            )
        else:
            t = tmpl
        res = cv2.matchTemplate(patch, t, cv2.TM_CCOEFF_NORMED)
        best = max(best, float(res.max()))
    return best


def _iou_boxes(a: tuple[float, float, float, float], b: tuple[float, float, float, float]) -> float:
    ax, ay, aw, ah = a
    bx, by, bw, bh = b
    ax2, ay2 = ax + aw, ay + ah
    bx2, by2 = bx + bw, by + bh
    ix1, iy1 = max(ax, bx), max(ay, by)
    ix2, iy2 = min(ax2, bx2), min(ay2, by2)
    if ix2 <= ix1 or iy2 <= iy1:
        return 0.0
    inter = (ix2 - ix1) * (iy2 - iy1)
    union = aw * ah + bw * bh - inter
    return inter / union if union > 0 else 0.0
