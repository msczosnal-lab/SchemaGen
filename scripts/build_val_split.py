"""Stratyfikowany dobor stron val — kazda klasa ma reprezentacje w zbiorze walidacyjnym.

Problem (028, Czesc C §5.3): przy losowym doborze 8 z 19 klas mialo ZERO instancji
w val. Ich mAP jest wtedy nieoznaczalne (YOLO poda 0 albo NaN niezaleznie od jakosci
modelu), wiec zadnej zmiany w treningu nie da sie ocenic — a to jest warunek
wdrozenia augmentacji.

Algorytm: zachlanne pokrycie zbioru (set cover). W kazdym kroku bierzemy strone,
ktora domyka najwiecej jeszcze niepokrytych klas; remis rozstrzyga mniejsza liczba
bboxow (tansza strona = mniej danych zabranych treningowi). Potem ewentualne
dopelnienie do zadanego udzialu.

[RYZYKO] Klasy wystepujace na JEDNEJ stronie sa nierozwiazywalne: strona w val
oznacza zero w train, strona w train — zero w val. Skrypt ich nie wciaga do val
(trening jest wazniejszy) i raportuje je jawnie jako trwale niemierzalne.

Uzycie:
    python scripts/build_val_split.py                  # dry-run
    python scripts/build_val_split.py --frac 0.15
    python scripts/build_val_split.py --apply
"""

from __future__ import annotations

import argparse
import os
import sys
from collections import Counter, defaultdict
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import yaml

from backend.class_map import bbox_class, build_class_map, load_palette_map
from backend.paths import VAL_PAGES
from train.dataset_export import load_all_training_records


def page_class_map(recs, class_map, pmap) -> dict[str, Counter]:
    """page_id -> Counter(klasa -> liczba instancji), tylko klasy treningowe."""
    out: dict[str, Counter] = {}
    for rec in recs:
        c: Counter = Counter()
        for b in rec.bboxes:
            cls = bbox_class(b.class_name, b.tag, pmap)
            if cls and cls in class_map:
                c[cls] += 1
        if c:
            out[rec.page_id] = c
    return out


