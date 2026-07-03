"""Usuwa oznaczone bboxy z bazy wg listy z scripts/element_review.py.

Lista: JSON ["<page_id>|<bbox_id>", ...] (plik z przegladarki, domyslnie
data/output/delete_list.json lub sciezka do pobranego pliku).

    python scripts/apply_delete.py --file delete_list.json          # DRY-RUN (podglad)
    python scripts/apply_delete.py --file delete_list.json --apply  # usun (z backupem)

Przed --apply robi kopie bazy: data/schemagen.db.bak-<timestamp>.
"""
from __future__ import annotations

import argparse
import json
import shutil
from collections import defaultdict
from datetime import datetime

from backend.db import load_annotation, save_annotation
from backend.paths import DATA


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--file", default="data/output/delete_list.json")
    ap.add_argument("--apply", action="store_true", help="faktyczne usuniecie")
    args = ap.parse_args()

    raw = json.loads(open(args.file, encoding="utf-8").read())
    by_page: dict[str, set] = defaultdict(set)
    for entry in raw:
        pid, _, bid = str(entry).partition("|")
        if pid and bid:
            by_page[pid].add(bid)
    total = sum(len(v) for v in by_page.values())
    print(f"Do usuniecia: {total} bboxow na {len(by_page)} stronach "
          f"({'APPLY' if args.apply else 'DRY-RUN'})")

    if args.apply:
        db = DATA / "schemagen.db"
        if db.exists():
            bak = DATA / f"schemagen.db.bak-{datetime.now():%Y%m%d_%H%M%S}"
            shutil.copy2(db, bak)
            print(f"Backup bazy -> {bak}")

    removed = 0
    for pid, ids in by_page.items():
        data = load_annotation(pid)
        if not data:
            print(f"  [POMIN] brak adnotacji: {pid}")
            continue
        before = len(data.get("bboxes", []))
        kept = [b for b in data.get("bboxes", []) if b.get("id") not in ids]
        got = before - len(kept)
        removed += got
        print(f"  {pid}: -{got} (z {before})")
        if args.apply:
            data["bboxes"] = kept
            save_annotation(pid, data)

    print(f"{'Usunieto' if args.apply else 'Do usuniecia'}: {removed} bboxow.")
    if not args.apply:
        print("To byl DRY-RUN. Dodaj --apply, aby zapisac.")


if __name__ == "__main__":
    main()
