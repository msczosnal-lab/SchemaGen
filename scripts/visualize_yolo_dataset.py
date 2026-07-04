"""Podglad WYEKSPORTOWANEGO datasetu YOLO — dokladnie to, na czym uczy sie model.

Rysuje etykiety z data/labeled/labels/*.txt (znormalizowane cx cy w h) na obrazach
z data/labeled/images/*, DENORMALIZUJAC po RZECZYWISTYM rozmiarze PNG. Jesli pudelka
nie siedza na symbolach -> etykiety treningowe sa zle (np. zla normalizacja).

Uzycie:
    python scripts/visualize_yolo_dataset.py
    python scripts/visualize_yolo_dataset.py --split train --limit 20
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

import cv2
import yaml

from backend.paths import LABELED

OUT_DIR = Path(__file__).resolve().parents[1] / "data" / "output" / "yolo_dataset_check"
PALETTE = [(46, 204, 113), (231, 76, 60), (52, 152, 219), (241, 196, 15),
           (155, 89, 182), (26, 188, 156), (230, 126, 34), (149, 165, 166)]


def _names() -> dict[int, str]:
    yml = LABELED / "data.yaml"
    if not yml.exists():
        return {}
    data = yaml.safe_load(yml.read_text(encoding="utf-8")) or {}
    names = data.get("names", {})
    if isinstance(names, dict):
        return {int(k): str(v) for k, v in names.items()}
    return {i: str(v) for i, v in enumerate(names)}


def _esc(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--split", choices=["train", "val", "both"], default="both")
    ap.add_argument("--limit", type=int, default=40)
    ap.add_argument("--out", type=Path, default=OUT_DIR)
    args = ap.parse_args()

    names = _names()
    if not names:
        print(f"[BŁĄD] Brak {LABELED/'data.yaml'}. Najpierw: python -m train.dataset_export")
        return 1
    print(f"Klasy z data.yaml: {len(names)}")

    splits = ["train", "val"] if args.split == "both" else [args.split]
    args.out.mkdir(parents=True, exist_ok=True)
    for old in args.out.glob("*.png"):
        old.unlink()

    per_class: Counter = Counter()
    out_of_range = 0
    pages = []
    shown = 0
    for split in splits:
        img_dir = LABELED / "images" / split
        lbl_dir = LABELED / "labels" / split
        if not img_dir.exists():
            continue
        for img_path in sorted(img_dir.glob("*")):
            if img_path.suffix.lower() not in (".png", ".jpg", ".jpeg"):
                continue
            img = cv2.imread(str(img_path))
            if img is None:
                continue
            H, W = img.shape[:2]
            lbl = lbl_dir / f"{img_path.stem}.txt"
            boxes = []
            if lbl.exists():
                for line in lbl.read_text(encoding="utf-8").splitlines():
                    parts = line.split()
                    if len(parts) != 5:
                        continue
                    cid = int(float(parts[0]))
                    cx, cy, bw, bh = map(float, parts[1:])
                    if not all(0.0 <= v <= 1.0 for v in (cx, cy, bw, bh)):
                        out_of_range += 1
                    per_class[names.get(cid, str(cid))] += 1
                    boxes.append((cid, cx, cy, bw, bh))
            if shown < args.limit:
                for cid, cx, cy, bw, bh in boxes:
                    x1 = int((cx - bw / 2) * W); y1 = int((cy - bh / 2) * H)
                    x2 = int((cx + bw / 2) * W); y2 = int((cy + bh / 2) * H)
                    col = PALETTE[cid % len(PALETTE)]
                    cv2.rectangle(img, (x1, y1), (x2, y2), col, 2)
                    cv2.putText(img, names.get(cid, str(cid)), (x1, max(y1 - 4, 12)),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.5, col, 1, cv2.LINE_AA)
                out_name = f"{split}_{img_path.stem}.png"
                cv2.imwrite(str(args.out / out_name), img)
                pages.append({"name": f"{split}/{img_path.stem}", "img": out_name,
                              "wh": f"{W}x{H}", "n": len(boxes)})
                shown += 1

    sections = "".join(
        f"<section><h2>{_esc(p['name'])} <small>{p['wh']} · {p['n']} bbox</small></h2>"
        f"<div class='imgwrap'><img src='{p['img']}' loading='lazy'></div></section>"
        for p in pages
    )
    summary = "".join(f"<tr><td>{_esc(k)}</td><td>{v}</td></tr>" for k, v in per_class.most_common())
    total = sum(per_class.values())
    warn = (f"<p style='color:#e74c3c'>⚠ {out_of_range} etykiet ma wspolrzedne poza [0,1] "
            f"— normalizacja zepsuta!</p>" if out_of_range else
            "<p style='color:#2ecc71'>Wszystkie wspolrzedne w [0,1] ✓</p>")
    html = f"""<!DOCTYPE html><html lang="pl"><head><meta charset="UTF-8">
<title>YOLO dataset check</title><style>
body{{font-family:Segoe UI,Arial,sans-serif;background:#1e1e1e;color:#eee;margin:0;padding:14px}}
section{{margin:18px 0;border-top:1px solid #444;padding-top:8px}} small{{color:#aaa}}
.imgwrap{{overflow:auto;background:#111;border:1px solid #333;max-height:85vh}}
img{{max-width:100%;height:auto;display:block}}
table{{border-collapse:collapse;font-size:.9rem}} td{{border-bottom:1px solid #333;padding:3px 12px}}
</style></head><body>
<h1>Dataset YOLO — {total} bbox, {len(names)} klas</h1>{warn}
<table><tr><th>klasa</th><th>bbox</th></tr>{summary}</table>
{sections}</body></html>"""
    (args.out / "index.html").write_text(html, encoding="utf-8")
    print(f"\nEtykiet razem: {total} | poza [0,1]: {out_of_range}")
    print(f"Galeria: {args.out / 'index.html'}")
    if out_of_range:
        print("[BŁĄD] Sa wspolrzedne poza zakresem -> normalizacja etykiet zepsuta.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
