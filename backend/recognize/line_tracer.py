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
    """Kolor linii: w pasie prostopadlym wybierz piksel najdalej od bialego tla."""
    x1, y1, x2, y2 = seg
    h, w = bgr.shape[:2]
    dx, dy = x2 - x1, y2 - y1
    length = math.hypot(dx, dy) or 1.0
    nx, ny = -dy / length, dx / length
    pts_b: list[int] = []
    pts_g: list[int] = []
    pts_r: list[int] = []
    for i in range(samples):
        t = i / max(samples - 1, 1)
        cx = x1 + (x2 - x1) * t
        cy = y1 + (y2 - y1) * t
        best_d = -1
        best_px: tuple[int, int, int] | None = None
        for offset in range(-3, 4):
            x = int(round(cx + nx * offset))
            y = int(round(cy + ny * offset))
            if 0 <= x < w and 0 <= y < h:
                b, g, r = (int(v) for v in bgr[y, x])
                d = abs(b - 255) + abs(g - 255) + abs(r - 255)
                if d > best_d:
                    best_d = d
                    best_px = (b, g, r)
        if best_px is not None:
            pts_b.append(best_px[0])
            pts_g.append(best_px[1])
            pts_r.append(best_px[2])
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


# Progi Hough wzgledne do rozdzielczosci strony — skany roznia sie skala
# (Adamed ~6600px vs WRT01). Skalibrowane wzrokowo na p040/p035 (Filip, 2026-06-27):
# frac 0.02 lapie wszystkie przewody bez ucinania (0.03 gubil linie stycznika).
MIN_LEN_FRAC = 0.02      # min_line_length = frac * max(W, H)
GAP_FRAC = 0.0015        # max_line_gap   = frac * max(W, H)
MIN_LEN_FLOOR = 20
HOUGH_FLOOR = 50
GAP_FLOOR = 4


def auto_line_params(w: int, h: int) -> tuple[int, int, int]:
    """Progi Hough z rozmiaru strony -> (min_line_length, hough_threshold, max_line_gap)."""
    big = max(w, h)
    min_len = max(MIN_LEN_FLOOR, round(MIN_LEN_FRAC * big))
    hough = max(HOUGH_FLOOR, min_len)
    gap = max(GAP_FLOOR, round(GAP_FRAC * big))
    return int(min_len), int(hough), int(gap)


class LineTracer:
    """Wykrywanie segmentow. Progi None -> auto wg rozdzielczosci (auto_line_params).

    Jawne wartosci (int) nadpisuja auto-skalowanie — uzywane w testach i kalibracji.
    """

    def __init__(
        self,
        canny_low: int = 50,
        canny_high: int = 150,
        hough_threshold: int | None = None,
        min_line_length: int | None = None,
        max_line_gap: int | None = None,
    ) -> None:
        self.canny_low = canny_low
        self.canny_high = canny_high
        self.hough_threshold = hough_threshold
        self.min_line_length = min_line_length
        self.max_line_gap = max_line_gap

    def _params(self, w: int, h: int) -> tuple[int, int, int]:
        """Efektywne progi: jawne nadpisuja auto; hough auto = max(floor, min_line_length)."""
        auto_len, auto_hough, auto_gap = auto_line_params(w, h)
        min_len = self.min_line_length if self.min_line_length is not None else auto_len
        hough = (
            self.hough_threshold
            if self.hough_threshold is not None
            else max(HOUGH_FLOOR, min_len)
        )
        gap = self.max_line_gap if self.max_line_gap is not None else auto_gap
        return int(min_len), int(hough), int(gap)

    def trace(self, image: "str | np.ndarray") -> list[LineSegment]:
        bgr = _to_bgr(image)
        h, w = bgr.shape[:2]
        min_line_length, hough_threshold, max_line_gap = self._params(w, h)
        gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
        # Schemat: ciemne linie na jasnym tle. Domkniecie cienkich przerw.
        edges = cv2.Canny(gray, self.canny_low, self.canny_high, apertureSize=3)
        kernel = np.ones((3, 3), np.uint8)
        edges = cv2.dilate(edges, kernel, iterations=1)

        raw = cv2.HoughLinesP(
            edges,
            rho=1,
            theta=np.pi / 180,
            threshold=hough_threshold,
            minLineLength=min_line_length,
            maxLineGap=max_line_gap,
        )
        segments: list[LineSegment] = []
        if raw is not None:
            for line in raw:
                x1, y1, x2, y2 = (int(v) for v in line[0])
                color = _sample_color(bgr, (x1, y1, x2, y2))
                segments.append(LineSegment(x1, y1, x2, y2, detected_color=color))

        merged = _merge_collinear(segments)
        # Po scaleniu probkuj kolor ponownie wzdluz finalnej geometrii — odporne
        # na to, ze czesc surowych segmentow Hougha lezy na krawedzi (tlo).
        for seg in merged:
            resampled = _sample_color(
                bgr, (int(seg.x1), int(seg.y1), int(seg.x2), int(seg.y2)), samples=15
            )
            if resampled:
                seg.detected_color = resampled
        return merged
