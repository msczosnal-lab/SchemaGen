"""Ile symboli/linii ma kazdy graf. Read-only.

  python tools/inspect_graph.py                 # data/schemagen.db
  python tools/inspect_graph.py <sciezka.db>    # dowolny plik
"""
import json
import sqlite3
import sys

path = sys.argv[1] if len(sys.argv) > 1 else "data/schemagen.db"
c = sqlite3.connect("file:%s?mode=ro" % path, uri=True)
try:
    rows = c.execute("SELECT page_id, payload_json FROM schematic_graph ORDER BY page_id").fetchall()
except sqlite3.DatabaseError as exc:
    print("blad odczytu schematic_graph: %s" % exc)
    rows = []
if not rows:
    print("BRAK grafow (lub tabela nieczytelna) w %s" % path)
for page_id, payload in rows:
    try:
        g = json.loads(payload)
        print("%s : symboli=%d linii=%d (bytes=%d)" % (
            page_id, len(g.get("symbols", [])), len(g.get("lines", [])), len(payload)))
    except Exception as exc:  # noqa: BLE001
        print("%s : blad JSON %s (bytes=%d)" % (page_id, exc, len(payload)))
