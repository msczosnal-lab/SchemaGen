"""reviewed.json (z element_review.py) -> config/reviewed-classes.yaml.

Klasy oznaczone "przejrzana" w przegladarce = zatwierdzone do treningu.
Wczesniej ta informacja zyla wylacznie w localStorage przegladarki i nie
widzial jej ani eksport datasetu, ani trening — ginela przy czyszczeniu
danych przegladarki.

Konwencja jak apply_reassign/apply_symmetry: DRY-RUN domyslnie, zapis atomowy,
scalanie zamiast nadpisywania (przeglad jednej partii klas nie kasuje reszty).

[UWAGA] Bramka jest AKTYWNA dopiero, gdy lista jest niepusta. Pusty plik nie
wyzeruje datasetu — to swiadoma asymetria wzgledem symbol-symmetry.yaml, gdzie
brak wpisu oznacza zakaz. Tam bledny domysl psuje etykiety, tu wywrocilby
caly trening bez czytelnej przyczyny.

Uzycie:
    python scripts/apply_reviewed.py                 # dry-run
    python scripts/apply_reviewed.py --apply
    python scripts/apply_reviewed.py --replace --apply
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

try:
    from scripts._pick_input import pick_input
except ModuleNotFoundError:
    from _pick_input import pick_input

import yaml

from backend.class_map import (
    class_distribution,
    load_palette_map,
    load_reviewed_classes,
    load_yolo_exclude_classes,
)
from backend.paths import ROOT

OUT = ROOT / "config" / "reviewed-classes.yaml"

HEADER = """# Klasy zatwierdzone wzrokowo w scripts/element_review.py ("przejrzana").
# Tylko one trafiaja do treningu YOLO (build_class_map / is_yolo_exportable).
#
# Pusta lista lub brak pliku = BRAMKA NIEAKTYWNA (trenuja sie wszystkie klasy).
# Celowo NIE jest to fail-safe w strone zakazu — pusty plik wyzerowalby dataset.
#
# Generowane przez scripts/apply_reviewed.py z reviewed.json.
"""


def write_atomic(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(text, encoding="utf-8")
    os.replace(tmp, path)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--file", type=Path, default=None)
    ap.add_argument("--out", type=Path, default=OUT)
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--replace", action="store_true",
                    help="zastap liste (domyslnie: scal z obecna)")
    args = ap.parse_args()

    candidates = [args.file] if args.file else [
        ROOT / "data" / "reviewed.json",
        ROOT / "data" / "output" / "reviewed.json",
        Path.home() / "Downloads" / "reviewed.json",
        Path.cwd() / "reviewed.json",
    ]
    path = pick_input(candidates, "reviewed.json")
    if path is None:
        return 1

    data = json.loads(path.read_text(encoding="utf-8"))
    incoming = set(data.get("reviewed") or []) if isinstance(data, dict) else set(data)
    if not incoming:
        print("[UWAGA] reviewed.json nie zawiera zadnej zatwierdzonej klasy — "
              "bramka pozostanie nieaktywna.")

    current = set(load_reviewed_classes())
    merged = incoming if args.replace else (current | incoming)

    from train.dataset_export import load_all_training_records

    recs = load_all_training_records()
    dist = class_distribution(recs, load_palette_map(), yolo_only=True)
    trainable = {c for c, n in dist.items() if n >= 5}

    added = sorted(merged - current)
    removed = sorted(current - merged) if args.replace else []
    blocked = sorted(c for c in trainable if merged and c not in merged)
    unknown = sorted(c for c in merged if c not in dist)

    print(f"\nZatwierdzonych klas: {len(merged)} (bylo {len(current)})")
    if added:
        print(f"  + {len(added)}: {', '.join(added)}")
    if removed:
        print(f"  - {len(removed)}: {', '.join(removed)}")
    if unknown:
        print(f"[UWAGA] {len(unknown)} klas nie wystepuje w danych: {', '.join(unknown)}")

    if not merged:
        print("\nBramka NIEAKTYWNA — do treningu ida wszystkie klasy.")
    else:
        n_ok = sum(dist[c] for c in merged if c in dist)
        n_blk = sum(dist[c] for c in blocked)
        print(f"\nBramka AKTYWNA: do treningu {len(trainable) - len(blocked)} klas "
              f"({n_ok} instancji)")
        if blocked:
            print(f"[UWAGA] {len(blocked)} klas >=5 instancji NIE przejdzie do treningu "
                  f"({n_blk} instancji) — brak oznaczenia 'przejrzana':")
            print("  " + ", ".join(blocked))

    if not args.apply:
        print(f"\nDRY-RUN — nic nie zapisano. Dodaj --apply, aby zapisac do {args.out}.")
        return 0

    body = yaml.safe_dump({"reviewed": sorted(merged)}, allow_unicode=True,
                          sort_keys=False, default_flow_style=False)
    write_atomic(args.out, HEADER + body)
    print(f"\nZAPISANO -> {args.out}")
    print("Sprawdz: python scripts/class_report.py --min-count 5")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
