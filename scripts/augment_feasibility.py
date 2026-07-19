"""Ile kafli kwalifikuje sie do augmentacji? — pomiar przed decyzja (prompt 028, Czesc C).

Wariant 1 (offline, kafel-warunkowo) generuje dodatkowa kopie kafla TYLKO gdy
WSZYSTKIE klasy obecne w tym kaflu dopuszczaja dana transformacje. Ultralytics
nie ma augmentacji per-klasa — fliplr/degrees dzialaja na calym obrazie, wiec
kafel z `zlaczka` (symetryczna) i `strzalka_potencjalu_wejsciowa`
(niesymetryczna) nie moze byc odbity: zepsulby te druga.

Ten skrypt liczy, ile kafli w ogole spelnia ten warunek. Jesli wyjdzie ponizej
~10%, wariant 1 jest bezwartosciowy i trzeba isc w C1a/C1b (transformacja
in-place / copy-paste na poziomie symbolu).

Geometria kafli identyczna jak train/tiled_export.py (`windows` + `clip_bbox`),
liczona z `image_width`/`image_height` w GT — PNG stron nie sa potrzebne.

Uzycie:
    python scripts/augment_feasibility.py
    python scripts/augment_feasibility.py --win 1536 --overlap 0.2 --min-count 5
    python scripts/augment_feasibility.py --json data/output/augment_feasibility.json
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

# Uruchomienie: python scripts/augment_feasibility.py (bez wymogu pip install -e .)
_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from backend.class_map import bbox_class, build_class_map, load_palette_map
from backend.symmetry import TRANSFORM_KEYS, load_symmetry_file
from train.dataset_export import load_all_training_records
from train.tiled_export import clip_bbox, windows

#: Zakres stosowania augmentacji (Czesc C1): ponizej dolnego progu najpierw
#: doznaczyc, powyzej gornego — malejacy zwrot przy rosnacym ryzyku artefaktow.
AUG_MIN_INSTANCES = 5
AUG_MAX_INSTANCES = 30


def tile_class_sets(recs, class_map, pmap, win: int, overlap: float, min_visible: float):
    """[(page_id, idx_okna, {klasy w kaflu})] — tylko kafle z >=1 bboxem.

    Odwzorowuje `train.tiled_export.tile_page`: bbox wchodzi do kafla, gdy jego
    widoczna czesc >= min_visible. Klasy spoza `class_map` (ponizej min_count)
    nie trafiaja do treningu, wiec nie blokuja transformacji.
    """
    out = []
    for rec in recs:
        W, H = rec.image_width, rec.image_height
        if not W or not H:
            continue
        boxes = []
        for b in rec.bboxes:
            cls = bbox_class(b.class_name, b.tag, pmap)
            if cls and cls in class_map:
                boxes.append((b.x, b.y, b.width, b.height, cls))
        if not boxes:
            continue
        for i, wnd in enumerate(windows(W, H, win, overlap)):
            present = {
                cls
                for (bx, by, bw, bh, cls) in boxes
                if clip_bbox(bx, by, bw, bh, wnd, min_visible) is not None
            }
            if present:
                out.append((rec.page_id, i, present))
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--win", type=int, default=1536)
    ap.add_argument("--overlap", type=float, default=0.2)
    ap.add_argument("--min-visible", type=float, default=0.35)
    ap.add_argument("--min-count", type=int, default=5)
    ap.add_argument(
        "--ceiling",
        action="store_true",
        help="SUFIT: zaloz zgode dla kazdej klasy poza jawnie zabronionymi w YAML "
        "(pokazuje potencjal wariantu 1 przy w pelni wypelnionym pliku symetrii)",
    )
    ap.add_argument("--json", type=Path, default=None, help="zapisz raport JSON")
    args = ap.parse_args()

    recs = load_all_training_records()
    if not recs:
        print("[BŁĄD] Brak danych GT (gt/*.json + SQLite).")
        return 1

    pmap = load_palette_map()
    class_map, dist = build_class_map(recs, min_count=args.min_count, bucket_rare=False)
    sym = load_symmetry_file(known_classes=set(dist))
    for w in sym.warnings:
        print(f"[UWAGA] symbol-symmetry.yaml: {w}")

    tiles = tile_class_sets(recs, class_map, pmap, args.win, args.overlap, args.min_visible)
    total = len(tiles)
    if not total:
        print("[BŁĄD] 0 kafli — sprawdz image_width/height w gt/*.json.")
        return 1

    # --- wariant 1: kafel kwalifikuje sie, gdy KAZDA klasa w nim dopuszcza transformacje ---
    # W trybie --ceiling zgoda ma kazda klasa poza jawnie zabroniona w YAML. Bez tego
    # wynik mowi wiecej o stopniu wypelnienia symbol-symmetry.yaml niz o geometrii kafli.
    denied = {c for c, s in sym.specs.items() if not s.any_allowed}

    def allows(cls: str, transform: str) -> bool:
        if args.ceiling:
            return cls not in denied
        return sym.allows(cls, transform)

    qualifying: dict[str, int] = {}
    blockers: dict[str, Counter] = defaultdict(Counter)
    any_transform = 0
    for _pid, _i, present in tiles:
        ok_any = False
        for t in TRANSFORM_KEYS:
            bad = [c for c in present if not allows(c, t)]
            if bad:
                blockers[t].update(bad)
            else:
                qualifying[t] = qualifying.get(t, 0) + 1
                ok_any = True
        if ok_any:
            any_transform += 1

    print(f"Stron: {len(recs)} | klas w treningu (min-count={args.min_count}): {len(class_map)}")
    print(f"Kafli z >=1 bboxem (win={args.win}, overlap={args.overlap}): {total}")
    consenting = sorted(c for c in class_map if sym.get(c).any_allowed)
    print(f"Klas z jakakolwiek zgoda na transformacje: {len(consenting)}/{len(class_map)}"
          + (f" ({', '.join(consenting)})" if consenting else ""))

    print("\n=== WARIANT 1 (kafel-warunkowo): ile kafli mozna zaugmentowac ===")
    print(f"{'transformacja':<16}{'kafli':>8}{'% wszystkich':>14}   glowny blocker")
    print("-" * 72)
    for t in TRANSFORM_KEYS:
        n = qualifying.get(t, 0)
        top = blockers[t].most_common(1)
        blk = f"{top[0][0]} ({top[0][1]} kafli)" if top else "-"
        print(f"{t:<16}{n:>8}{100 * n / total:>13.1f}%   {blk}")
    pct_any = 100 * any_transform / total
    print("-" * 72)
    print(f"{'DOWOLNA':<16}{any_transform:>8}{pct_any:>13.1f}%")

    verdict = (
        "wariant 1 uzyteczny — wdrazac jako pierwszy"
        if pct_any >= 10
        else "wariant 1 BEZWARTOSCIOWY (<10% kafli) — isc w C1a (transformacja in-place)"
    )
    print(f"\n=> WERDYKT: {pct_any:.1f}% kafli, {verdict}"
          + ("  [tryb --ceiling]" if args.ceiling else ""))
    if not args.ceiling:
        print("   Uwaga: bez --ceiling ta liczba mierzy stopien wypelnienia "
              "symbol-symmetry.yaml, nie geometrie kafli. Porownaj z --ceiling.")

    # --- struktura kafli: ile roznych klas przypada na kafel ---
    # To rozstrzyga zalozenie "schematy sa geste i mieszane". Kafel jednoklasowy
    # kwalifikuje sie zawsze, gdy ta jedna klasa ma zgode.
    per_tile = Counter(len(p) for _, _, p in tiles)
    mono = per_tile.get(1, 0)
    print(f"\n=== Struktura kafli ===")
    print(f"  kafli jednoklasowych: {mono}/{total} ({100 * mono / total:.1f}%)")
    print("  klas na kafel: "
          + ", ".join(f"{k}->{v}" for k, v in sorted(per_tile.items())))

    # --- zakres C1: klasy 5-30 instancji ---
    in_range = sorted(
        (c, n) for c, n in dist.items()
        if AUG_MIN_INSTANCES <= n <= AUG_MAX_INSTANCES and c in class_map
    )
    c1_classes = {c for c, _ in in_range}
    tiles_with_c1 = sum(1 for _, _, p in tiles if p & c1_classes)
    qual_c1 = sum(
        1
        for _, _, p in tiles
        if (p & c1_classes) and any(all(allows(c, t) for c in p) for t in TRANSFORM_KEYS)
    )
    print(f"\n=== Celowanie: kafle zawierajace klase {AUG_MIN_INSTANCES}-"
          f"{AUG_MAX_INSTANCES} instancji (te, ktorym augmentacja jest potrzebna) ===")
    print(f"  zawieraja klase z zakresu C1:      {tiles_with_c1}/{total} "
          f"({100 * tiles_with_c1 / total:.1f}%)")
    print(f"  z tego kwalifikuja sie (wariant 1): {qual_c1}"
          + (f" ({100 * qual_c1 / tiles_with_c1:.1f}% z nich)" if tiles_with_c1 else ""))
    if qual_c1 < tiles_with_c1 * 0.5:
        print("  [RYZYKO] wariant 1 augmentuje glownie kafle klas licznych, "
              "ktore dodatkowych danych nie potrzebuja")
    print(f"\n=== Zakres C1 (klasy {AUG_MIN_INSTANCES}-{AUG_MAX_INSTANCES} instancji): "
          f"{len(in_range)} klas ===")
    for c, n in sorted(in_range, key=lambda kv: kv[1]):
        s = sym.get(c)
        state = ",".join(s.transforms()) if s.any_allowed else "(brak zgody)"
        print(f"  {c:<34} {n:>4} inst.   {state}")
    unset = [c for c, _ in in_range if not sym.get(c).any_allowed]
    if unset:
        print(f"\n[UWAGA] {len(unset)} klas z zakresu C1 nie ma jeszcze zgody w "
              "symbol-symmetry.yaml — przejrzyj je w element_review.py")

    # --- top blockery ogolem: co najbardziej ogranicza wariant 1 ---
    all_blk: Counter = Counter()
    for t in TRANSFORM_KEYS:
        all_blk.update(blockers[t])
    if all_blk:
        print("\n=== Klasy najczesciej blokujace kafel (suma po transformacjach) ===")
        for c, n in all_blk.most_common(10):
            print(f"  {n:>7}  {c}")

    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(
            json.dumps(
                {
                    "win": args.win,
                    "overlap": args.overlap,
                    "min_visible": args.min_visible,
                    "min_count": args.min_count,
                    "tiles_total": total,
                    "qualifying": {t: qualifying.get(t, 0) for t in TRANSFORM_KEYS},
                    "qualifying_any": any_transform,
                    "pct_any": round(pct_any, 2),
                    "classes_with_consent": consenting,
                    "c1_range": {c: n for c, n in in_range},
                    "top_blockers": all_blk.most_common(20),
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
        print(f"\nRaport JSON -> {args.json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
