import json
import sqlite3
from collections import defaultdict

c = sqlite3.connect("data/schemagen.db")
rows = c.execute(
    "SELECT page_id, payload_json FROM annotations ORDER BY page_id"
).fetchall()
total_bbox = 0
by_project = defaultdict(lambda: {"pages": 0, "bboxes": 0})
for pid, raw in rows:
    if pid.startswith("test"):
        continue
    n = len(json.loads(raw).get("bboxes", []))
    if n == 0:
        continue
    total_bbox += n
    if pid.startswith("SchematWRT01"):
        key = "WRT01"
    elif "Adamed_AGV" in pid:
        key = "Adamed_AGV"
    elif "229_PL5" in pid:
        key = "Stanley_229"
    else:
        key = pid.split("_p")[0]
    by_project[key]["pages"] += 1
    by_project[key]["bboxes"] += n

print(f"Stron z bbox: {sum(v['pages'] for v in by_project.values())}")
print(f"Bbox razem: {total_bbox}")
for k, v in sorted(by_project.items()):
    print(f"  {k}: {v['pages']} stron, {v['bboxes']} bbox")
