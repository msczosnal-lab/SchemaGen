"""Diagnostyka linii (read-only): histogram detected_color per rola / semantic_group.

Nie modyfikuje danych — tylko trace + classify + zliczanie. Pomaga wykryc linie bez
grupy semantycznej (np. niebieski tusz przed kalibracja palety) i rozklad kolorow.

Uzycie:
    python scripts/diag_lines.py --page p027
    python scripts/diag_lines.py --page data/raw/..._p027.png --top 15
"""

from __future__ import annotations

import argparse
from collections import Counter
from pathlib import Path

import cv2

from backend.paths import raw_image_path
from backend.recognize.line_classifier import LineClassifier
from backend.recognize.line_tracer import LineTracer


def _resolve(page: str) -> Path | None:
    p = Path(page)
    if p.exists():
        return p
    return raw_image_path(page)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--page", required=True, help="skrot (p027) lub sciezka PNG")
    ap.add_argument("--top", type=int, default=12, help="ile kolorow w histogramie")
    args = ap.parse_args()

    path = _resolve(args.page)
    if path is None or not path.exists():
        print(f"[BLAD] Nie znaleziono strony: {args.page}")
        return 1

    img = cv2.imread(str(path))
    if img is None:
        print(f"[BLAD] Nie wczytano obrazu: {path}")
        return 1
    h, w = img.shape[:2]

    segments = LineTracer().trace(str(path))
    lines = LineClassifier().classify(segments, image_size=(w, h))

    roles = Counter(l.role for l in lines)
    groups = Counter(l.semantic_group or "<brak>" for l in lines)
    colors = Counter(l.detected_color or "<brak>" for l in lines)
    # Kolory linii BEZ grupy semantycznej — kandydaci do kalibracji palety.
    no_group_colors = Counter(
        l.detected_color or "<brak>" for l in lines if not l.semantic_group
    )

    print(f"# {path.stem}  ({w}x{h})  segs={len(segments)} lines={len(lines)}")
    print(f"role: {dict(roles)}")
    print(f"semantic_group: {dict(groups)}")
    print(f"top {args.top} detected_color:")
    for hexv, n in colors.most_common(args.top):
        print(f"  {hexv:>10}  {n}")
    if no_group_colors:
        print(f"kolory BEZ semantic_group (kandydaci do palety), top {args.top}:")
        for hexv, n in no_group_colors.most_common(args.top):
            print(f"  {hexv:>10}  {n}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
