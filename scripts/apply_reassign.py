"""Zastosuj zmiany klas z reassignments.json do GT v2 (gt/*.json).

reassignments.json (z element_review.py): [{page_id, bbox_id, old, new_tag}, ...]
Ustawia type/tag symbolu na `new_tag` -> przy eksporcie zmienia sie klasa YOLO.
new_tag="__DELETE__" usuwa symbol (i linie do niego prowadzace).

Zapis przez backend.db.save_schematic_graph (atomowo, guard empty-overwrite).
Nie zapisuje bezposrednio do cache SQLite.

Uzycie:
    python scripts/apply_reassign.py                 # dry-run (nic nie zapisuje)
    python scripts/apply_reassign.py --apply
    python scripts/apply_reassign.py --file data/reassignments.json --apply
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

try:
    from scripts._pick_input import pick_input
except ModuleNotFoundError:  # uruchomienie z katalogu scripts/
    from _pick_input import pick_input

from backend import gt_store
from backend.db import load_annotation, load_schematic_graph, rebuild_cache_from_gt, save_schematic_graph
from backend.models.label import LabelRecord
from backend.models.schematic_graph import GraphSymbol, SchematicGraph
from backend.paths import ROOT

DELETE = "__DELETE__"


def _load_page_graph(page_id: str) -> SchematicGraph | None:
    """GT v2 z pliku/cache; fallback: konwersja label v1 -> SchematicGraph."""
    raw = load_schematic_graph(page_id)
    if raw:
        return SchematicGraph.model_validate(raw)
    data = load_annotation(page_id)
    if not data:
        return None
    rec = LabelRecord.model_validate(data)
    if not rec.bboxes:
        return None
    from labeler.migrate_label_v1 import label_record_to_graph

    return label_record_to_graph(rec)


def _retag_symbol(sym: GraphSymbol, new_class: str) -> None:
    sym.type = new_class
    sym.tag = new_class


def _delete_symbols(graph: SchematicGraph, ids: set[str]) -> int:
    if not ids:
        return 0
    before = len(graph.symbols)
    graph.symbols = [s for s in graph.symbols if s.id not in ids]

    def touches(sym_id: str, ref: str) -> bool:
        return ref.startswith(f"{sym_id}:")

    graph.lines = [
        ln
        for ln in graph.lines
        if not any(touches(sid, ln.from_ref) or touches(sid, ln.to) for sid in ids)
    ]
    return before - len(graph.symbols)


def _backup_gt_pages(page_ids: set[str]) -> Path | None:
    existing = [pid for pid in page_ids if gt_store.gt_path(pid).exists()]
    if not existing:
        return None
    bak_dir = ROOT / "data" / "backups" / f"gt-reassign-{datetime.now():%Y%m%d_%H%M%S}"
    bak_dir.mkdir(parents=True, exist_ok=True)
    for pid in existing:
        src = gt_store.gt_path(pid)
        shutil.copy2(src, bak_dir / src.name)
    return bak_dir


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
        Path.home() / "Downloads" / "reassignments.json",
        Path.cwd() / "reassignments.json",
    ]
    path = pick_input(candidates, "reassignments.json")
    if path is None:
        return 1
    changes = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(changes, list) or not changes:
        print("Pusta lista zmian.")
        return 1

    # Podsumowanie ZANIM cokolwiek ruszy — zeby bylo widac, czy to ten zestaw zmian.
    summary = Counter((c.get("old", "?"), c.get("new_tag", "?")) for c in changes)
    n_del = sum(n for (_o, new), n in summary.items() if new == DELETE)
    print(f"\nZestaw zmian: {len(changes)} pozycji ({n_del} usuniec, "
          f"{len(changes) - n_del} retagow) na {len({c['page_id'] for c in changes})} stronach")
    for (old, new), n in summary.most_common(12):
        print(f"  {n:>4}  {old:<32} -> {new}")
    if len(summary) > 12:
        print(f"  ... i {len(summary) - 12} innych par")
    print()

    by_page: dict[str, dict[str, str]] = defaultdict(dict)
    for c in changes:
        by_page[c["page_id"]][c["bbox_id"]] = c["new_tag"]

    if args.apply:
        db = ROOT / "data" / "schemagen.db"
        if db.exists():
            bak = db.with_name(f"schemagen.db.bak-{datetime.now():%Y%m%d_%H%M%S}")
            shutil.copy2(db, bak)
            print(f"Backup bazy -> {bak}")
        gt_bak = _backup_gt_pages(set(by_page))
        if gt_bak:
            print(f"Backup gt/*.json -> {gt_bak}")

    total = 0
    deleted = 0
    missing = 0
    skipped = 0
    for page_id, mapping in by_page.items():
        graph = _load_page_graph(page_id)
        if graph is None:
            print(f"[RYZYKO] brak GT/adnotacji: {page_id}")
            missing += len(mapping)
            continue

        del_ids = {i for i, t in mapping.items() if t == DELETE}
        applied = 0
        for sym in graph.symbols:
            if sym.id in del_ids:
                continue
            if sym.id in mapping and mapping[sym.id] != DELETE:
                _retag_symbol(sym, mapping[sym.id])
                applied += 1

        n_del = _delete_symbols(graph, del_ids)
        found = applied + n_del
        not_found = len(mapping) - found
        missing += not_found
        total += applied
        deleted += n_del

        flag = f" ({not_found} bbox_id nieznalezionych)" if not_found else ""
        print(f"{page_id}: {applied} retag, {n_del} usun{flag}")

        if args.apply and found:
            res = save_schematic_graph(
                page_id, graph.model_dump(mode="json", by_alias=True)
            )
            if res["status"] == "skipped_empty_overwrite":
                print(f"  [UWAGA] skipped_empty_overwrite — graf pusty, zapis pominiety")
                skipped += 1

    if args.apply and total + deleted > skipped:
        n = rebuild_cache_from_gt()
        print(f"Cache odbudowany z gt/*.json ({n} stron)")

    print(
        f"\n{'ZAPISANO' if args.apply else 'DRY-RUN'}: {total} retag, "
        f"{deleted} usunietych, {missing} nieznalezionych bbox_id."
    )
    if skipped:
        print(f"[UWAGA] {skipped} stron pominietych (guard empty-overwrite)")
    if not args.apply:
        print("Dodaj --apply aby zapisac do gt/*.json.")
    else:
        print("GT zapisane w gt/*.json (zrodlo prawdy).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
