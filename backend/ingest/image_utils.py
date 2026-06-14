"""Wspolne operacje na obrazach."""

from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np


def load_bgr(image_path: str | Path) -> np.ndarray:
    img = cv2.imread(str(image_path))
    if img is None:
        raise ValueError(f"Nie mozna wczytac obrazu: {image_path}")
    return img


def resize_for_yolo(image: np.ndarray, size: int = 640) -> np.ndarray:
    h, w = image.shape[:2]
    scale = size / max(h, w)
    new_w, new_h = int(w * scale), int(h * scale)
    resized = cv2.resize(image, (new_w, new_h))
    canvas = np.zeros((size, size, 3), dtype=np.uint8)
    canvas[:new_h, :new_w] = resized
    return canvas
