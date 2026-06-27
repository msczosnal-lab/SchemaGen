"""Ad-hoc sweep progow LineTracer pod kalibracje (prompt 004 follow-up).

Cel: zbic szum Hough (p040: 1321 linii) do sensownej liczby, NIE gubiac wire/bus.
Uruchom:  .venv311\\Scripts\\python.exe calib_lines.py *p040*
Czytaj kolumne wire/bus (kandydaci na Connection) vs total — szukaj "kolana":
total mocno spada, wire/bus trzyma sie. Plik mozna skasowac po kalibracji.
"""

from __future__ import annotations

import glob
import sys

import cv2

from backend.recognize.line_classifier import LineClassifier
from backend.recognize.line_tracer import LineTracer

# (canny_low, canny_high, hough_threshold, min_line_length, max_line_gap)
GRID = [
    (50, 150, 50, 30, 8),    # baseline (obecne defaulty)
    (50, 150, 80, 60, 6),
    (50, 150, 100, 80, 5),
    (60, 180, 120, 120, 4),
    (60, 180, 150, 160, 3),
    (80, 200, 180, 200, 3),
]


def main() -> None:
    pattern = sys.argv[1] if len(sys.argv) > 1 else "*p040*"
    matches = glob.glob(f"data/raw/{pattern}.png")
    if not matches:
        print(f"Brak strony dla wzorca data/raw/{pattern}.png")
        return
    path = matches[0]
    img = cv2.imread(path)
    h, w = img.shape[:2]
    clf = LineClassifier()
    print(f"Strona: {path}  ({w}x{h})\n")
    print(f"{'canny':>9} {'hough':>5} {'minLen':>6} {'gap':>3} | {'total':>6} {'wire/bus':>8}")
    for cl, ch, ht, ml, mg in GRID:
        tracer = LineTracer(
            canny_low=cl, canny_high=ch,
            hough_threshold=ht, min_line_length=ml, max_line_gap=mg,
        )
        segs = tracer.trace(path)
        lines = clf.classify(segs, image_size=(w, h))
        wb = sum(1 for l in lines if LineClassifier.is_connection_candidate(l))
        print(f"{cl:>4}/{ch:<4} {ht:>5} {ml:>6} {mg:>3} | {len(segs):>6} {wb:>8}")


if __name__ == "__main__":
    main()
