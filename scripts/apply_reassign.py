"""Zastosuj zmiany klas z reassignments.json do bazy (pole `tag` bboxow).

reassignments.json (z relabel_tool): [{page_id, bbox_id, old, new_tag}, ...]
Ustawia tag bboxa na `new_tag` -> przy nastepnym eksporcie zmienia sie klasa YOLO.

Uzycie:
    python scripts/apply_reassign.py                 # dry-run (nic nie zapisuje)
    python scripts/apply_reassign.py --apply
    python scripts/apply_reassign.py --file data/reassignments.json --apply
"""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path

from backend.db import load_annotation, save_annotation
from backend.models.label import LabelRecord
from backend.paths import ROOT


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--file", type=Path, default=None)
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    candidates = [args.file] if args.file else [
        ROOT / "data" / "reassignments.json",
        ROOT / "data" / "output" / "reassignments.json",
        ROOT / "data" / "output" / "relabel" / "reassignments.json",
        ROOT / "Downloads" / "reassignments.json",
    ]
    path = next((c for c in candidates if c and c.exists()), None)
    if path is None:
        print("[BŁĄD] Nie znaleziono reassignments.json. Sprawdzone:")
        for c in candidates:
            print(f"  - {c}")
        print("Wskaz: --file <sciezka>")
        return 1
    print(f"Plik zmian: {path}")
    args.file = path
    changes = json.loads(args.file.read_text(encoding="utf-8"))
    if not isinstance(changes, list) or not changes:
        print("Pusta lista zmian.")
        return 1

    by_page: dict[str, dict[str, str]] = defaultdict(dict)
    for c in changes:
        by_page[c["page_id"]][c["bbox_id"]] = c["new_tag"]

    total = 0
    missing = 0
    for page_id, mapping in by_page.items():
        data = load_annotation(page_id)
        if not data:
            print(f"[RYZYKO] brak adnotacji: {page_id}")
            continue
        rec = LabelRecord.model_validate(data)
        applied = 0
        for b in rec.bboxes:
            if b.id in mapping:
                b.tag = mapping[b.id]
                applied += 1
        not_found = len(mapping) - applied
        missing += not_found
        total += applied
        flag = f" ({not_found} bbox_id nieznalezionych)" if not_found else ""
        print(f"{page_id}: {applied} zmian{flag}")
        if args.apply and applied:
            save_annotation(page_id, rec.model_dump())

    print(f"\n{'ZAPISANO' if args.apply else 'DRY-RUN'}: {total} zmian, "
          f"{missing} nieznalezionych bbox_id.")
    if not args.apply:
        print("Dodaj --apply aby zapisac. Potem: python -m train.dataset_export --min-count 5")
    else:
        print("Teraz: python -m train.dataset_export --min-count 5  (re-eksport datasetu)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
