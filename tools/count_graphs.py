"""Ile grafow (bboxow) siedzi w kazdym pliku bazy w data/. Read-only."""
import glob
import sqlite3

for f in sorted(glob.glob("data/schemagen*.db*")):
    try:
        c = sqlite3.connect("file:%s?mode=ro" % f, uri=True)
        try:
            n = c.execute("SELECT count(*) FROM schematic_graph").fetchone()[0]
        except sqlite3.DatabaseError:
            # tabela nieczytelna hurtem — policz skanem po rowid
            n = 0
            for rid in range(1, 200000):
                try:
                    r = c.execute("SELECT 1 FROM schematic_graph WHERE rowid=?", (rid,)).fetchone()
                except sqlite3.DatabaseError:
                    continue
                if r:
                    n += 1
            n = "%d (skan)" % n
        print("%-45s grafy=%s" % (f, n))
    except Exception as exc:  # noqa: BLE001
        print("%-45s BLAD: %s" % (f, exc))
