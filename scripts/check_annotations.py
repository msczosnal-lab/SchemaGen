import json
import sqlite3
from pathlib import Path

db = Path("data/schemagen.db")
if not db.exists():
    print("NO DB")
    raise SystemExit(0)

c = sqlite3.connect(db)
rows = c.execute(
    "SELECT page_id, length(payload_json), updated_at FROM annotations ORDER BY updated_at DESC"
).fetchall()
print(f"annotations in DB: {len(rows)}")
for r in rows[:20]:
    print(r)

for page_id, payload_len, updated in rows[:5]:
    raw = c.execute("SELECT payload_json FROM annotations WHERE page_id=?", (page_id,)).fetchone()[0]
    data = json.loads(raw)
    print(f"  {page_id}: {len(data.get('bboxes', []))} bboxes, updated {updated}")

labeled = c.execute("SELECT id, status FROM pages WHERE status='labeled'").fetchall()
print(f"labeled pages: {len(labeled)}")
for x in labeled[:10]:
    print(" ", x)
