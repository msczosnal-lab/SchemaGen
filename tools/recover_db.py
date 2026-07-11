"""Odzyskiwanie uszkodzonej bazy SQLite (malformed disk image).

Uzycie (PC Filip, venv, z katalogu repo) — NAJPIERW zatrzymaj uvicorn i wstrzymaj OneDrive:
    python tools/recover_db.py            # normalne odzyskiwanie
    python tools/recover_db.py --from-bak # wymus odbudowe z backupu .bak-*

Bezpieczne: NIC nie kasuje. Buduje schemagen.rebuilt-<ts>.db, sprawdza
integralnosc, dopiero potem atomowo podmienia na schemagen.db (retry przy
blokadzie). Grafy (bboxy) probuje wyciagnac skanem po rowid — omija uszkodzone
strony zamiast poddawac sie na pierwszym bledzie.
"""

from __future__ import annotations

import os
import shutil
import sqlite3
import sys
import time
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
DB = DATA / "schemagen.db"
TABLES = ["pages", "annotations", "model_versions", "tag_usage", "schematic_graph"]


def _stamp() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def _init_schema(path: Path) -> None:
    sys.path.insert(0, str(ROOT))
    import backend.db as dbm
    import backend.paths as pm
    dbm.DB_PATH = path
    pm.DB_PATH = path
    dbm.init_db()


def _pick_source():
    if DB.exists() and DB.stat().st_size > 0:
        return DB
    cands = sorted(
        list(DATA.glob("schemagen.db.old-*")) + list(DATA.glob("schemagen.db.corrupt-*")),
        key=lambda p: p.stat().st_mtime, reverse=True,
    )
    return cands[0] if cands else None


def _newest_bak():
    baks = sorted(DATA.glob("schemagen.db.bak-*"), key=lambda p: p.stat().st_mtime, reverse=True)
    return baks[0] if baks else None


def _copy_table(src, dst, tbl):
    try:
        cur = src.execute("SELECT * FROM " + tbl)
        cols = [d[0] for d in cur.description]
    except sqlite3.DatabaseError:
        cols = None
    n = 0
    if cols:
        ph = ",".join("?" * len(cols))
        ok_bulk = True
        while True:
            try:
                row = cur.fetchone()
            except sqlite3.DatabaseError:
                ok_bulk = False
                break
            if row is None:
                break
            try:
                dst.execute("INSERT OR REPLACE INTO %s (%s) VALUES (%s)" % (tbl, ",".join(cols), ph), tuple(row))
                n += 1
            except sqlite3.DatabaseError:
                continue
        dst.commit()
        if ok_bulk:
            return n
    # skan po rowid
    try:
        mx = src.execute("SELECT max(rowid) FROM " + tbl).fetchone()[0]
    except sqlite3.DatabaseError:
        mx = None
    hi = int(mx) if mx else 500000
    if not cols:
        cols = [r[1] for r in dst.execute("PRAGMA table_info(%s)" % tbl).fetchall()]
    ph = ",".join("?" * len(cols))
    got = 0
    for rid in range(1, hi + 1):
        try:
            r = src.execute("SELECT %s FROM %s WHERE rowid=?" % (",".join(cols), tbl), (rid,)).fetchone()
        except sqlite3.DatabaseError:
            continue
        if r is None:
            continue
        try:
            dst.execute("INSERT OR REPLACE INTO %s (%s) VALUES (%s)" % (tbl, ",".join(cols), ph), tuple(r))
            got += 1
        except sqlite3.DatabaseError:
            continue
    dst.commit()
    return max(n, got)


def _salvage(src_path, out):
    _init_schema(out)
    counts = {}
    src = sqlite3.connect("file:%s?mode=ro" % src_path, uri=True)
    dst = sqlite3.connect(out)
    for tbl in TABLES:
        try:
            counts[tbl] = _copy_table(src, dst, tbl)
        except sqlite3.DatabaseError as exc:
            print("    - %s: blad (%s)" % (tbl, exc))
            counts[tbl] = 0
    src.close()
    dst.close()
    return counts


def _atomic_swap(rebuilt):
    for attempt in range(1, 6):
        try:
            os.replace(rebuilt, DB)
            return True
        except PermissionError:
            print("    [blokada pliku, proba %d/5] zatrzymaj uvicorn / wstrzymaj OneDrive… czekam 3s" % attempt)
            time.sleep(3)
    return False


def main():
    args = sys.argv[1:]
    stamp = _stamp()
    rebuilt = DATA / ("schemagen.rebuilt-%s.db" % stamp)

    if "--from-bak" in args:
        bak = _newest_bak()
        if not bak:
            print("[!] brak backupu .bak-* w data/")
            return 1
        print("[bak] Odbudowa z backupu: %s" % bak.name)
        shutil.copy2(bak, rebuilt)
    else:
        src = _pick_source()
        if src is None:
            print("[!] Nie znalazlem zrodla (schemagen.db ani .old-/.corrupt-).")
            print("    Sprobuj: python tools/recover_db.py --from-bak")
            return 1
        print("[1] Zrodlo do odzyskania: %s" % src.name)
        if src == DB:
            shutil.copy2(src, DATA / ("schemagen.db.corrupt-%s" % stamp))
        for ext in ("-wal", "-shm", "-journal"):
            p = DATA / (DB.name + ext)
            if p.exists():
                try:
                    p.unlink()
                    print("    usunieto %s" % p.name)
                except OSError:
                    pass
        print("[2] Salvage (bulk + skan po rowid) ...")
        counts = _salvage(src, rebuilt)
        for t, n in counts.items():
            print("    - %s: %d wierszy" % (t, n))
        if counts.get("schematic_graph", 0) == 0:
            print("[!] Grafow (bboxy) NIE wyciagnieto z uszkodzonej bazy.")
            bak = _newest_bak()
            if bak:
                print("    Sprobuj backup: python tools/recover_db.py --from-bak  (z %s)" % bak.name)
            print("    Albo sqlite3 CLI: sqlite3 <zrodlo> \".recover\" | sqlite3 data/schemagen.new.db")

    chk = sqlite3.connect(rebuilt).execute("PRAGMA integrity_check").fetchone()[0]
    print("[3] integrity_check odbudowanej: %s" % chk)
    if chk != "ok":
        print("[!] Odbudowana baza ma problemy — NIE podmieniam. Plik: %s" % rebuilt.name)
        return 2

    if DB.exists():
        shutil.copy2(DB, DATA / ("schemagen.db.prev-%s" % stamp))
    if not _atomic_swap(rebuilt):
        print("[!] Blokada pliku. Gdy zwolnisz proces, recznie zmien nazwe '%s' na 'schemagen.db'." % rebuilt.name)
        return 3
    print("[4] Gotowe. Aktywna baza podmieniona (integralnosc ok). Uruchom uvicorn + Ctrl+F5.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
