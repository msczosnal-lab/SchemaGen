"""Per-stage line counts on p028 vector path."""
from __future__ import annotations

import copy
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT))

from backend.ingest.vector import (
    drop_inside_symbol_segments,
    drop_t_stubs_at_mostek,
    filter_vector_through_wires,
    merge_l_corners,
    trace_vector_page,
)
from backend.paths import RAW
from backend.recognize.graph_builder import (
    GraphBuilder,
    _apply_roi,
    _join_tol,
)
from backend.recognize.line_classifier import LineClassifier
from backend.recognize.line_sieve import apply_sieve, recover_terminal_bridges
from backend.validate.diff_metrics import _lines_prf, page_id
from labeler.gt_loader import load_gt_schema


def prf(label: str, lines, gt_lines) -> None:
    m = _lines_prf(gt_lines, lines, 8.0)
    wires = sum(1 for ln in lines if LineClassifier.is_connection_candidate(ln))
    poly = sum(1 for ln in lines if len(ln.points) > 2)
    print(
        f"{label:28s} n={len(lines):3d} wire={wires:3d} poly={poly:3d} "
        f"P={m['precision']:.3f} R={m['recall']:.3f} F1={m['f1']:.3f}"
    )


def main() -> None:
    pid = page_id("p028")
    img = str(RAW / f"{pid}.png")
    gt = load_gt_schema(pid)
    gt_lines = gt.graphic_lines
    gb = GraphBuilder()
    size = (6617, 4678)  # p028 known
  # build components like graph_builder
    from backend.recognize.graph_builder import GraphBuilder as GB

    builder = GB()
    detections = builder._detect(img)
    from backend.models.schema import Component

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
    join_tol = _join_tol(size)

    segs = trace_vector_page(img)
    segs2 = drop_inside_symbol_segments(segs or [], components, bridge_tol=join_tol)
    lines = builder._classify(segs2, size)
    prf("after classify", lines, gt_lines)

    from backend.recognize.ocr_engine import PaddleOcrEngine

    texts = PaddleOcrEngine().extract_text(img)
    from backend.recognize.graph_builder import _edge_tol

    lines = apply_sieve(
        lines, components, [t.bbox for t in texts], edge_tol=_edge_tol(size)
    )
    prf("after sieve", lines, gt_lines)

    from backend.runtime_config import roi_bottom_cut_frac

    lines = _apply_roi(lines, size, roi_bottom_cut_frac())
    prf("after roi", lines, gt_lines)

    lines = recover_terminal_bridges(lines, components, bridge_tol=join_tol)
    prf("after bridges", lines, gt_lines)

    from backend.recognize.terminal_resolver import resolve as resolve_terminals
    from backend.recognize.graph_builder import _pattern_tol, _contact_tol
    from backend.recognize.mostek_terminals import load_bgr
    from backend.runtime_config import terminal_patterns

    image_bgr = load_bgr(img)
    contact_tol = _contact_tol(size)
    pattern_tol = _pattern_tol(size)
    merge_tol = min(contact_tol, 15.0)
    patterns = terminal_patterns()
    from backend.recognize.line_classifier import LineClassifier as LC

    candidate_lines = [
        ln for ln in lines if LC.is_connection_candidate(ln)
    ]
    for c in components:
        if c.terminals:
            continue
        c.terminals = resolve_terminals(
            c, candidate_lines, image_bgr, patterns,
            contact_tol=contact_tol, pattern_tol=pattern_tol, merge_tol=merge_tol,
        )
    prf("after terminals", lines, gt_lines)

    lines2 = drop_t_stubs_at_mostek(copy.deepcopy(lines), components, tol=join_tol)
    prf("after T-drop", lines2, gt_lines)

    corner_tol = min(16.0, max(8.0, join_tol * 0.15))
    lines3 = merge_l_corners(copy.deepcopy(lines2), gap_tol=corner_tol)
    prf("after L-merge", lines3, gt_lines)

    lines4 = filter_vector_through_wires(
        copy.deepcopy(lines3), components, tol=join_tol
    )
    prf("after through-filter", lines4, gt_lines)

    lines5 = [ln for ln in lines4 if ln.role == "wire"]
    prf("wire-only (no merge_collinear)", lines5, gt_lines)

    lines_nf = filter_vector_through_wires(
        merge_l_corners(copy.deepcopy(lines), gap_tol=corner_tol),
        components,
        tol=join_tol,
    )
    prf("L+filter, no T-drop", [ln for ln in lines_nf if ln.role == "wire"], gt_lines)

    from backend.recognize.line_sieve import merge_collinear_wires

    wonly = [ln for ln in lines_nf if ln.role == "wire"]
    two_pt = [ln for ln in wonly if len(ln.points) == 2]
    poly = [ln for ln in wonly if len(ln.points) > 2]
    merged2 = merge_collinear_wires(
        two_pt, gap_tol=join_tol * 2.0, perp_tol=max(6.0, join_tol * 0.5)
    )
    prf("L+filter+merge2pt", merged2 + poly, gt_lines)

    # stricter through-filter variant
    from backend.ingest.vector import _polyline_crosses_components
    from backend.recognize.line_sieve import _components_with_terminals_on_path, _containing_component
    from backend.recognize.line_classifier import LineClassifier

    strict = []
    for ln in merge_l_corners(copy.deepcopy(lines), gap_tol=corner_tol):
        if not LineClassifier.is_connection_candidate(ln):
            continue
        inside = _containing_component(ln, components, 2.0)
        if inside is not None and "mostek" not in str(inside.type).lower():
            continue
        cr = _polyline_crosses_components(ln, components, join_tol)
        op = _components_with_terminals_on_path(ln, components, join_tol)
        if cr >= 2 or op >= 1:
            strict.append(ln)
    prf("strict cross>=2|on_path", strict, gt_lines)


if __name__ == "__main__":
    main()
