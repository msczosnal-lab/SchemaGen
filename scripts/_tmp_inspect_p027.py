import json
import sqlite3
from pathlib import Path

db = sqlite3.connect(Path(__file__).resolve().parents[1] / "data" / "schemagen.db")
rows = db.execute("SELECT page_id FROM schematic_graph WHERE page_id LIKE '%p027%'").fetchall()
print("pages:", rows)
row = db.execute(
    "SELECT payload_json FROM schematic_graph WHERE page_id LIKE '%p027%' LIMIT 1"
).fetchone()
if not row:
    print("no graph")
    raise SystemExit
g = json.loads(row[0])
print("symbols:", len(g.get("symbols", [])))
print("lines:", len(g.get("lines", [])))
for line in g.get("lines", []):
    print(line)
    for label, ref in ("from", line.get("from")), ("to", line.get("to")):
        sid, tid = ref.split(":", 1)
        sym = next(s for s in g["symbols"] if s["id"] == sid)
        t = next((x for x in sym["terminals"] if str(x["id"]) == tid), None)
        print(f"  {label} {ref} -> term={t}, bbox={sym['bbox']}")
