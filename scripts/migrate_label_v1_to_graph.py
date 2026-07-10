"""Migracja GT v1 → SchematicGraph v2: tylko bbox + terminale, bez linii.

Linie OD-DO rysujesz ręcznie w labelerze v2 (:8765).

Przykłady:
    python scripts/migrate_label_v1_to_graph.py --page SchematWRT01_p027
    python scripts/migrate_label_v1_to_graph.py --page SchematWRT01_p040 --force
    python scripts/migrate_label_v1_to_graph.py --all
    python scripts/migrate_label_v1_to_graph.py --all --dry-run
"""

from __future__ import annotations

import argparse
import sys

from backend.db import db_session, init_db, list_pages
from backend.paths import ensure_data_dirs
from labeler.migrate_label_v1 import MigrateReport, migrate_page


def _pages_with_v1() -> list[str]:
    init_db()
    with db_session() as conn:
        rows = conn.execute(
            """
            SELECT page_id FROM annotations
            WHERE json_extract(payload_json, '$.bboxes') IS NOT NULL
              AND json_array_length(json_extract(payload_json, '$.bboxes')) > 0
            ORDER BY page_id
            """
        ).fetchall()
    if rows:
        return [r["page_id"] for r in rows]
    return [
        p["id"]
        for p in list_pages()
        if p.get("annotation_updated_at")
    ]


def _print_report(r: MigrateReport) -> None:
    if r.status == "ok":
        warn = ""
        if r.symbols_without_terminals:
            n = len(r.symbols_without_terminals)
            warn = f" | bez terminali: {n}"
        print(
            f"{r.page_id}: OK - symbole={r.symbols}, terminale={r.terminals}, "
            f"linie={r.lines} ({r.reason}){warn}"
        )
        if r.symbols_without_terminals and len(r.symbols_without_terminals) <= 8:
            print(f"  -> {', '.join(r.symbols_without_terminals)}")
    elif r.status == "skipped":
        print(f"{r.page_id}: POMINIETO - {r.reason}")
    else:
        print(f"{r.page_id}: BLAD - {r.reason}", file=sys.stderr)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--page", help="page_id (stem PNG w data/raw)")
    ap.add_argument("--all", action="store_true", help="wszystkie strony z bboxami v1")
    ap.add_argument("--force", action="store_true", help="nadpisz istniejący graf v2")
    ap.add_argument("--dry-run", action="store_true", help="raport bez zapisu do SQLite")
    args = ap.parse_args()

    if not args.page and not args.all:
        print("Podaj --page lub --all", file=sys.stderr)
        return 1

    ensure_data_dirs()
    pages = _pages_with_v1() if args.all else [args.page]
    if not pages:
        print("Brak stron z adnotacjami v1", file=sys.stderr)
        return 1

    ok = skip = err = 0
    for page_id in pages:
        report = migrate_page(page_id, force=args.force, dry_run=args.dry_run)
        _print_report(report)
        if report.status == "ok":
            ok += 1
        elif report.status == "skipped":
            skip += 1
        else:
            err += 1

    print(f"\nPodsumowanie: ok={ok}, pominiete={skip}, bledy={err}")
    return 1 if err else 0


if __name__ == "__main__":
    raise SystemExit(main())
