import json
import sqlite3

conn = sqlite3.connect("data/schemagen.db")
rows = conn.execute(
    "SELECT page_id FROM annotations WHERE page_id LIKE '%p040%'"
).fetchall()
print("p040 pages", rows)
for pid, in rows:
    data = json.loads(
        conn.execute(
            "SELECT payload_json FROM annotations WHERE page_id=?", (pid,)
        ).fetchone()[0]
    )
    print(pid, "bboxes", len(data.get("bboxes", [])), "lines", len(data.get("lines", [])))
