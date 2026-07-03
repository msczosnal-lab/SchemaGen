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

from backend.db import list_pages, load_annotation
from backend.models.label import LabelRecord
from backend.paths import LABELED, RAW
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

        # GT vs eksport
        lines = yolo_label_lines(rec)
        lp, split = _label_path(pid)
        exp = lp.read_text(encoding="utf-8").strip().splitlines() if lp else []
        print(f"  bboxy GT: {len(rec.bboxes)} | linie yolo (re-gen): {len(lines)} | "
              f"plik eksportu [{split}]: {len(exp)}")
        if lp and len(exp) != len(lines):
            print(f"  [RYZYKO] plik eksportu != swiezo wygenerowane -> stary eksport, ponow dataset_export")

        # pierwsze 3 boxy: GT piksel vs denorm z labelu na FAKTYCZNY PNG
        if png_sz and exp:
            pw, ph = png_sz
            print("  kontrola 3 boxow (GT px vs label→PNG px):")
            for i, ln in enumerate(exp[:3]):
                c, cx, cy, bw, bh = ln.split()
                dx = (float(cx) - float(bw) / 2) * pw
                dy = (float(cy) - float(bh) / 2) * ph
                dw = float(bw) * pw
                dh = float(bh) * ph
                g = rec.bboxes[i] if i < len(rec.bboxes) else None
                gt = f"GT[{g.x:.0f},{g.y:.0f},{g.width:.0f},{g.height:.0f}]" if g else "GT[?]"
                print(f"    #{i} label->PNG[{dx:.0f},{dy:.0f},{dw:.0f},{dh:.0f}]  {gt}")


if __name__ == "__main__":
    main()
