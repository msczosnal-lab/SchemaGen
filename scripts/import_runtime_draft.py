"""Import draft GT z runtime (recognize_file) do SQLite labelera.

Nie nadpisuje istniejących adnotacji bez --force.

Uzycie:
    python scripts/import_runtime_draft.py --page 22_A_153_PL_Adamed_AGV_SA2_20250706_p040
    python scripts/import_runtime_draft.py --pages "data/raw/*p04*.png" --force
"""

from __future__ import annotations

import argparse
import glob
from pathlib import Path

from backend.db import load_annotation, save_annotation, upsert_page
from backend.paths import RAW, ensure_data_dirs
from backend.recognize.pipeline import recognize_file
from labeler.runtime_draft import schema_to_label_record


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--page", help="page_id (stem PNG w data/raw)")
    ap.add_argument("--pages", nargs="*", help="glob(y) sciezek PNG")
    ap.add_argument("--force", action="store_true", help="nadpisz istniejace adnotacje")
    args = ap.parse_args()

    ensure_data_dirs()
    pages: list[Path] = []
    if args.page:
        for ext in (".png", ".jpg", ".jpeg"):
            p = RAW / f"{args.page}{ext}"
            if p.exists():
                pages.append(p)
                break
        if not pages:
            print(f"[BLAD] Brak obrazu: {args.page}")
            return 1
    elif args.pages:
        for pat in args.pages:
            pages.extend(Path(x) for x in glob.glob(pat))
        pages = sorted(set(pages))
    else:
        print("Podaj --page lub --pages")
        return 1

    ok = 0
    skip = 0
    for path in pages:
        page_id = path.stem
        existing = load_annotation(page_id)
        if existing and existing.get("bboxes") and not args.force:
            print(f"{page_id}: pomijam (ma bboxy; --force aby nadpisac)")
            skip += 1
            continue
        print(f"{page_id}: recognize_file…")
        schema = recognize_file(str(path))
        record = schema_to_label_record(page_id, schema)
        save_annotation(page_id, record.model_dump())
        upsert_page(page_id, f"{page_id}{path.suffix}", status="draft")
        print(
            f"  -> {len(record.bboxes)} bbox, {len(record.lines)} linii, "
            f"{len(record.connections)} conn, "
            f"{sum(len(b.terminals) for b in record.bboxes)} terminali"
        )
        ok += 1

    print(f"\nZapisano draft: {ok}, pominięto: {skip}")
    return 0 if ok or skip else 1


if __name__ == "__main__":
    raise SystemExit(main())
