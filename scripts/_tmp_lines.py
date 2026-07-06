import json
import sqlite3
from pathlib import Path

db = sqlite3.connect(Path(__file__).resolve().parents[1] / "data" / "schemagen.db")
row = db.execute(
    "SELECT payload_json FROM schematic_graph WHERE page_id LIKE '%p027%' LIMIT 1"
).fetchone()
g = json.loads(row[0])
print("lines:", len(g["lines"]))
for line in g["lines"]:
    print(json.dumps(line, ensure_ascii=False))
    for key in ("from", "from_ref", "to", "to_ref"):
        if key in line:
            print(f"  {key}={line[key]!r} type={type(line[key]).__name__}")