def greedy_cover(pages: dict[str, Counter], need: set[str]) -> list[str]:
    """Zachlannie wybierz strony pokrywajace `need`. Remis -> mniejsza strona."""
    chosen: list[str] = []
    uncovered = set(need)
    avail = dict(pages)
    while uncovered:
        best, best_gain, best_size = None, 0, None
        for pid, cnt in avail.items():
            gain = len(uncovered & set(cnt))
            if gain == 0:
                continue
            size = sum(cnt.values())
            if gain > best_gain or (gain == best_gain and size < (best_size or 1 << 30)):
                best, best_gain, best_size = pid, gain, size
        if best is None:
            break  # reszty nie da sie pokryc
        chosen.append(best)
        uncovered -= set(avail[best])
        del avail[best]
    return chosen


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--frac", type=float, default=0.12,
                    help="docelowy udzial stron val (domyslnie 0.12)")
    ap.add_argument("--min-count", type=int, default=5)
    ap.add_argument("--min-val", type=int, default=3,
                    help="minimum instancji kazdej klasy w val (domyslnie 3); "
                         "ponizej tego mAP per klasa jest szumem")
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--out", type=Path, default=VAL_PAGES)
    args = ap.parse_args()

    recs = load_all_training_records()
    pmap = load_palette_map()
    class_map, dist = build_class_map(recs, min_count=args.min_count, bucket_rare=False)
    if not class_map:
        print("[BŁĄD] Brak klas treningowych.")
        return 1

    pages = page_class_map(recs, class_map, pmap)
    by_class: dict[str, set[str]] = defaultdict(set)
    for pid, cnt in pages.items():
        for cls in cnt:
            by_class[cls].add(pid)

    single = sorted(c for c in class_map if len(by_class[c]) <= 1)
    coverable = set(class_map) - set(single)

    # Strony bedace JEDYNYM zrodlem jakiejs klasy zostaja w train — inaczej ta klasa
    # ma zero danych treningowych, co jest gorsze niz brak pomiaru. Wykluczamy je
    # JUZ NA WEJSCIU do pokrycia; usuwanie ich po fakcie rozbijalo gotowe pokrycie.
    sole_pages = {next(iter(by_class[c])) for c in single if by_class[c]}
    candidates = {p: c for p, c in pages.items() if p not in sole_pages}

    chosen = greedy_cover(candidates, coverable)

    # Dopelnienie: nie "najubozszymi stronami", tylko takimi, ktore najlepiej
    # domykaja NIEDOBOR per klasa. Samo pokrycie daje czesto 1-2 instancje na klase,
    # a przy takiej probie mAP jest szumem — jedno trafienie to kilkadziesiat punktow.
    want = {
        c: max(args.min_val, round(dist[c] * args.frac))
        for c in class_map if c not in single
    }
    target_pages = max(len(chosen), round(len(pages) * args.frac))
    avail = {p: c for p, c in pages.items() if p not in set(chosen) and p not in sole_pages}

    total = Counter()
    for cnt in pages.values():
        total.update(cnt)

    def deficit(sel: set[str]) -> dict[str, int]:
        have: Counter = Counter()
        for p in sel:
            have.update(pages[p])
        return {c: max(0, want[c] - have[c]) for c in want}

    def would_starve(sel: set[str], pid: str) -> bool:
        """Czy dolozenie strony zostawi jakas klase z zerem instancji w TRAIN?

        Klasa bez danych treningowych jest gorsza niz klasa bez pomiaru — model
        nie ma z czego sie jej nauczyc, wiec mierzenie jej traci sens.
        """
        have: Counter = Counter()
        for p in sel | {pid}:
            have.update(pages[p])
        return any(total[c] - have[c] <= 0 for c in pages[pid] if c not in single)

    sel = set(chosen)
    while avail and (len(sel) < target_pages or any(deficit(sel).values())):
        d = deficit(sel)
        if not any(d.values()) and len(sel) >= target_pages:
            break
        # ile realnego niedoboru domyka stronа, wazone: male klasy licza sie bardziej
        best, best_score = None, 0.0
        for pid, cnt in avail.items():
            if would_starve(sel, pid):
                continue
            score = sum(min(d[c], n) / max(1, want[c]) for c, n in cnt.items() if c in d)
            if score > best_score:
                best, best_score = pid, score
        if best is None:
            if len(sel) >= target_pages:
                break
            safe = [p for p in avail if not would_starve(sel, p)]
            if not safe:
                break
            best = min(safe, key=lambda p: sum(pages[p].values()))
        sel.add(best)
        del avail[best]
        if len(sel) >= target_pages and not any(deficit(sel).values()):
            break

    chosen = sorted(sel)
    chosen_set = set(chosen)

    val_cnt: Counter = Counter()
    trn_cnt: Counter = Counter()
    for pid, cnt in pages.items():
        (val_cnt if pid in chosen_set else trn_cnt).update(cnt)

    print(f"Stron z bboxami: {len(pages)} | val: {len(chosen)} "
          f"({100 * len(chosen) / len(pages):.0f}%) | klas: {len(class_map)}")

    print(f"\n{'klasa':<32}{'razem':>7}{'train':>7}{'val':>6}  uwagi")
    print("-" * 70)
    zero_val = []
    for c, n in sorted(dist.items(), key=lambda kv: -kv[1]):
        if c not in class_map:
            continue
        v, t = val_cnt[c], trn_cnt[c]
        note = ""
        if c in single:
            note = "JEDNA STRONA — trwale niemierzalne"
        elif v == 0:
            note = "brak w val"
            zero_val.append(c)
        elif t == 0:
            note = "[BŁĄD] brak w train"
        elif v < args.min_val:
            note = f"tylko {v} w val — mAP na granicy szumu"
        print(f"{c:<32}{n:>7}{t:>7}{v:>6}  {note}")

    if single:
        print(f"\n[RYZYKO] {len(single)} klas na jednej stronie — kazdy podzial je psuje. "
              "Rozwiazaniem jest doznaczenie kolejnych stron, nie zmiana splitu:")
        for c in single:
            print(f"    {c:<30} {dist[c]:>4} inst. — {sorted(by_class[c])[0][-5:]}")
    if zero_val:
        print(f"\n[BŁĄD] {len(zero_val)} klas nadal bez instancji w val: "
              + ", ".join(zero_val))
    else:
        print("\nOK — kazda klasa poza jednostronnymi ma reprezentacje w val.")

    print("\nStrony val:")
    for pid in sorted(chosen):
        print(f"  {pid}")

    if not args.apply:
        print(f"\nDRY-RUN — nic nie zapisano. Dodaj --apply, aby zapisac do {args.out}.")
        return 0

    text = ("# Strony walidacyjne — dobor stratyfikowany (scripts/build_val_split.py).\n"
            "# Kazda klasa >= min-count ma tu reprezentacje, inaczej jej mAP jest\n"
            "# nieoznaczalne. Val NIGDY nie jest augmentowany.\n"
            + yaml.safe_dump({"val_pages": sorted(chosen)}, allow_unicode=True,
                             sort_keys=False, default_flow_style=False))
    args.out.parent.mkdir(parents=True, exist_ok=True)
    tmp = args.out.with_suffix(args.out.suffix + ".tmp")
    tmp.write_text(text, encoding="utf-8")
    os.replace(tmp, args.out)
    print(f"\nZAPISANO -> {args.out}")
    print("[UWAGA] Zmiana splitu unieważnia porownania mAP z wczesniejszymi biegami.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
