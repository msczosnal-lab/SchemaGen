"""Wycinki (wnetrza bboxow) pogrupowane PER KLASA — co naprawde widzi model.

Tnie kazdy bbox z wyeksportowanego datasetu YOLO i grupuje w galerii wg klasy.
Pozwala wzrokowo ocenic spojnosc etykiet danej klasy (szum/pomylki).

Uzycie:
    python scripts/visualize_class_crops.py
    python scripts/visualize_class_crops.py --per-class 80 --class zacisk
"""

from __future__ import annotations

import argparse
from collections import defaultdict
from pathlib import Path

import cv2
import yaml

from backend.paths import LABELED

OUT_DIR = Path(__file__).resolve().parents[1] / "data" / "output" / "class_crops"


def _names() -> dict[int, str]:
    yml = LABELED / "data.yaml"
    if not yml.exists():
        return {}
    data = yaml.safe_load(yml.read_text(encoding="utf-8")) or {}
    n = data.get("names", {})
    return {int(k): str(v) for k, v in n.items()} if isinstance(n, dict) else {i: str(v) for i, v in enumerate(n)}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--per-class", type=int, default=60, help="ile wycinkow na klase w galerii")
    ap.add_argument("--class", dest="only", default=None, help="tylko ta klasa")
    ap.add_argument("--pad", type=float, default=0.0, help="margines kontekstu (0 = samo wnetrze)")
    ap.add_argument("--out", type=Path, default=OUT_DIR)
    args = ap.parse_args()

    names = _names()
    if not names:
        print(f"[BŁĄD] Brak {LABELED/'data.yaml'}. Najpierw: python -m train.dataset_export")
        return 1

    args.out.mkdir(parents=True, exist_ok=True)
    for old in args.out.glob("*.png"):
        old.unlink()

    counts: dict[str, int] = defaultdict(int)      # ile zapisano (galeria)
    totals: dict[str, int] = defaultdict(int)      # ile wszystkich
    by_class: dict[str, list[str]] = defaultdict(list)

    for split in ("train", "val"):
        img_dir = LABELED / "images" / split
        lbl_dir = LABELED / "labels" / split
        if not img_dir.exists():
            continue
        for img_path in sorted(img_dir.glob("*")):
            if img_path.suffix.lower() not in (".png", ".jpg", ".jpeg"):
                continue
            lbl = lbl_dir / f"{img_path.stem}.txt"
            if not lbl.exists():
                continue
            img = None
            H = W = 0
            for line in lbl.read_text(encoding="utf-8").splitlines():
                p = line.split()
                if len(p) != 5:
                    continue
                cid = int(float(p[0])); cx, cy, bw, bh = map(float, p[1:])
                cls = names.get(cid, str(cid))
                if args.only and cls != args.only:
                    continue
                totals[cls] += 1
                if counts[cls] >= args.per_class:
                    continue
                if img is None:
                    img = cv2.imread(str(img_path))
                    if img is None:
                        break
                    H, W = img.shape[:2]
                mx = args.pad * bw; my = args.pad * bh
                x1 = max(int((cx - bw / 2 - mx) * W), 0); y1 = max(int((cy - bh / 2 - my) * H), 0)
                x2 = min(int((cx + bw / 2 + mx) * W), W); y2 = min(int((cy + bh / 2 + my) * H), H)
                if x2 <= x1 or y2 <= y1:
                    continue
                crop = img[y1:y2, x1:x2]
                fn = f"{cls}__{counts[cls]:03d}.png"
                cv2.imwrite(str(args.out / fn), crop)
                by_class[cls].append(fn)
                counts[cls] += 1

    if not by_class:
        print("Brak wycinkow (pusty dataset?).")
        return 1

    sections = []
    for cls in sorted(by_class, key=lambda c: -totals[c]):
        thumbs = "".join(f"<img src='{f}' title='{f}'>" for f in by_class[cls])
        sections.append(
            f"<section><h2>{cls} <small>{totals[cls]} szt. (pokazano {len(by_class[cls])})</small></h2>"
            f"<div class='row'>{thumbs}</div></section>"
        )
    html = f"""<!DOCTYPE html><html lang="pl"><head><meta charset="UTF-8">
<title>Wycinki per klasa</title><style>
body{{font-family:Segoe UI,Arial,sans-serif;background:#1e1e1e;color:#eee;margin:0;padding:14px}}
section{{margin:16px 0;border-top:1px solid #444;padding-top:8px}} small{{color:#aaa}}
.row{{display:flex;flex-wrap:wrap;gap:6px}}
.row img{{height:64px;background:#fff;border:1px solid #555;border-radius:3px;object-fit:contain}}
</style></head><body>
<h1>Wycinki bboxow per klasa</h1>
<p style="color:#999">Każdy obrazek = wnętrze jednego bboxa treningowego. Szukaj klas, gdzie wycinki są niespójne (różne kształty) — to szum etykiet.</p>
{''.join(sections)}</body></html>"""
    (args.out / "index.html").write_text(html, encoding="utf-8")
    print(f"Klas: {len(by_class)} | wycinkow zapisano: {sum(len(v) for v in by_class.values())}")
    print(f"Galeria: {args.out / 'index.html'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
