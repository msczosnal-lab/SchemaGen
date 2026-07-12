"""Migracja jednorazowa: wiersze cache ``schematic_graph`` (SQLite) → ``gt/*.json``.

Użycie:
    python -m tools.export_gt_to_json [--dry-run]

Po uruchomieniu zacommituj powstałe pliki ``gt/*.json``. Idempotentne — można
puszczać wielokrotnie (nadpisuje pliki treścią z bazy, zapis atomowy).
"""

from __future__ import annotations

import argparse
import json
import sqlite3

from backend import gt_store
from backend.paths import DB_PATH


def export_all(dry_run: bool = False) -> list[str]:
    if not DB_PATH.exists():
        print(f"[export_gt] brak bazy: {DB_PATH} — nic do migracji")
        return []
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        rows = conn.execute(
            "SELECT page_id, payload_json FROM schematic_graph ORDER BY page_id"
        ).fetchall()
    except sqlite3.OperationalError:
        print("[export_gt] brak tabeli schematic_graph — nic do migracji")
        return []
    finally:
        conn.close()

    written: list[str] = []
    for row in rows:
        page_id = row["page_id"]
        payload = json.loads(row["payload_json"])
        if dry_run:
            print(f"[export_gt] DRY {page_id} -> {gt_store.gt_path(page_id)}")
        else:
            path = gt_store.write_gt_json(page_id, payload)
            print(f"[export_gt] {page_id} -> {path}")
        written.append(page_id)
    print(f"[export_gt] {'(dry) ' if dry_run else ''}stron: {len(written)}")
    return written


def main() -> None:
    ap = argparse.ArgumentParser(description="Eksport GT z SQLite do gt/*.json")
    ap.add_argument("--dry-run", action="store_true", help="tylko wypisz, nie zapisuj")
    args = ap.parse_args()
    export_all(dry_run=args.dry_run)


if __name__ == "__main__":
    main()
