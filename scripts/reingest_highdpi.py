"""Ponowny raster PDF przy wyzszym DPI + skalowanie adnotacji w SQLite.

Uzycie:
    python scripts/reingest_highdpi.py --dry-run
    python scripts/reingest_highdpi.py --apply
    python scripts/reingest_highdpi.py --apply --pdf sync/sources/22_A_153_PL_Adamed_AGV_SA2_20250706.pdf
"""

from __future__ import annotations

import argparse
import json
import sqlite3
from pathlib import Path

from backend.db import save_annotation
from backend.ingest import pdf_to_png
from backend.models.label import LabelRecord
from backend.paths import RAW, ROOT
from backend.runtime_config import legacy_pdf_dpi, pdf_dpi

SOURCES = ROOT / "sync" / "sources"
DEFAULT_PDFS = [
    RAW / "SchematWRT01.pdf",
    SOURCES / "25_A_229_PL5_19012026.pdf",
    SOURCES / "22_A_153_PL_Adamed_AGV_SA2_20250706.pdf",
]


def _scale_factor() -> float:
    old = legacy_pdf_dpi()
    new = pdf_dpi()
    if old <= 0:
        raise ValueError("legacy_pdf_dpi musi byc > 0")
    return new / old


def scale_annotations(apply: bool) -> int:
    factor = _scale_factor()
    if abs(factor - 1.0) < 1e-6:
        print("Skala 1.0 — pomijam migracje adnotacji.")
        return 0

    db = ROOT / "data" / "schemagen.db"
    conn = sqlite3.connect(db)
    rows = conn.execute("SELECT page_id, payload_json FROM annotations").fetchall()
    updated = 0
    for page_id, payload_json in rows:
        data = json.loads(payload_json)
        record = LabelRecord.model_validate(data)
        if not record.bboxes:
            continue
        if record.image_width and record.image_width > 3000:
            # heurystyka: juz w wysokim DPI (np. >3000 px szerokosci)
            continue
        for b in record.bboxes:
            b.x = round(b.x * factor, 2)
            b.y = round(b.y * factor, 2)
            b.width = round(b.width * factor, 2)
            b.height = round(b.height * factor, 2)
        if record.image_width:
            record.image_width = int(record.image_width * factor)
        if record.image_height:
            record.image_height = int(record.image_height * factor)
        updated += 1
        if apply:
            save_annotation(page_id, record.model_dump())
    conn.close()
    print(f"Adnotacje do skalowania x{factor:.2f}: {updated}")
    return updated


def rasterize_pdfs(pdfs: list[Path], apply: bool) -> int:
    dpi = pdf_dpi()
    total = 0
    for pdf in pdfs:
        if not pdf.exists():
            print(f"POMIN: brak {pdf}")
            continue
        print(f"{'[dry] ' if not apply else ''}Raster {pdf.name} @ {dpi} DPI …")
        if apply:
            pages = pdf_to_png(pdf, output_dir=RAW, dpi=dpi)
            total += len(pages)
            print(f"  -> {len(pages)} PNG")
        else:
            import fitz

            doc = fitz.open(pdf)
            n = len(doc)
            doc.close()
            total += n
            print(f"  -> {n} stron (bez zapisu)")
    return total


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--pdf", action="append", default=None, help="Konkretny PDF (mozna wielokrotnie)")
    parser.add_argument("--skip-annotations", action="store_true")
    args = parser.parse_args()

    pdfs = [Path(p) for p in args.pdf] if args.pdf else DEFAULT_PDFS
    print(f"DPI: {pdf_dpi()} (legacy {legacy_pdf_dpi()}), skala adnotacji x{_scale_factor():.2f}")

    n_pages = rasterize_pdfs(pdfs, apply=args.apply)
    if not args.skip_annotations:
        scale_annotations(apply=args.apply)

    if not args.apply:
        print(f"\nDry-run: {n_pages} stron do przerasterowania. Dodaj --apply.")
    else:
        print(f"\nGotowe: {n_pages} PNG @ {pdf_dpi()} DPI.")
        print("Nastepnie: python -m train.dataset_export && python -m train.train_symbols --name symbols_v3")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
