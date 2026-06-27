"""Ad-hoc preview kalibracji LineTracer (bez GT, ocena wzrokowa).

Renderuje nakladki wire/bus na skan dla kilku progów (wyrażonych jako % max(W,H),
przenośne między skanami). Otwórz PNG-i z data/output/calib/ i wskaż, który zestaw
pokrywa realne przewody bez śmieci. Potem zaszyję wybrany ułamek w LineTracer.

Uruchom:  .venv311\\Scripts\\python.exe preview_calib.py *p040*
Kolory:   wire = zielony, bus = niebieski (tylko kandydaci na Connection).
Plik throwaway — skasuj po kalibracji.
"""

from __future__ import annotations

import glob
import os
import sys

import cv2

from backend.recognize.line_classifier import LineClassifier
from backend.recognize.line_tracer import LineTracer

# ulamek max(W,H) -> min_line_length. hough_threshold i gap pochodne.
FRACS = [0.005, 0.010, 0.015, 0.020, 0.030]
VIEW_W = 2200          # szerokosc zapisanego podgladu (downscale)
OUT_DIR = "data/output/calib"


def main() -> None:
    pattern = sys.argv[1] if len(sys.argv) > 1 else "*p040*"
    matches = glob.glob(f"data/raw/{pattern}.png")
    if not matches:
        print(f"Brak strony dla wzorca data/raw/{pattern}.png")
        return
    path = matches[0]
    img = cv2.imread(path)
    h, w = img.shape[:2]
    big = max(w, h)
    os.makedirs(OUT_DIR, exist_ok=True)
    clf = LineClassifier()
    base = os.path.splitext(os.path.basename(path))[0]
    scale = VIEW_W / w
    thick = max(2, int(round(big / 900)))

    print(f"Strona: {path}  ({w}x{h})\n")
    print(f"{'frac':>6} {'minLen':>6} {'hough':>5} {'gap':>4} | {'total':>6} {'wire':>5} {'bus':>4}  -> plik")
    for frac in FRACS:
        minlen = max(20, int(round(frac * big)))
        hough = max(50, minlen)
        gap = max(4, int(round(0.0015 * big)))
        segs = LineTracer(
            hough_threshold=hough, min_line_length=minlen, max_line_gap=gap
        ).trace(path)
        lines = clf.classify(segs, image_size=(w, h))

        overlay = img.copy()
        n_wire = n_bus = 0
        for ln in lines:
            if not LineClassifier.is_connection_candidate(ln):
                continue
            color = (0, 200, 0) if ln.role == "wire" else (255, 0, 0)  # BGR
            n_wire += ln.role == "wire"
            n_bus += ln.role == "bus"
            pts = ln.points
            for i in range(len(pts) - 1):
                p1 = (int(pts[i][0]), int(pts[i][1]))
                p2 = (int(pts[i + 1][0]), int(pts[i + 1][1]))
                cv2.line(overlay, p1, p2, color, thick)

        view = cv2.resize(overlay, (VIEW_W, int(round(h * scale))))
        fname = f"{OUT_DIR}/{base}_f{frac:.3f}.png"
        cv2.imwrite(fname, view)
        print(f"{frac:>6.3f} {minlen:>6} {hough:>5} {gap:>4} | {len(segs):>6} {n_wire:>5} {n_bus:>4}  -> {fname}")


if __name__ == "__main__":
    main()
