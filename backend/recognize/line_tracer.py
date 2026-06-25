# COWORK_TASK: sync/prompts/003-line-tracer-classifier.md

"""Wykrywanie linii graficznych na schemacie — OpenCV + sampling koloru.

LineTracer.trace() zwraca geometryczne segmenty (`LineSegment`) z probka koloru
(`detected_color`, hex). NIE klasyfikuje roli ani polaczen — to robi LineClassifier
(rola/grupa) i dalej GraphBuilder (Connection). Linia != polaczenie.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import cv2
import numpy as np


@dataclass
class LineSegment:
    x1: float
    y1: float
    x2: float
    y2: float
    detected_color: str = ""

    @property
    def length(self) -> float:
        return math.hypot(self.x2 - self.x1, self.y2 - self.y1)

    @property
    def angle_deg(self) -> float:
        """Kat w stopniach [0, 180) — nieskierowany."""
        a = math.degrees(math.atan2(self.y2 - self.y1, self.x2 - self.x1)) % 180.0
        return a


def _to_bgr(image: "str | np.ndarray") -> np.ndarray:
    if isinstance(image, str):
        img = cv2.imread(image, cv2.IMREAD_COLOR)
        if img is None:
            raise FileNotFoundError(f"Nie mozna wczytac obrazu: {image}")
        return img
    arr = np.asarray(image)
    if arr.ndim == 2:
        return cv2.cvtColor(arr, cv2.COLOR_GRAY2BGR)
    if arr.ndim == 3 and arr.shape[2] == 4:
        return cv2.cvtColor(arr, cv2.COLOR_BGRA2BGR)
    return arr


def _bgr_to_hex(b: int, g: int, r: int) -> str:
    return f"#{int(r):02x}{int(g):02x}{int(b):02x}"


def _sample_color(bgr: np.ndarray, seg: tuple[int, int, int, int], samples: int = 9) -> str:
    """Mediana koloru wzdluz srodka segmentu (odporna na tlo/antialiasing)."""
    x1, y1, x2, y2 = seg
    h, w = bgr.shape[:2]
    pts_b: list[int] = []
    pts_g: list[int] = []
    pts_r: list[int] = []
    for i in range(samples):
        t = i / max(samples - 1, 1)
        x = int(round(x1 + (x2 - x1) * t))
        y = int(round(y1 + (y2 - y1) * t))
        if 0 <= x < w and 0 <= y < h:
            px = bgr[y, x]
            pts_b.append(int(px[0]))
            pts_g.append(int(px[1]))
            pts_r.append(int(px[2]))
    if not pts_b:
        return ""
    return _bgr_to_hex(
        int(np.median(pts_b)), int(np.median(pts_g)), int(np.median(pts_r))
    )


def _merge_collinear(
    segments: list[LineSegment],
    angle_tol_deg: float = 6.0,
    gap_tol: float = 12.0,
) -> list[LineSegment]:
    """Lacz kolinearne i bliskie segmenty w dluzsze linie."""
    remaining = sorted(segments, key=lambda s: -s.length)
    merged: list[LineSegment] = []
    used = [False] * len(remaining)
    for i, base in enumerate(remaining):
        if used[i]:
            continue
        x1, y1, x2, y2 = base.x1, base.y1, base.x2, base.y2
        colors = [base.detected_color] if base.detected_color else []
        for j in range(i + 1, len(remaining)):
            if used[j]:
                continue
            other = remaining[j]
            d_ang = abs(base.angle_deg - other.angle_deg)
            d_ang = min(d_ang, 180.0 - d_ang)
            if d_ang > angle_tol_deg:
                continue
            if _endpoints_gap((x1, y1, x2, y2), other) > gap_tol:
                continue
            # rozszerz po osi bazowej: zbierz wszystkie 4 konce, wez skrajne
            x1, y1, x2, y2 = _extend_along((x1, y1, x2, y2), other)
            if other.detected_color:
                colors.append(other.detected_color)
            used[j] = True
        used[i] = True
        merged.append(
            LineSegment(x1, y1, x2, y2, detected_color=_dominant_color(colors))
        )
    return merged


def _dominant_color(colors: list[str]) -> str:
    if not colors:
        return ""
    counts: dict[str, int] = {}
    for c in colors:
        counts[c] = counts.get(c, 0) + 1
    return max(counts.items(), key=lambda kv: kv[1])[0]


def _endpoints_gap(a: tuple[float, float, float, float], b: LineSegment) -> float:
    ax1, ay1, ax2, ay2 = a
    pts_a = [(ax1, ay1), (ax2, ay2)]
    pts_b = [(b.x1, b.y1), (b.x2, b.y2)]
    return min(math.hypot(pa[0] - pb[0], pa[1] - pb[1]) for pa in pts_a for pb in pts_b)


def _extend_along(
    a: tuple[float, float, float, float], b: LineSegment
) -> tuple[float, float, float, float]:
    pts = [(a[0], a[1]), (a[2], a[3]), (b.x1, b.y1), (b.x2, b.y2)]
    # rzutuj na kierunek bazowy, wez skrajne
    ox, oy = a[0], a[1]
    dx, dy = a[2] - a[0], a[3] - a[1]
    norm = math.hypot(dx, dy) or 1.0
    ux, uy = dx / norm, dy / norm
    projs = [((px - ox) * ux + (py - oy) * uy, (px, py)) for px, py in pts]
    pmin = min(projs, key=lambda p: p[0])[1]
    pmax = max(projs, key=lambda p: p[0])[1]
    return (pmin[0], pmin[1], pmax[0], pmax[1])


class LineTracer:
    def __init__(
        self,
        canny_low: int = 50,
        canny_high: int = 150,
        hough_threshold: int = 50,
        min_line_length: int = 30,
        max_line_gap: int = 8,
    ) -> None:
        self.canny_low = canny_low
        self.canny_high = canny_high
        self.hough_threshold = hough_threshold
        self.min_line_length = min_line_length
        self.max_line_gap = max_line_gap

    def trace(self, image: "str | np.ndarray") -> list[LineSegment]:
        bgr = _to_bgr(image)
        gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
        # Schemat: ciemne linie na jasnym tle. Domkniecie cienkich przerw.
        edges = cv2.Canny(gray, self.canny_low, self.canny_high, apertureSize=3)
        kernel = np.ones((3, 3), np.uint8)
        edges = cv2.dilate(edges, kernel, iterations=1)

        raw = cv2.HoughLinesP(
            edges,
            rho=1,
            theta=np.pi / 180,
            threshold=self.hough_threshold,
            minLineLength=self.min_line_length,
            maxLineGap=self.max_line_gap,
        )
        segments: list[LineSegment] = []
        if raw is not None:
            for line in raw:
                x1, y1, x2, y2 = (int(v) for v in line[0])
                color = _sample_color(bgr, (x1, y1, x2, y2))
                segments.append(LineSegment(x1, y1, x2, y2, detected_color=color))

        return _merge_collinear(segments)
