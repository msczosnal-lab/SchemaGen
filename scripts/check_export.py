"""Weryfikacja eksportu YOLO dla wskazanych stron.

Sprawdza:
  - czy record.image_width/height == faktyczny rozmiar PNG (rozjazd skali),
  - POKRYCIE: kazdy box z pliku eksportu -> najblizszy GT (niezaleznie od kolejnosci);
    jesli wszystkie blisko GT -> eksport poprawny.

    python scripts/check_export.py --pages p035,p036,p037
"""
from __future__ import annotations

import argparse

from PIL import Image

from backend.db import list_pages, load_annotation
from backend.models.label import LabelRecord
from backend.paths import LABELED, RAW
from labeler.export import find_raw_image
from train.dataset_export import load_labeled_records


def _match_page(frag: str, all_ids: list[str]) -> str | None:
    frag = frag.strip()
    if frag in all_ids:
        return frag
    hits = [p for p in all_ids if p.endswith(frag) or frag in p]
    return hits[0] if hits else None


def _label_path(page_id: str):
    for split in ("train", "val"):
        p = LABELED / "labels" / split / f"{page_id}.txt"
        if p.exists():
            return p, split
    return None, None


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--pages", required=True, help="fragmenty id po przecinku")
    ap.add_argument("--tol", type=int, default=30, help="tolerancja pokrycia [px]")
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
        rec = recs.get(pid)
        if rec is None:
            data = load_annotation(pid)
            rec = LabelRecord.model_validate(data) if data else None
        if rec is None:
            print("  [BLAD] brak adnotacji w bazie")
            continue

        src = find_raw_image(rec, RAW)
        png_sz = Image.open(src).size if src else None
        print(f"  record.image: {rec.image_width} x {rec.image_height}")
        print(f"  PNG faktyczny: {png_sz}  ({src.name if src else 'BRAK PNG'})")
        if png_sz and (rec.image_width, rec.image_height) != png_sz:
            fx = png_sz[0] / (rec.image_width or 1)
            fy = png_sz[1] / (rec.image_height or 1)
            print(f"  [BLAD] ROZJAZD WYMIAROW! PNG/record = {fx:.3f} x {fy:.3f}")

        lp, split = _label_path(pid)
        exp = lp.read_text(encoding="utf-8").strip().splitlines() if lp else []
        print(f"  bboxy GT: {len(rec.bboxes)} | plik eksportu [{split}]: {len(exp)}")
        if not png_sz or not exp:
            print("  (brak PNG lub pusty plik eksportu)")
            continue

        pw, ph = png_sz
        gt_c = [(b.x + b.width / 2, b.y + b.height / 2) for b in rec.bboxes]
        worst = 0.0
        far = 0
        for ln in exp:
            _c, cx, cy, bw, bh = ln.split()
            ex, ey = float(cx) * pw, float(cy) * ph
            d = min(((ex - gx) ** 2 + (ey - gy) ** 2) ** 0.5 for gx, gy in gt_c) if gt_c else 9e9
            worst = max(worst, d)
            if d > args.tol:
                far += 1
        avg = sum(b.width + b.height for b in rec.bboxes) / (2 * max(1, len(rec.bboxes)))
        print(f"  pokrycie: {len(exp) - far}/{len(exp)} boxow trafia w GT (<{args.tol}px), "
              f"max={worst:.0f}px (sredni bok ~{avg:.0f}px)")
        print("  [OK] eksport pokrywa sie z GT." if far == 0
              else f"  [BLAD] {far} boxow daleko od GT -> realne przesuniecie/skala")


if __name__ == "__main__":
    main()
