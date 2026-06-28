"""Temporary: test derive_auto_terminals on real GT."""
import json
import sqlite3

from backend.models.schema import Component, GraphicLine
from backend.recognize.net_builder import derive_auto_terminals

conn = sqlite3.connect("data/schemagen.db")
pid = "22_A_153_PL_Adamed_AGV_SA2_20250706_p027"
row = conn.execute(
    "SELECT payload_json FROM annotations WHERE page_id=?", (pid,)
).fetchone()
data = json.loads(row[0])
lines = [
    GraphicLine(id=str(i), points=ln["points"], role=ln.get("role", "wire"))
    for i, ln in enumerate(data["lines"])
]
img_max = max(data.get("image_width", 4000), data.get("image_height", 3000))
tol = max(12, 0.012 * img_max)
print("tol", tol, "lines", len(lines))
zeros = 0
with_terms = 0
for b in data["bboxes"]:
    if not (b.get("tag") or "").strip():
        continue
    comp = Component(
        id=b["id"],
        type="x",
        bbox=[b["x"], b["y"], b["x"] + b["width"], b["y"] + b["height"]],
    )
    terms = derive_auto_terminals(comp, lines, tol)
    if terms:
        with_terms += 1
        tag = (b.get("tag") or "")[:30]
        print(f"  {tag:30} -> {len(terms)} terms")
    else:
        zeros += 1
print("tagged bboxes: with_terms", with_terms, "zeros", zeros)
