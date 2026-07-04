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
    downscale = float(cfg.get("downscale", 0.5))
    scales = cfg.get("scales") or [1.0]
    roi_frac = float(cfg.get("roi_top_frac", 0.93))

    gray = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2GRAY)
    if downscale != 1.0:
        gray = cv2.resize(
            gray, None, fx=downscale, fy=downscale, interpolation=cv2.INTER_AREA
        )
    cutoff = int(roi_frac * gray.shape[0])

    extra: list[SymbolDetection] = []
    inv = 1.0 / downscale if downscale else 1.0

    for class_name in need:
        for tmpl in gallery[class_name]:
            for sc in scales:
                t = cv2.resize(tmpl, None, fx=sc, fy=sc, interpolation=cv2.INTER_LINEAR)
                th, tw = t.shape[:2]
                if th > gray.shape[0] or tw > gray.shape[1]:
                    continue
                res = cv2.matchTemplate(gray, t, cv2.TM_CCOEFF_NORMED)
                ys, xs = np.where(res >= min_score)
                for y, x in zip(ys, xs):
                    if y > cutoff:
                        continue
                    score = float(res[y, x])
                    extra.append(
                        SymbolDetection(
                            class_id=-1,
                            class_name=class_name,
                            confidence=score,
                            x=float(x) * inv,
                            y=float(y) * inv,
                            width=float(tw) * inv,
                            height=float(th) * inv,
                        )
                    )

    if not extra:
        return yolo_detections

    merged = list(yolo_detections) + _nms_arrows(extra, float(cfg.get("nms_iou", 0.4)))
    return merged


def _nms_arrows(dets: list[SymbolDetection], iou_thr: float) -> list[SymbolDetection]:
    """NMS tylko na dopelnieniach (unikaj duplikatow tego samego strzalki)."""
    if not dets:
        return []
    dets = sorted(dets, key=lambda d: d.confidence, reverse=True)
    keep: list[SymbolDetection] = []
    for d in dets:
        if all(_iou(d, k) < iou_thr for k in keep):
            keep.append(d)
    return keep


def _iou(a: SymbolDetection, b: SymbolDetection) -> float:
    ax2, ay2 = a.x + a.width, a.y + a.height
    bx2, by2 = b.x + b.width, b.y + b.height
    ix1, iy1 = max(a.x, b.x), max(a.y, b.y)
    ix2, iy2 = min(ax2, bx2), min(ay2, by2)
    if ix2 <= ix1 or iy2 <= iy1:
        return 0.0
    inter = (ix2 - ix1) * (iy2 - iy1)
    union = a.width * a.height + b.width * b.height - inter
    return inter / union if union > 0 else 0.0
