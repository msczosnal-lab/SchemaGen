"""Pokrycie klas: na ilu stronach wystepuja i ile ich jest w val (READ-ONLY).

Prompt 028. Liczba instancji sama w sobie klamie. Klasa z 36 bboxami z JEDNEJ
strony to jeden kontekst wizualny powielony 36 razy — model uczy sie strony,
nie symbolu. A klasa z zerem instancji w val ma mAP nieoznaczalne: YOLO poda
0 albo NaN niezaleznie od tego, jak dobrze model dziala.

To drugie jest krytyczne dla miary sukcesu augmentacji (028 Czesc C §5.3):
"mAP per klasa przed i po" nie da sie policzyc dla klasy, ktorej w val nie ma.

Uzycie:
    python scripts/class_coverage.py
    python scripts/class_coverage.py --min-count 5
    python scripts/class_coverage.py --only-problems
"""

from __future__ import annotations

import argparse
import sys
from collections import Counter, defaultdict
from pathlib import Path

# Uruchomienie: python scripts/class_coverage.py (bez wymogu pip install -e .)
_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from backend.class_map import bbox_class, build_class_map, load_palette_map
from train.dataset_export import load_all_training_records, load_val_page_ids

#: Ponizej tego progu udzialu jednej strony klasa jest "jednostronna".
SINGLE_PAGE_WARN = 1


def collect(recs, class_map, pmap) -> dict[str, Counter]:
    """klasa -> Counter(page_id -> liczba instancji)."""
    pages: dict[str, Counter] = defaultdict(Counter)
    for rec in recs:
        for b in rec.bboxes:
            cls = bbox_class(b.class_name, b.tag, pmap)
            if cls and cls in class_map:
                pages[cls][rec.page_id] += 1
    return pages


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--min-count", type=int, default=5)
    ap.add_argument("--only-problems", action="store_true",
                    help="pokaz wylacznie klasy jednostronne lub bez instancji w val")
    args = ap.parse_args()

    recs = load_all_training_records()
    if not recs:
        print("[BŁĄD] Brak danych GT (gt/*.json + SQLite).")
        return 1

    pmap = load_palette_map()
    class_map, _dist = build_class_map(recs, min_count=args.min_count, bucket_rare=False)
    val = set(load_val_page_ids())
    pages = collect(recs, class_map, pmap)

    gt_pages = {r.page_id for r in recs}
    val_missing_gt = sorted(p for p in val if p not in gt_pages)

    print(f"Klas (min-count={args.min_count}): {len(class_map)} | "
          f"stron val: {len(val)} | stron GT: {len(gt_pages)}")
    if val_missing_gt:
        print(f"[BŁĄD] {len(val_missing_gt)} stron z val-pages.yaml nie ma GT: "
              + ", ".join(p[-5:] for p in val_missing_gt))

    rows = []
    for cls in class_map:
        pg = pages[cls]
        total = sum(pg.values())
        n_pages = len(pg)
        top_share = 100 * max(pg.values()) / total if total else 0
        n_val = sum(v for p, v in pg.items() if p in val)
        rows.append((n_pages, cls, total, top_share, n_val))

    single = [r for r in rows if r[0] <= SINGLE_PAGE_WARN]
    no_val = [r for r in rows if r[4] == 0]
    only_val = [r for r in rows if r[4] == r[2] and r[2] > 0]

    shown = sorted(single + no_val + only_val) if args.only_problems else sorted(rows)
    seen = set()
    print(f"\n{'klasa':<32}{'inst':>6}{'stron':>7}{'max/1str':>10}{'val':>6}  uwagi")
    print("-" * 80)
    for n_pages, cls, total, top_share, n_val in shown:
        if cls in seen:
            continue
        seen.add(cls)
        notes = []
        if n_pages <= SINGLE_PAGE_WARN:
            notes.append("JEDNA STRONA")
        if n_val == 0:
            notes.append("brak w val -> mAP nieoznaczalne")
        elif n_val == total:
            notes.append("tylko w val -> 0 w train")
        print(f"{cls:<32}{total:>6}{n_pages:>7}{top_share:>9.0f}%{n_val:>6}  "
              + "; ".join(notes))

    print(f"\n[BŁĄD] {len(no_val)}/{len(class_map)} klas ma ZERO instancji w val — "
          "ich mAP nie da sie zmierzyc:")
    print("  " + ", ".join(sorted(r[1] for r in no_val)))
    if single:
        print(f"\n[RYZYKO] {len(single)} klas wystepuje na JEDNEJ stronie "
              "(jeden kontekst wizualny, brak dowodu na generalizacje):")
        for _n, cls, total, _s, _v in sorted(single):
            page = pages[cls].most_common(1)[0][0]
            print(f"  {cls:<30} {total:>4} inst. — wszystkie z {page[-5:]}")
    if only_val:
        print(f"\n[BŁĄD] {len(only_val)} klas istnieje WYLACZNIE w val "
              "(zero danych treningowych):")
        print("  " + ", ".join(sorted(r[1] for r in only_val)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
