from backend.db import load_annotation
from backend.models.label import LabelRecord
from backend.paths import resolve_page_id
from backend.recognize.pipeline import recognize_file
from backend.runtime_config import line_match_tol
from labeler.export import label_to_schema
from backend.validate.diff_metrics import _sample_polyline, _coverage, _build_grid

pid = resolve_page_id("p027")
gt = label_to_schema(LabelRecord.model_validate(load_annotation(pid)))
rt = recognize_file(f"data/raw/{pid}.png")
tol = line_match_tol()
step = max(2.0, tol / 2.0)
rt_pts = [p for ln in rt.graphic_lines for p in _sample_polyline(ln.points, step)]
grid = _build_grid(rt_pts, tol)
for ln in gt.graphic_lines:
    if ln.role == "bus":
        pts = _sample_polyline(ln.points, step)
        cov = _coverage(pts, grid, tol)
        print("GT bus", ln.id, "coverage", round(cov, 3))

low = []
for ln in gt.graphic_lines:
    if ln.role != "wire":
        continue
    pts = _sample_polyline(ln.points, step)
    cov = _coverage(pts, grid, tol)
    if cov < 0.5:
        xs = [p[0] for p in ln.points]
        ys = [p[1] for p in ln.points]
        low.append((cov, ln.id, min(xs), max(xs), min(ys), max(ys)))
low.sort()
print("worst wire GT lines (<0.5 cov):", len(low))
for row in low[:10]:
    print(" ", [round(x, 3) if isinstance(x, float) else x for x in row])

near = [
    ln
    for ln in rt.graphic_lines
    if ln.role == "wire" and any(2940 < p[1] < 2960 for p in ln.points)
]
print("RT wire near y2945:", len(near))
