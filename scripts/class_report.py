"""Raport klas YOLO z bazy (READ-ONLY). Pokazuje jak `tag` mapuje sie na klasy.

Uruchom przed treningiem, by zobaczyc WSZYSTKIE klasy i ich licznosci.

Uzycie:
    python scripts/class_report.py
    python scripts/class_report.py --min-count 5
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Uruchomienie: python scripts/class_report.py (bez wymogu pip install -e .)
_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from backend.class_map import (
    build_class_map,
    class_distribution,
    load_palette_map,
    load_yolo_exclude_classes,
)
from backend.paths import ROOT
from train.dataset_export import load_all_training_records


def _load_records():
    return load_all_training_records()


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--min-count", type=int, default=1,
                    help="klasy ponizej progu -> 'inny' (domyslnie 1 = wszystkie)")
    args = ap.parse_args()

    recs = _load_records()
    if not recs:
        print(f"[BŁĄD] Brak danych GT (gt/*.json + SQLite). ROOT={ROOT}")
        return 1

    pmap = load_palette_map()
    dist_all = class_distribution(recs, pmap)
    dist = class_distribution(recs, pmap, yolo_only=True)
    exclude = load_yolo_exclude_classes()
    class_map, _ = build_class_map(recs, min_count=args.min_count, bucket_rare=False)

    total_bbox = sum(len(r.bboxes) for r in recs)
    tagged = sum(dist_all.values())
    contextual_n = sum(dist_all[c] for c in exclude if c in dist_all)
    print(f"Stron: {len(recs)} | bbox: {total_bbox} | otagowanych: {tagged} "
          f"| bez tagu (pominiete): {total_bbox - tagged}")
    if exclude:
        print(f"Kontekstowe (bez YOLO, GT relacji): {contextual_n} bbox w klasach: "
              f"{', '.join(sorted(exclude))}")
    print(f"Klas YOLO (po min-count={args.min_count}): {len(class_map)}\n")
    print(f"{'id':>3}  {'klasa':<32} {'instancji':>9}")
    print("-" * 48)
    for name, idx in sorted(class_map.items(), key=lambda kv: kv[1]):
        print(f"{idx:>3}  {name:<32} {dist.get(name, 0):>9}")

    excluded = sorted((c, n) for c, n in dist.items() if c not in class_map)
    if excluded:
        lost = sum(n for _, n in excluded)
        print(f"\n[INFO] WYKLUCZONE (<{args.min_count} instancji): {len(excluded)} klas, "
              f"{lost} bbox nie trafi do treningu:")
        print("  " + ", ".join(f"{c}({n})" for c, n in excluded[:30])
              + ("..." if len(excluded) > 30 else ""))
    print(f"\n[INFO] Klas do treningu: {len(class_map)} | "
          f"instancji w treningu: {sum(dist.get(n, 0) for n in class_map)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
