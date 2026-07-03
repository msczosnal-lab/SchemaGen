"""Weryfikacja eksportu YOLO dla wskazanych stron (diagnostyka rozjazdu wymiarow).

Sprawdza:
  - czy record.image_width/height == faktyczny rozmiar PNG w data/raw,
  - czy bboxy miesza sie w obrazie (max x+w, y+h <= wymiar) — inaczej zly SCALE,
  - liczbe bboxow GT vs linii w wyeksportowanym labelu (data/labeled/labels/...),
  - de-normalizacje kilku boxow z labelu na FAKTYCZNY PNG vs GT (piksele).

    python scripts/check_export.py --pages p035,p036,p037
    python scripts/check_export.py --pages 22_A_153_..._p035     # pelne id tez OK
"""
from __future__ import annotations

import argparse

from PIL import Image

from collections import Counter

from backend.db import list_pages, load_annotation
from backend.models.label import LabelRecord
from backend.paths import LABELED, RAW
from backend.class_map import (
    load_class_map,
    load_yolo_exclude_classes,
    tag_to_class,
)
from labeler.export import find_raw_image, yolo_label_lines
from train.dataset_export import load_labeled_records


def _match_page(frag: str, all_ids: list[str]) -> str | None:
    frag = frag.strip()
    if frag in all_ids:
        return frag
    hits = [p for p in all_ids if p.endswith(frag) or frag in p]
    return hits[0] if len(hits) == 1 else (hits[0] if hits else None)


def _label_path(page_id: str):
    for split in ("train", "val"):
        p = LABELED / "labels" / split / f"{page_id}.txt"
        if p.exists():
            return p, split
    return None, None


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--pages", required=True, help="lista fragmentow id po przecinku")
    args = ap.parse_args()

    all_ids = [p["id"] for p in list_pages()]
    recs = {r.page_id: r for r in load_labeled_records()}

    for frag in args.pages.split(","):
        pid = _match_page(frag, all_ids)
        print("\n" + "=" * 60)
        if pid is None:
            print(f"[BLAD] nie znaleziono strony dla '{frag}'")
            continue
        print(f"STRONA: {pid}")
        rec = recs.get(pid) or (LabelRecord.model_validate(load_annotation(pid)) if load_annotation(pid) else None)
        if rec is None:
            print("  [BLAD] brak adnotacji w bazie")
            continue

        # wymiary
        src = find_raw_image(rec, RAW)
        png_sz = Image.open(src).size if src else None
        print(f"  record.image: {rec.image_width} x {rec.image_height}")
        print(f"  PNG faktyczny: {png_sz}  ({src.name if src else 'BRAK PNG'})")
        if png_sz and (rec.image_width, rec.image_height) != png_sz:
            fx = png_sz[0] / (rec.image_width or 1)
            fy = png_sz[1] / (rec.image_height or 1)
            print(f"  [BLAD] ROZJAZD WYMIAROW! PNG/record = {fx:.3f} x {fy:.3f} "
                  f"-> boxy YOLO przesuniete/przeskalowane o ten czynnik")

        # sanity boxow wzgledem zapisanych wymiarow
        W = rec.image_width or 1
        H = rec.image_height or 1
        over = [b.id for b in rec.bboxes if (b.x + b.width) > W * 1.02 or (b.y + b.height) > H * 1.02]
        if over:
            print(f"  [BLAD] {len(over)} bboxow WYCHODZI poza record.image "
                  f"(zly scale?) np. {over[:3]}")

        # rozbicie tagow: dlaczego bboxy nie trafiaja do YOLO
        cmap = load_class_map()
        excl = load_yolo_exclude_classes()
        stat = Counter()
        examples = {}
        for b in rec.bboxes:
            tag = (b.tag or "").strip()
            cls = tag_to_class(tag)
            if not tag:
                key = "PUSTY TAG -> pomijany"
            elif cls is None:
                key = f"tag '{tag}' -> brak klasy"
            elif cls in excl:
                key = f"{cls} -> KONTEKSTOWA (poza YOLO)"
            elif cls in cmap:
                key = f"{cls} -> YOLO ok"
            else:
                key = f"{cls} -> BRAK w class_map (pomijany!)"
            stat[key] += 1
            examples.setdefault(key, tag)
        print(f"  class_map ma {len(cmap)} klas. Rozbicie {len(rec.bboxes)} bboxow:")
        for k, n in stat.most_common():
            print(f"    {n:4d}  {k}")

        # GT vs eksport (pokrycie: kazdy box eksportu -> najblizszy GT)
        lp, split = _label_path(pid)
        exp = lp.read_text(encoding="utf-8").strip().splitlines() if lp else []
        print(f"  bboxy GT: {len(rec.bboxes)} | plik eksportu [{split}]: {len(exp)}")
        if not png_sz or not exp:
            continue
        pw, ph = png_sz
        gt_centers = [(b.x + b.width / 2, b.y + b.height / 2) for b in rec.bboxes]
        worst = 0.0
        far = 0
        for ln in exp:
            _c, cx, cy, bw, bh = ln.split()
            ex = float(cx) * pw
            ey = float(cy) * ph
            d = min((((ex - gx) ** 2 + (ey - gy) ** 2) ** 0.5) for gx, gy in gt_centers) if gt_centers else 9e9
            worst = max(worst, d)
            if d > 30:
                far += 1
        avg_side = sum(b.width + b.height for b in rec.bboxes) / (2 * max(1, len(rec.bboxes)))
        print(f"  pokrycie: {len(exp)-far}/{len(exp)} boxow trafia w GT (<30px), "
              f"max odleglosc={worst:.0f}px (sredni bok obiektu ~{avg_side:.0f}px)")
        if far == 0:
            print("  [OK] eksport pokrywa sie z GT — boxy na miejscu.")
        else:
            print(f"  [BLAD] {far} boxow eksportu daleko od GT -> realne przesuniecie/skala")


if __name__ == "__main__":
    main()
