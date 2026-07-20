"""Diagnoza merge_l_corners — offset poziomych odcinkow."""
from __future__ import annotations

import copy
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT))

from backend.ingest.vector import merge_l_corners, trace_vector_page, drop_inside_symbol_segments
from backend.paths import RAW
from backend.recognize.graph_builder import GraphBuilder, _join_tol, _apply_roi, _edge_tol
from backend.recognize.line_classifier import LineClassifier
from backend.recognize.line_sieve import apply_sieve, recover_terminal_bridges
from backend.recognize.ocr_engine import PaddleOcrEngine
from backend.runtime_config import roi_bottom_cut_frac
from backend.models.schema import Component
from labeler.gt_loader import load_gt_schema


def near_y(lines, y: float, band: float = 80.0) -> list:
    out = []
    for ln in lines:
        if not LineClassifier.is_connection_candidate(ln):
            continue
        ys = [p[1] for p in ln.points]
        if min(abs(v - y) for v in ys) <= band:
            out.append(ln)
    return out


def show(label: str, lines) -> None:
    print(f"\n=== {label} ({len(lines)}) ===")
    for ln in lines:
        pts = ln.points
        print(
            f"  n={len(pts)} role={ln.role} "
            f"{pts[0]} -> {pts[-1]}"
            + (f" mid={pts[1]}" if len(pts) > 2 else "")
        )


def main() -> None:
    pid = "22_A_153_PL_Adamed_AGV_SA2_20250706_p028"
    img = str(RAW / f"{pid}.png")
    gt = load_gt_schema(pid)
    gb = GraphBuilder()
    size = (6617, 4678)
    join_tol = _join_tol(size)
    corner_tol = min(16.0, max(8.0, join_tol * 0.15))

    detections = gb._detect(img)
    components = [
        Component(
            id=f"sym_{i}",
            type=d.class_name,
            bbox=[d.x, d.y, d.x + d.width, d.y + d.height],
            confidence=d.confidence,
            source="yolo",
        )
        for i, d in enumerate(detections)
    ]

    segs = drop_inside_symbol_segments(
        trace_vector_page(img) or [], components, bridge_tol=join_tol
    )
    lines = gb._classify(segs, size)
    texts = PaddleOcrEngine().extract_text(img)
    lines = apply_sieve(lines, components, [t.bbox for t in texts], edge_tol=_edge_tol(size))
    lines = _apply_roi(lines, size, roi_bottom_cut_frac())
    lines = recover_terminal_bridges(lines, components, bridge_tol=join_tol)

    for y_target, idx in [(1400, 9), (1587, 10), (1597, 12), (1392, 13)]:
        gl = gt.graphic_lines[idx]
        print(f"\n######## gt[{idx}] y={gl.points[0][1]:.0f}")
        show("before merge", near_y(lines, gl.points[0][1]))
        merged = merge_l_corners(copy.deepcopy(lines), gap_tol=corner_tol)
        show("after merge", near_y(merged, gl.points[0][1]))


if __name__ == "__main__":
    main()
