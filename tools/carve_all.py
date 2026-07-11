"""Skanuje WSZYSTKIE pliki data/schemagen* (w tym -wal) i pokazuje, gdzie jest
najbogatszy p028/p029. Zapisuje najlepsze wersje do data/schemagen.best.db.

  python tools/carve_all.py
"""
from __future__ import annotations

import glob
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import tools.carve_graphs as cg  # noqa: E402


def _carve_wal(path):
    """Plik -wal: 32-bajtowy naglowek + ramki (24B naglowek + strona)."""
    data = Path(path).read_bytes()
    if len(data) < 32:
        return {}
    ps = int.from_bytes(data[8:12], "big")  # page size w naglowku WAL
    if ps in (0, 1):
        ps = 4096
    found = {}
    off = 32
    frames = b""
    while off + 24 + ps <= len(data):
        frames += data[off + 24: off + 24 + ps]
        off += 24 + ps
    # potraktuj sklejone strony jak plik-bazy przez tymczasowy zapis
    tmp = Path(str(path) + ".frames.tmp")
    tmp.write_bytes(data[:100] + frames if len(data) >= 100 else frames)
    try:
        found = cg.carve(str(tmp))
    except Exception:
        found = {}
    finally:
        try:
            tmp.unlink()
        except OSError:
            pass
    return found


def main():
    best = {}
    files = sorted(glob.glob(str(ROOT / "data" / "schemagen*")))
    for f in files:
        if f.endswith((".sql", ".tmp", ".best.db")):
            continue
        try:
            found = _carve_wal(f) if f.endswith("-wal") else cg.carve(f)
        except Exception as exc:  # noqa: BLE001
            print("%-48s blad: %s" % (Path(f).name, exc))
            continue
        if not found:
            print("%-48s -" % Path(f).name)
            continue
        summ = ", ".join("%s=%d" % (pid.split("_")[-1], v[1]) for pid, v in sorted(found.items()))
        print("%-48s %s" % (Path(f).name, summ))
        for pid, (payload, nsym, nlin) in found.items():
            if pid not in best or nsym > best[pid][1]:
                best[pid] = (payload, nsym, nlin)

    if not best:
        print("\n[WYNIK] Nigdzie nie ma zadnego grafu v2 — p028 do przeetykietowania.")
        return 1
    print("\n[NAJLEPSZE]")
    for pid, (_p, ns, nl) in sorted(best.items()):
        print("  %s : symboli=%d linii=%d" % (pid, ns, nl))

    import datetime
    import sqlite3
    import backend.db as dbm
    import backend.paths as pm
    out = ROOT / "data" / "schemagen.best.db"
    dbm.DB_PATH = out
    pm.DB_PATH = out
    if out.exists():
        out.unlink()
    dbm.init_db()
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()
    c = sqlite3.connect(out)
    for pid, (payload, _s, _l) in best.items():
        c.execute("INSERT OR REPLACE INTO schematic_graph (page_id, payload_json, updated_at) VALUES (?,?,?)",
                  (pid, payload, now))
    c.commit()
    c.close()
    print("\n[OK] Najlepsze wersje zapisane do data/schemagen.best.db")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
