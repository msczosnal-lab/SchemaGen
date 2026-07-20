"""Pipeline stages for vector line extraction (p028)."""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT))

from backend.paths import RAW
from backend.recognize.graph_builder import GraphBuilder
from backend.validate.diff_metrics import line_metrics, page_id
from labeler.gt_loader import load_gt_schema


def main() -> None:
    pid = page_id("p028")
    img = str(RAW / f"{pid}.png")
    gt = load_gt_schema(pid)
    gb = GraphBuilder()
    schema = gb.build(img)
    rt_lines = schema.graphic_lines
    m = line_metrics(gt.graphic_lines, rt_lines, tol=8.0, step=4.0)
    print(
        f"GT={len(gt.graphic_lines)} RT={len(rt_lines)} "
        f"P={m['precision']:.3f} R={m['recall']:.3f} F1={m['f1']:.3f}"
    )
    poly = sum(1 for ln in rt_lines if len(ln.points) > 2)
    print(f"polylines (>2 pts): {poly}")


if __name__ == "__main__":
    main()
