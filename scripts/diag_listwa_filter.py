"""Diagnoza brakujących linii listwy i filtra through-wires."""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT))

from backend.ingest.vector import (
    _polyline_crosses_components,
    filter_vector_through_wires,
    merge_l_corners,
    trace_vector_page,
    drop_inside_symbol_segments,
)
from backend.paths import RAW
from backend.recognize.graph_builder import GraphBuilder, _join_tol, _apply_roi, _edge_tol
from backend.recognize.line_classifier import LineClassifier
from backend.recognize.line_sieve import (
    _components_with_terminals_on_path,
    apply_sieve,
    recover_terminal_bridges,
)
from backend.recognize.terminal_resolver import resolve as resolve_terminals
from backend.recognize.mostek_terminals import load_bgr
from backend.runtime_config import roi_bottom_cut_frac, terminal_patterns
from backend.recognize.ocr_engine import PaddleOcrEngine
from backend.recognize.graph_builder import _contact_tol, _pattern_tol
from backend.models.schema import Component
from labeler.gt_loader import load_gt_schema


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

    image_bgr = load_bgr(img)
    candidate = [ln for ln in lines if LineClassifier.is_connection_candidate(ln)]
    for c in components:
        if c.terminals:
            continue
        c.terminals = resolve_terminals(
            c, candidate, image_bgr, terminal_patterns(),
            contact_tol=_contact_tol(size),
            pattern_tol=_pattern_tol(size),
            merge_tol=min(_contact_tol(size), 15.0),
        )

    merged = merge_l_corners(lines, gap_tol=corner_tol)
    filtered = filter_vector_through_wires(merged, components, tol=join_tol)

    demoted = [
        ln for ln in filtered
        if LineClassifier.is_connection_candidate(ln) is False
        and any(
            LineClassifier.is_connection_candidate(o)
            for o in merged
            if o.id == ln.id
        )
    ]
    # simpler: compare merged vs filtered wire count
    before_w = [ln for ln in merged if ln.role == "wire"]
    after_w = [ln for ln in filtered if ln.role == "wire"]
    print(f"merged wires={len(before_w)}  after filter={len(after_w)}  demoted={len(before_w)-len(after_w)}")

    # GT listwa y~2945
    for i in [0, 1, 22, 23, 24, 9, 10, 12, 13]:
        gl = gt.graphic_lines[i]
        y = gl.points[0][1]
        print(f"\ngt[{i}] y={y:.0f} pts={gl.points[0]}..{gl.points[-1]}")
        # find nearest runtime wire before filter
        best = None
        best_d = 1e9
        for ln in before_w:
            p0, p1 = ln.points[0], ln.points[-1]
            d = min(
                abs(p0[1] - y),
                abs(p1[1] - y),
                min(abs(p[1] - y) for p in ln.points),
            )
            if d < best_d:
                best_d = d
                best = ln
        if best:
            cr = _polyline_crosses_components(best, components, join_tol)
            op = _components_with_terminals_on_path(best, components, join_tol)
            kept = best in after_w
            print(
                f"  nearest dY={best_d:.1f} crosses={cr} on_path={op} kept={kept} "
                f"pts={best.points[0]}..{best.points[-1]} n={len(best.points)}"
            )
        else:
            print("  no nearby wire in merged")


if __name__ == "__main__":
    main()
