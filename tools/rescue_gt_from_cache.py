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
from tools.gt_dup_scan import signature  # noqa: E402


def _dup_victims(
    rows: list[tuple[str, dict[str, Any], str]],
    existing: set[str],
    min_symbols: int,
) -> dict[str, str]:
    """page_id -> page_id oryginału, dla stron będących kopią innej strony.

    Zachowujemy: stronę obecną w ``gt/`` (źródło prawdy), a gdy takiej nie ma —
    najstarszy zapis w grupie. Reszta to kopie z wyścigu ``selectPage`` (F1).
    Grupy poniżej ``min_symbols`` pomijamy — przy 2 bboxach kolizja podpisu
    może być przypadkiem, a nie kopią.
    """
    groups: dict[str, list[tuple[str, str]]] = {}
    for page_id, payload, updated_at in rows:
        sig, n_sym, _ = signature(payload)
        if n_sym < min_symbols:
            continue
        groups.setdefault(sig, []).append((page_id, updated_at))
    # strony już w gt/ też liczą się jako kandydat na oryginał
    for pid in existing:
        payload = gt_store.read_gt_json(pid)
        if not payload:
            continue
        sig, n_sym, _ = signature(payload)
        if n_sym >= min_symbols and sig in groups:
            groups[sig].append((pid, ""))

    victims: dict[str, str] = {}
    for sig, items in groups.items():
        pages = {p for p, _ in items}
        if len(pages) < 2:
            continue
        in_gt = sorted(p for p in pages if p in existing)
        if in_gt:
            keep = in_gt[0]
        else:
            keep = min(items, key=lambda i: (i[1] or "9999"))[0]
        for p in sorted(pages):
            if p != keep:
                victims[p] = keep
    return victims


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
    ap.add_argument(
        "--skip-dups",
        action="store_true",
        help="pomiń strony o zawartości identycznej z inną (kopie z wyścigu F1)",
    )
    ap.add_argument(
        "--dup-min-symbols",
        type=int,
        default=5,
        help="próg, poniżej którego identyczny podpis nie liczy się jako kopia (domyślnie 5)",
    )
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    rows = _read_cache()
    existing = set(gt_store.list_gt_page_ids())
    victims = (
        _dup_victims(rows, existing, args.dup_min_symbols) if args.skip_dups else {}
    )
    skipped_dup: list[str] = []

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
        if page_id in victims:
            skipped_dup.append(f"{page_id} (kopia {victims[page_id]})")
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
    if args.dry_run:
        print(f"DRY-RUN — nic nie zapisano. Do zapisania: {len(written)} -> {dest}")
    else:
        print(f"Zapisane: {len(written)} -> {dest}")
    if skipped_existing:
        print(f"Pominięte (plik gt/ już istnieje, źródło prawdy wygrywa): {len(skipped_existing)}")
    if skipped_dup:
        print(f"Pominięte jako kopie z wyścigu F1: {len(skipped_dup)}")
        for s in skipped_dup:
            print(f"    {s}")
    if skipped_small:
        print(f"Pominięte (poniżej --min-symbols): {len(skipped_small)}")
    if not args.promote and written and not args.dry_run:
        print()
        print("To jest katalog roboczy — aplikacja go NIE czyta (glob gt/*.json nie schodzi")
        print("do podkatalogów). Przejrzyj zawartość, potem przenieś ręcznie albo puść")
        print("ponownie z --promote.")
        print()
        print("[UWAGA] Skrypt nie kasuje plików, których nie zapisuje. Jeśli wcześniejszy")
        print("bieg (bez --skip-dups) zapisał do tego katalogu więcej stron, nadmiarowe")
        print("pliki zostaną. Sprawdź liczbę: powinna zgadzać się z 'Zapisane'.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
