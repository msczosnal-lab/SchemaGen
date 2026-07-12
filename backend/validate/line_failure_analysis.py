"""Analiza powodu pudła per linia GT (draft vs GT v2)."""

from __future__ import annotations

from collections import Counter
from types import SimpleNamespace

from backend.validate.diff_metrics import (
    _build_terminal_remap,
    _infer_page_size,
    _norm_graph_line_key,
    _parse_ref,
    _remap_conn_ref,
    _terminal_match_tol,
    pair_components,
)


def _graph_line_context(gt_graph, draft_graph, iou_threshold: float = 0.5) -> dict:
    gt_adapt = SimpleNamespace(components=list(gt_graph.symbols))
    draft_adapt = SimpleNamespace(components=list(draft_graph.symbols))
    pairing = pair_components(gt_adapt, draft_adapt, iou_threshold=iou_threshold)
    rt_to_gt = pairing["rt_to_gt"]
    gt_to_rt = pairing["gt_to_rt"]
    gt_by_id = {s.id: s for s in gt_graph.symbols}
    draft_by_id = {s.id: s for s in draft_graph.symbols}
    tol = _terminal_match_tol(_infer_page_size(gt_adapt, draft_adapt))
    terminal_remaps: dict[str, dict[str, str]] = {
        rt_id: _build_terminal_remap(gt_by_id[gt_id], draft_by_id[rt_id], tol)
        for rt_id, gt_id in rt_to_gt.items()
    }

    draft_keys_by_kind: dict[tuple[str, str, str], set[str]] = {}
    draft_keys_any_kind: set[tuple[str, str]] = set()
    for ln in draft_graph.lines:
        f = _remap_conn_ref(ln.from_ref, rt_to_gt, terminal_remaps, gt_by_id)
        t = _remap_conn_ref(ln.to, rt_to_gt, terminal_remaps, gt_by_id)
        if f is None or t is None:
            continue
        key = _norm_graph_line_key(f, t, ln.kind)
        draft_keys_by_kind.setdefault(key, set()).add(ln.id)
        draft_keys_any_kind.add(tuple(sorted([f, t])))

    matched_keys = {
        _norm_graph_line_key(ln.from_ref, ln.to, ln.kind)
        for ln in gt_graph.lines
        if _norm_graph_line_key(ln.from_ref, ln.to, ln.kind) in draft_keys_by_kind
    }

    return {
        "pairing": pairing,
        "gt_to_rt": gt_to_rt,
        "rt_to_gt": rt_to_gt,
        "gt_by_id": gt_by_id,
        "draft_by_id": draft_by_id,
        "terminal_remaps": terminal_remaps,
        "draft_keys_by_kind": draft_keys_by_kind,
        "draft_keys_any_kind": draft_keys_any_kind,
        "matched_keys": matched_keys,
    }


def _endpoint_status(
    gt_ref: str,
    ctx: dict,
) -> tuple[str, str | None]:
    """Zwraca (reason_code, draft_ref) — reason pusty gdy OK."""
    sym_id, term_id = _parse_ref(gt_ref)
    gt_to_rt = ctx["gt_to_rt"]
    gt_by_id = ctx["gt_by_id"]
    draft_by_id = ctx["draft_by_id"]
    terminal_remaps = ctx["terminal_remaps"]

    if sym_id not in gt_by_id:
        return "symbol_unknown", None
    if sym_id not in gt_to_rt:
        return "symbol_missing", None

    rt_sym = gt_to_rt[sym_id]
    if rt_sym not in draft_by_id:
        return "symbol_missing", None

    if term_id is None:
        return "", gt_ref

    gt_comp = gt_by_id[sym_id]
    if not any(t.id == term_id for t in gt_comp.terminals):
        return "terminal_unknown", None

    tmap = terminal_remaps.get(rt_sym, {})
    if term_id in tmap:
        return "", f"{rt_sym}:{tmap[term_id]}"
    if any(t.id == term_id for t in draft_by_id[rt_sym].terminals):
        return "", f"{rt_sym}:{term_id}"
    return "terminal_remap_failed", None


def classify_gt_line_failure(ln, ctx: dict) -> dict:
    """Powód pudła dla jednej linii GT."""
    key = _norm_graph_line_key(ln.from_ref, ln.to, ln.kind)
    if key in ctx["matched_keys"]:
        return {
            "line_id": ln.id,
            "from": ln.from_ref,
            "to": ln.to,
            "kind": ln.kind,
            "status": "matched",
            "reason": "matched",
        }

    r_from, draft_from = _endpoint_status(ln.from_ref, ctx)
    r_to, draft_to = _endpoint_status(ln.to, ctx)

    if r_from == "symbol_missing":
        reason = "symbol_missing_from"
    elif r_to == "symbol_missing":
        reason = "symbol_missing_to"
    elif r_from == "terminal_remap_failed":
        reason = "terminal_remap_failed_from"
    elif r_to == "terminal_remap_failed":
        reason = "terminal_remap_failed_to"
    elif r_from or r_to:
        reason = "endpoint_error"
    elif draft_from and draft_to:
        pair = tuple(sorted([draft_from, draft_to]))
        if pair in ctx["draft_keys_any_kind"]:
            reason = "kind_mismatch"
        else:
            reason = "topology_mismatch"
    else:
        reason = "topology_mismatch"

    return {
        "line_id": ln.id,
        "from": ln.from_ref,
        "to": ln.to,
        "kind": ln.kind,
        "status": "miss",
        "reason": reason,
        "draft_from": draft_from,
        "draft_to": draft_to,
    }


def analyze_line_failures(
    gt_graph,
    draft_graph,
    iou_threshold: float = 0.5,
) -> dict:
    """Raport per linia GT + agregat powodów pudła."""
    ctx = _graph_line_context(gt_graph, draft_graph, iou_threshold=iou_threshold)
    lines_out: list[dict] = []
    reasons = Counter()

    for ln in gt_graph.lines:
        row = classify_gt_line_failure(ln, ctx)
        lines_out.append(row)
        if row["status"] == "miss":
            reasons[row["reason"]] += 1

    total = len(gt_graph.lines)
    matched = sum(1 for r in lines_out if r["status"] == "matched")
    return {
        "gt_count": total,
        "matched": matched,
        "missed": total - matched,
        "reason_counts": dict(reasons.most_common()),
        "lines": lines_out,
    }
