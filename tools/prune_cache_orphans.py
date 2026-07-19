"""Usuń z cache SQLite wpisy, które nie mają pliku w ``gt/`` (prompt 025, F3).

Cache ``schematic_graph`` jest odbudowywalny z ``gt/*.json``, ale
``rebuild_cache_from_gt()`` tylko dopisuje — nigdy nie kasuje. Wpisy po stronach
usuniętych lub odsianych (kopie z wyścigu F1) zostają w bazie na zawsze i
``load_schematic_graph`` serwuje je zamiast źródła prawdy.

Domyślnie **dry-run**. Kasuje dopiero z ``--apply``.

    python -m tools.prune_cache_orphans
    python -m tools.prune_cache_orphans --apply

Zabezpieczenia:

* odmawia działania, gdy ``gt/`` ma mniej niż ``--min-gt-files`` plików
  (domyślnie 1) — chroni przed wyczyszczeniem cache przy pustym/niezsynchronizowanym ``gt/``
* przed kasowaniem wypisuje, ile symboli i linii przepadnie
* z ``--apply`` robi kopię bazy obok (``.bak-prune-<data>``)
"""

from __future__ import annotations

import argparse
import json
import shutil
import sqlite3
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from backend import gt_store  # noqa: E402
from backend.paths import DB_PATH  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser(description="Kasuj sieroty z cache schematic_graph")
    ap.add_argument("--apply", action="store_true", help="faktycznie kasuj (domyślnie dry-run)")
    ap.add_argument("--min-gt-files", type=int, default=1)
    args = ap.parse_args()

    if not DB_PATH.exists():
        print(f"Brak bazy: {DB_PATH}")
        return 0

    existing = set(gt_store.list_gt_page_ids())
    if len(existing) < args.min_gt_files:
        print(
            f"[STOP] gt/ ma {len(existing)} plików (< {args.min_gt_files}). "
            "Nie ruszam cache — to wygląda na niezsynchronizowane repo."
        )
        return 2

    conn = sqlite3.connect(DB_PATH, timeout=30.0)
    conn.row_factory = sqlite3.Row
    try:
        rows = conn.execute(
            "SELECT page_id, payload_json FROM schematic_graph ORDER BY page_id"
        ).fetchall()
    except sqlite3.OperationalError as exc:
        print(f"Brak tabeli schematic_graph: {exc}")
        conn.close()
        return 0

    orphans = []
    for r in rows:
        if r["page_id"] in existing:
            continue
        try:
            payload = json.loads(r["payload_json"])
        except json.JSONDecodeError:
            payload = {}
        orphans.append(
            (
                r["page_id"],
                len(payload.get("symbols") or []),
                len(payload.get("lines") or []),
            )
        )

    if not orphans:
        print(f"Cache czysty — {len(rows)} wpisów, wszystkie mają plik w gt/.")
        conn.close()
        return 0

    print(f"Sieroty w cache: {len(orphans)} (gt/ ma {len(existing)} plików)")
    for pid, n_sym, n_lin in orphans:
        print(f"    {pid:50} {n_sym:4} sym./{n_lin:3} linii")
    tot_sym = sum(o[1] for o in orphans)
    tot_lin = sum(o[2] for o in orphans)
    print(f"Do skasowania łącznie: {tot_sym} symboli, {tot_lin} linii")

    if not args.apply:
        print()
        print("DRY-RUN — nic nie skasowano. Dodaj --apply.")
        print("[UWAGA] Upewnij się, że gt/ jest zacommitowane. Cache nie ma kopii.")
        conn.close()
        return 0

    bak = DB_PATH.with_name(f"{DB_PATH.name}.bak-prune-{date.today().isoformat()}")
    shutil.copy2(DB_PATH, bak)
    print(f"Kopia bazy: {bak}")

    conn.executemany(
        "DELETE FROM schematic_graph WHERE page_id = ?",
        [(o[0],) for o in orphans],
    )
    conn.commit()
    left = conn.execute("SELECT COUNT(*) FROM schematic_graph").fetchone()[0]
    conn.close()
    print(f"Skasowano {len(orphans)} wpisów. W cache zostało: {left}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
