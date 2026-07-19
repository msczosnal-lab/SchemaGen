"""Porownaj gt/*.json z katalogiem backupu — znajdz strony, ktore stracily symbole.

Powstalo po [BŁĄD] 2026-07-19: `apply_reassign` czytal cache SQLite zamiast
`gt/*.json`, wiec nieaktualny cache nadpisal zrodlo prawdy. p034: 108 -> 17 symboli.
Objawem w logu byly "bbox_id nieznalezionych", ale strony, gdzie cache byl stary
a wszystkie id akurat pasowaly, nie daly zadnego sygnalu — dlatego potrzebny jest
przeglad calosci, nie tylko stron z ostrzezeniem.

Uzycie:
    python scripts/gt_restore_check.py                          # najnowszy backup
    python scripts/gt_restore_check.py --backup data/backups/gt-reassign-20260719_182608
    python scripts/gt_restore_check.py --restore                # przywroc pliki, ktore straciły
    python scripts/gt_restore_check.py --restore --min-loss 1   # przywroc kazda strate

Domyslnie NIC nie zapisuje. Przywracanie kopiuje plik z backupu do gt/ atomowo.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from backend.paths import GT, ROOT

BACKUPS = ROOT / "data" / "backups"


def _counts(path: Path) -> tuple[int, int]:
    """(liczba symboli, liczba linii) w pliku GT; (-1,-1) gdy nieczytelny."""
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001 — nieczytelny plik ma byc raportowany, nie wywracac
        return (-1, -1)
    return (len(data.get("symbols") or []), len(data.get("lines") or []))


def _latest_backup() -> Path | None:
    if not BACKUPS.exists():
        return None
    dirs = [d for d in BACKUPS.iterdir() if d.is_dir() and d.name.startswith("gt-")]
    if not dirs:
        return None
    return max(dirs, key=lambda d: d.stat().st_mtime)


def _git_counts(rev: str, rel: str) -> tuple[int, int] | None:
    """(symbole, linie) pliku GT w rewizji gita; None gdy plik tam nie istnieje."""
    out = subprocess.run(
        ["git", "show", f"{rev}:{rel}"],
        cwd=ROOT, capture_output=True, text=True, encoding="utf-8",
    )
    if out.returncode != 0:
        return None
    try:
        data = json.loads(out.stdout)
    except json.JSONDecodeError:
        return None
    return (len(data.get("symbols") or []), len(data.get("lines") or []))


def _run_git(args) -> int:
    """Porownanie gt/ z rewizja gita. Git jest wiarygodniejszy niz backup —
    backup powstaje tuz przed zapisem, wiec zawiera juz wczesniejsze uszkodzenia."""
    rev = args.git_rev
    print(f"Porownanie z rewizja: {rev}")
    losses = []
    checked = 0
    for cur in sorted(GT.glob("*.json")):
        rel = f"gt/{cur.name}"
        ref = _git_counts(rev, rel)
        if ref is None:
            continue
        checked += 1
        c_sym, c_lin = _counts(cur)
        if ref[0] - c_sym >= args.min_loss:
            losses.append((cur.name, ref[0], c_sym, ref[1], c_lin))

    print(f"Plikow porownanych: {checked} | ZE STRATA: {len(losses)}")
    if not losses:
        print(f"\nOK — zadna strona nie stracila symboli wzgledem {rev}.")
        return 0

    print(f"\n{'strona':<52}{rev[:8]:>8}{'teraz':>8}{'strata':>8}  linie")
    print("-" * 88)
    for name, b_sym, c_sym, b_lin, c_lin in sorted(losses, key=lambda t: t[2] - t[1]):
        pct = f"{100 * (b_sym - c_sym) / b_sym:.0f}%" if b_sym else "-"
        print(f"{name[-50:]:<52}{b_sym:>8}{c_sym:>8}{b_sym - c_sym:>8} ({pct})"
              f"   {b_lin}->{c_lin}")
    print(f"\nLacznie utracone symbole: {sum(b - c for _n, b, c, _x, _y in losses)}")

    if not args.restore:
        print(f"\nDRY-RUN — nic nie przywrocono. Dodaj --restore, aby zrobic "
              f"`git checkout {rev} -- gt/<plik>` dla tych stron.")
        return 0

    for name, _b, _c, _bl, _cl in losses:
        subprocess.run(["git", "checkout", rev, "--", f"gt/{name}"], cwd=ROOT, check=True)
        print(f"  przywrocono {name}")

    from backend.db import rebuild_cache_from_gt

    n = rebuild_cache_from_gt()
    print(f"\nPRZYWROCONO {len(losses)} stron z {rev}. Cache odbudowany ({n} stron).")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--backup", type=Path, default=None, help="katalog backupu gt/")
    ap.add_argument("--git-rev", default=None,
                    help="porownaj z rewizja gita zamiast z backupem, np. HEAD~5 "
                         "(backup tez bywa uszkodzony — git jest pewniejszy)")
    ap.add_argument("--restore", action="store_true", help="przywroc pliki ze strata")
    ap.add_argument("--min-loss", type=int, default=1,
                    help="minimalna strata symboli, by uznac za regresje")
    args = ap.parse_args()

    if args.git_rev:
        return _run_git(args)

    bak = args.backup or _latest_backup()
    if bak is None or not bak.exists():
        print(f"[BŁĄD] Nie znaleziono katalogu backupu w {BACKUPS}")
        return 1
    print(f"Backup: {bak}")

    files = sorted(bak.glob("*.json"))
    if not files:
        print("[BŁĄD] Backup nie zawiera plikow *.json")
        return 1

    losses: list[tuple[str, int, int, int, int]] = []
    same = 0
    grew = 0
    for src in files:
        cur = GT / src.name
        b_sym, b_lin = _counts(src)
        if not cur.exists():
            losses.append((src.name, b_sym, 0, b_lin, 0))
            continue
        c_sym, c_lin = _counts(cur)
        if b_sym - c_sym >= args.min_loss:
            losses.append((src.name, b_sym, c_sym, b_lin, c_lin))
        elif c_sym > b_sym:
            grew += 1
        else:
            same += 1

    print(f"Plikow w backupie: {len(files)} | bez zmian: {same} | urosly: {grew} "
          f"| ZE STRATA: {len(losses)}")

    if not losses:
        print("\nOK — zadna strona nie stracila symboli wzgledem backupu.")
        return 0

    print(f"\n{'strona':<52}{'backup':>8}{'teraz':>8}{'strata':>8}  linie")
    print("-" * 88)
    for name, b_sym, c_sym, b_lin, c_lin in sorted(losses, key=lambda t: t[2] - t[1]):
        pct = f"{100 * (b_sym - c_sym) / b_sym:.0f}%" if b_sym else "-"
        print(f"{name[-50:]:<52}{b_sym:>8}{c_sym:>8}{b_sym - c_sym:>8} ({pct})"
              f"   {b_lin}->{c_lin}")

    total = sum(b - c for _n, b, c, _bl, _cl in losses)
    print(f"\nLacznie utracone symbole: {total}")

    if not args.restore:
        print("\nDRY-RUN — nic nie przywrocono. Dodaj --restore, aby skopiowac "
              "te pliki z backupu do gt/.")
        return 0

    for name, _b, _c, _bl, _cl in losses:
        src = bak / name
        dst = GT / name
        tmp = dst.with_suffix(".json.tmp")
        shutil.copy2(src, tmp)
        os.replace(tmp, dst)
        print(f"  przywrocono {name}")

    from backend.db import rebuild_cache_from_gt

    n = rebuild_cache_from_gt()
    print(f"\nPRZYWROCONO {len(losses)} stron. Cache odbudowany z gt/*.json ({n} stron).")
    print("[UWAGA] Zmiany z reassignments.json dla tych stron zostaly cofniete — "
          "powtorz apply_reassign po pobraniu poprawki.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
