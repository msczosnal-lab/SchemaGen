import json
import sqlite3
from pathlib import Path

db = sqlite3.connect(Path(__file__).resolve().parents[1] / "data" / "schemagen.db")
row = db.execute(
    "SELECT payload_json FROM schematic_graph WHERE page_id LIKE '%p027%' LIMIT 1"
).fetchone()
g = json.loads(row[0])
sym_ids = {s["id"] for s in g["symbols"]}
print("symbol ids:", sorted(sym_ids))
for line in g["lines"]:
    for label, ref in ("from", line["from"]), ("to", line["to"]):
        sid, tid = ref.split(":", 1)
        ok_sym = sid in sym_ids
        sym = next(s for s in g["symbols"] if s["id"] == sid) if ok_sym else None
        ok_term = (
            sym
            and any(str(t["id"]) == tid for t in sym.get("terminals") or [])
        )
        print(f"{line['id']} {label} {ref}: sym={ok_sym} term={ok_term}")
