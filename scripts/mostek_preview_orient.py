"""Podglad przypisania orientacji mostka na realnych cropach.

Renderuje siatke HTML: crop + przypisana klasa + score NCC, posortowane od
NAJGORSZEGO score (najpierw watpliwe). Do wzrokowej weryfikacji przed treningiem.

    python scripts/mostek_preview_orient.py            # wszystkie
    python scripts/mostek_preview_orient.py --limit 60 # tylko 60 najgorszych
Wynik: data/output/mostek_orient_preview.html
"""
from __future__ import annotations

import argparse

from backend.paths import RAW, ROOT
from train.dataset_export import load_labeled_records, _load_page_images
from train.mostek_orient import CLASS_NAMES, _as_gallery, classify_gallery
from scripts._thumb import thumb_b64
from train.mostek_tiles import (
    MOSTEK_TAG,
    crop_bbox,
    load_exemplars,
    load_mostek_config,
    count_edge_crossings,
)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0, help="ile pokazac (0=wszystko)")
    ap.add_argument("--thumb", type=int, default=96)
    ap.add_argument("--thicken", type=int, default=1)
    args = ap.parse_args()

    cfg = load_mostek_config()
    tpl = load_exemplars(ROOT / cfg.get("exemplar_dir", "data/mostek_exemplars"))
    if tpl is None:
        print("[BLAD] brak eksemplarzy w data/mostek_exemplars/")
        return
    gallery = _as_gallery(tpl)
    recs = load_labeled_records()
    imgs = _load_page_images(recs, RAW)

    items = []
    for rec in recs:
        page = imgs.get(rec.page_id)
        if page is None:
            continue
        for b in rec.bboxes:
            if b.tag.strip().lower() != MOSTEK_TAG:
                continue
            crop = crop_bbox(page, b.x, b.y, b.width, b.height)
            if crop.size == 0:
                continue
            idx, score = classify_gallery(crop, gallery)
            items.append((score, CLASS_NAMES[idx], count_edge_crossings(crop),
                          rec.page_id, crop))

    items.sort(key=lambda t: t[0])  # najgorsze najpierw
    if args.limit:
        items = items[: args.limit]

    cells = []
    for score, name, cr, pid, crop in items:
        color = "#c0392b" if score < 0.55 else "#27ae60"
        cells.append(
            f'<div style="display:inline-block;margin:4px;text-align:center;'
            f'font:11px monospace;border:1px solid #ddd;padding:3px">'
            f'<img src="data:image/png;base64,{thumb_b64(crop, args.thumb, args.thicken)}" '
            f'style="height:{args.thumb}px;image-rendering:pixelated;background:#fff"><br>'
            f'<b>{name[7:]}</b> <span style="color:{color}">{score:.2f}</span><br>'
            f'<span style="color:#888">stub={cr} {pid[-4:]}</span></div>'
        )

    out = ROOT / "data" / "output" / "mostek_orient_preview.html"
    out.parent.mkdir(parents=True, exist_ok=True)
    n_low = sum(1 for it in items if it[0] < 0.55)
    out.write_text(
        f"<html><body><h3>Mostek orientacja — {len(items)} cropow, "
        f"score&lt;0.55: {n_low}</h3>{''.join(cells)}</body></html>",
        encoding="utf-8",
    )
    print(f"OK -> {out}  ({len(items)} cropow, low-score={n_low})")


if __name__ == "__main__":
    main()
