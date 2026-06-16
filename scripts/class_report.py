"""Raport klas YOLO z bazy (READ-ONLY). Pokazuje jak `tag` mapuje sie na klasy.

Uruchom przed treningiem, by zobaczyc WSZYSTKIE klasy i ich licznosci.

Uzycie:
    python scripts/class_report.py
    python scripts/class_report.py --min-count 5
"""

from __future__ import annotations

import argparse
import json
import sqlite3

from backend.class_map import build_class_map, class_distribution, load_palette_map
from backend.models.label import LabelRecord
from backend.paths import DB_PATH


def _load_records() -> list[LabelRecord]:
    if not DB_PATH.exists():
        print(f"[BŁĄD] Brak bazy: {DB_PATH}")
        return []
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute("SELECT page_id, payload_json FROM annotations").fetchall()
    conn.close()
    recs = []
    for page_id, payload in rows:
        if page_id.startswith("test"):
            continue
        rec = LabelRecord.model_validate(json.loads(payload))
        if rec.bboxes:
            recs.append(rec)
    return recs


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--min-count", type=int, default=1,
                    help="klasy ponizej progu -> 'inny' (domyslnie 1 = wszystkie)")
    args = ap.parse_args()

    recs = _load_records()
    if not recs:
        return 1

    pmap = load_palette_map()
    dist = class_distribution(recs, pmap)
    class_map, _ = build_class_map(recs, min_count=args.min_count)

    total_bbox = sum(len(r.bboxes) for r in recs)
    tagged = sum(dist.values())
    print(f"Stron: {len(recs)} | bbox: {total_bbox} | otagowanych: {tagged} "
          f"| bez tagu (pominiete): {total_bbox - tagged}")
    print(f"Klas (po min-count={args.min_count}): {len(class_map)}\n")
    print(f"{'id':>3}  {'klasa':<32} {'instancji':>9}")
    print("-" * 48)
    for name, idx in sorted(class_map.items(), key=lambda kv: kv[1]):
        cnt = dist.get(name, 0)
        if name == "inny":
            cnt = sum(n for c, n in dist.items() if c not in class_map)
        print(f"{idx:>3}  {name:<32} {cnt:>9}")

    rare = [c for c, n in dist.items() if n < args.min_count]
    if rare:
        print(f"\n[RYZYKO] {len(rare)} klas < min-count -> 'inny': "
              f"{', '.join(sorted(rare)[:20])}{'...' if len(rare) > 20 else ''}")
    singles = [c for c, n in dist.items() if n == 1 and c in class_map]
    if singles:
        print(f"[RYZYKO] {len(singles)} klas ma tylko 1 instancje "
              f"(slabo sie naucza, nie trafia do val): {', '.join(sorted(singles)[:20])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
