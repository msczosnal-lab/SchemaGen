"""Odzyskiwanie uszkodzonej bazy SQLite (malformed disk image).

Uzycie (PC Filip, z katalogu repo, w venv):
    python tools/recover_db.py

Kolejnosc dzialania:
1. Kopia uszkodzonej bazy -> schemagen.db.corrupt-<timestamp> (nic nie kasujemy).
2. Proba `sqlite3 .recover` (jesli CLI dostepne) -> pelne odzyskanie.
3. Fallback: salvage per-tabela (kopiuje czytelne wiersze).
4. Jesli nic sie nie da: swieza pusta baza (labeler znow dziala; graf p028
   ew. z ostatniego backupu schemagen.db.bak-*).

Po uruchomieniu: zrestartuj uvicorn i odswiez przegladarke.
"""

from __future__ import annotations

import shutil
import sqlite3
import subprocess
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "schemagen.db"

TABLES = ["pages", "annotations", "model_versions", "tag_usage", "schematic_graph"]


def _stamp() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def _init_schema(path: Path) -> None:
    sys.path.insert(0, str(ROOT))
    import backend.db as dbm  # noqa: E402

    dbm.DB_PATH = path
    import backend.paths as pm  # noqa: E402

    pm.DB_PATH = path
    dbm.init_db()


def _try_sqlite_recover(corrupt: Path, out: Path) -> bool:
    exe = shutil.which("sqlite3")
    if not exe:
        print("  [i] brak CLI sqlite3 — pomijam .recover")
        return False
    try:
        dump = subprocess.run(
            [exe, str(corrupt), ".recover"],
            capture_output=True, text=True, timeout=120,
        )
        if dump.returncode != 0 or not dump.stdout.strip():
            print(f"  [i] .recover nic nie zwrocil ({dump.returncode})")
            return False
        newc = sqlite3.connect(out)
        newc.executescript(dump.stdout)
        newc.commit()
        newc.close()
        print("  [OK] .recover zbudowal nowa baze")
        return True
    except Exception as exc:  # noqa: BLE001
        print(f"  [i] .recover blad: {exc}")
        return False


def _salvage_per_table(corrupt: Path, out: Path) -> dict[str, int]:
    _init_schema(out)
    counts: dict[str, int] = {}
    try:
        src = sqlite3.connect(f"file:{corrupt}?mode=ro", uri=True)
    except sqlite3.DatabaseError as exc:
        print(f"  [!] nie moge otworzyc uszkodzonej bazy: {exc}")
        return counts
    dst = sqlite3.connect(out)
    for tbl in TABLES:
        n = 0
        try:
            cur = src.execute(f"SELECT * FROM {tbl}")
            cols = [d[0] for d in cur.description]
            ph = ",".join("?" * len(cols))
            while True:
                try:
                    row = cur.fetchone()
                except sqlite3.DatabaseError:
                    break  # trafilismy na uszkodzona strone — konczymy tabele
                if row is None:
                    break
                try:
                    dst.execute(
                        f"INSERT OR REPLACE INTO {tbl} ({','.join(cols)}) VALUES ({ph})",
                        tuple(row),
                    )
                    n += 1
                except sqlite3.DatabaseError:
                    continue
            dst.commit()
        except sqlite3.DatabaseError as exc:
            print(f"    - {tbl}: nieczytelna ({exc})")
        counts[tbl] = n
    src.close()
    dst.close()
    return counts


def main() -> int:
    if not DB.exists():
        print(f"[!] Brak bazy: {DB} — uruchom labeler raz, utworzy pusta.")
        return 1

    stamp = _stamp()
    corrupt = DB.with_name(f"schemagen.db.corrupt-{stamp}")
    shutil.copy2(DB, corrupt)
    print(f"[1] Kopia uszkodzonej bazy: {corrupt.name}")

    # sprzatanie WAL/journal, ktore moga byc uszkodzone
    for ext in ("-wal", "-shm", "-journal"):
        p = DB.with_name(DB.name + ext)
        if p.exists():
            p.unlink()
            print(f"    usunieto {p.name}")

    rebuilt = DB.with_name(f"schemagen.rebuilt-{stamp}.db")

    print("[2] Proba sqlite3 .recover ...")
    ok = _try_sqlite_recover(corrupt, rebuilt)

    if not ok:
        print("[3] Fallback: salvage per-tabela ...")
        if rebuilt.exists():
            rebuilt.unlink()
        counts = _salvage_per_table(corrupt, rebuilt)
        total = sum(counts.values())
        for t, n in counts.items():
            print(f"    - {t}: {n} wierszy")
        if total == 0:
            print("[4] Nic nie odzyskano. Sprawdz backupy:")
            for bak in sorted(DB.parent.glob("schemagen.db.bak-*")):
                print(f"      {bak.name} ({bak.stat().st_size} B)")
            print("    Tworze swieza pusta baze (labeler znow zadziala).")
            if rebuilt.exists():
                rebuilt.unlink()
            _init_schema(rebuilt)

    # integralnosc odbudowanej bazy
    chk = sqlite3.connect(rebuilt).execute("PRAGMA integrity_check").fetchone()[0]
    print(f"[5] integrity_check odbudowanej: {chk}")
    if chk != "ok":
        print("[!] Odbudowana baza tez ma problemy — NIE podmieniam. Zostaje kopia.")
        return 2

    # podmiana: stara -> .old, odbudowana -> schemagen.db
    old = DB.with_name(f"schemagen.db.old-{stamp}")
    DB.replace(old)
    rebuilt.replace(DB)
    print(f"[6] Gotowe. Aktywna baza podmieniona. Stara: {old.name}")
    print("    Zrestartuj uvicorn i odswiez przegladarke (Ctrl+F5).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
