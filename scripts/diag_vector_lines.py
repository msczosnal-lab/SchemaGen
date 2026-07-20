"""Diagnostyka linii wektorowych vs GT (034)."""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT))

from backend.paths import RAW
from backend.recognize.pipeline import recognize_file
from backend.validate.diff_metrics import _sample_polyline, _build_grid, _coverage, page_id
from labeler.gt_loader import load_gt_schema

pid = page_id("p028")
gt = load_gt_schema(pid)
rt = recognize_file(str(RAW / f"{pid}.png"))
tol = 8.0
step = 4.0

print(f"GT {len(gt.graphic_lines)}  RT {len(rt.graphic_lines)}")
for i, gl in enumerate(gt.graphic_lines):
    gt_pts = _sample_polyline(gl.points, step)
    grid = _build_grid(gt_pts, tol)
    best = 0.0
    for ln in rt.graphic_lines:
        rt_pts = _sample_polyline(ln.points, step)
        best = max(best, _coverage(rt_pts, grid, tol))
    flag = "OK" if best > 0.5 else "MISS"
    print(f"  gt[{i:2d}] cov={best:.2f} {flag}  pts={gl.points[0]}..{gl.points[-1]}")
