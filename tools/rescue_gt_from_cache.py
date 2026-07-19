"""Ratunek GT, który istnieje tylko w cache SQLite (prompt 025).

Kontekst: audyt A1 wykrył strony obecne w tabeli ``schematic_graph``, dla których
nie ma pliku ``gt/<page_id>.json``. Baza jest w ``.gitignore`` i już raz padła
(``malformed``) — te dane nie mają żadnej kopii w repo.

Domyślnie **nie dotyka ``gt/``**. Zrzuca sieroty do katalogu roboczego
(``gt/_rescue_<data>/``), żeby nic nie wjechało do źródła prawdy bez decyzji
człowieka. Podkatalog nie wpada w glob ``gt/*.json``, więc aplikacja go zignoruje.

    python -m tools.rescue_gt_from_cache                 # zrzut do gt/_rescue_<data>/
    python -m tools.rescue_gt_from_cache --min-symbols 1 # tylko strony z danymi
    python -m tools.rescue_gt_from_cache --promote       # dopiero to pisze do gt/

``--promote`` NIE nadpisuje istniejących plików ``gt/*.json`` (źródło prawdy
zawsze wygrywa) — pomija je i wypisuje listę.
"""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from datetime import date
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from backend import gt_store  # noqa: E402
from backend.paths import DB_PATH, GT  # noqa: E402


def _read_cache() -> list[tuple[str, dict[str, Any], str]]:
    if not DB_PATH.exists():
        raise SystemExit(f"Brak bazy: {DB_PATH}")
    conn = sqlite3.connect(f"file:{DB_PATH}?immutable=1", uri=True, timeout=10.0)
    conn.row_factory = sqlite3.Row
    try:
        rows = conn.execute(
            "SELECT page_id, payload_json, updated_at FROM schematic_graph ORDER BY page_id"
        ).fetchall()
    except sqlite3.OperationalError as exc:
        raise SystemExit(f"Brak tabeli schematic_graph: {exc}") from exc
    finally:
        conn.close()
    out = []
    for r in rows:
        try:
            out.append((r["page_id"], json.loads(r["payload_json"]), r["updated_at"] or ""))
        except json.JSONDecodeError:
            print(f"[POMINIĘTO] {r['page_id']}: payload_json nie parsuje się")
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description="Ratunek GT z cache SQLite")
    ap.add_argument("--min-symbols", type=int, default=0, help="pomiń strony poniżej progu")
    ap.add_argument(
        "--promote",
        action="store_true",
        help="zapisz prosto do gt/ (nie nadpisuje istniejących plików)",
    )
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    rows = _read_cache()
    existing = set(gt_store.list_gt_page_ids())

    dest = GT if args.promote else GT / f"_rescue_{date.today().isoformat()}"
    written: list[str] = []
    skipped_existing: list[str] = []
    skipped_small: list[str] = []

    for page_id, payload, updated_at in rows:
        n_sym = len(payload.get("symbols") or [])
        n_lin = len(payload.get("lines") or [])
        if page_id in existing:
            skipped_existing.append(page_id)
            continue
        if n_sym < args.min_symbols and n_lin == 0:
            skipped_small.append(page_id)
            continue
        target = dest / f"{gt_store.sanitize_page_id(page_id)}.json"
        print(f"{'DRY ' if args.dry_run else ''}{page_id}: {n_sym} sym./{n_lin} linii "
              f"({updated_at}) -> {target}")
        if not args.dry_run:
            dest.mkdir(parents=True, exist_ok=True)
            tmp = target.with_suffix(".json.tmp")
            tmp.write_text(
                json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
                newline="\n",
            )
            tmp.replace(target)
        written.append(page_id)

    print()
    print(f"Zapisane: {len(written)} -> {dest}")
    if skipped_existing:
        print(f"Pominięte (plik gt/ już istnieje, źródło prawdy wygrywa): {len(skipped_existing)}")
    if skipped_small:
        print(f"Pominięte (poniżej --min-symbols): {len(skipped_small)}")
    if not args.promote and written:
        print()
        print("To jest katalog roboczy — aplikacja go NIE czyta (glob gt/*.json nie schodzi")
        print("do podkatalogów). Przejrzyj zawartość, potem przenieś ręcznie albo puść")
        print("ponownie z --promote.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
