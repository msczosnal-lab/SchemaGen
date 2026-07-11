"""Ile symboli/linii ma kazdy graf w bazie. Read-only."""
import json
import sqlite3

c = sqlite3.connect("file:data/schemagen.db?mode=ro", uri=True)
rows = c.execute("SELECT page_id, payload_json FROM schematic_graph ORDER BY page_id").fetchall()
if not rows:
    print("BRAK grafow w schematic_graph")
for page_id, payload in rows:
    try:
        g = json.loads(payload)
        print("%s : symboli=%d linii=%d  (bytes=%d)" % (
            page_id, len(g.get("symbols", [])), len(g.get("lines", [])), len(payload)))
    except Exception as exc:  # noqa: BLE001
        print("%s : blad JSON %s (bytes=%d)" % (page_id, exc, len(payload)))
