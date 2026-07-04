"""Wspolne metryki diff GT vs runtime — uzywane przez diff_gt_runtime i eval_val_pages."""

from __future__ import annotations


def _norm_conn(c) -> tuple[str, str, str]:
    return (str(c.from_ref), str(c.to), str(getattr(c, "kind", "power")))


def _page_id(raw: str) -> str:
    if raw.startswith("22_"):
        return raw
    return f"22_A_153_PL_Adamed_AGV_SA2_20250706_{raw}"


def _bbox_iou(a: list[float], b: list[float]) -> float:
    if len(a) < 4 or len(b) < 4:
        return 0.0
    ix1 = max(a[0], b[0])
    iy1 = max(a[1], b[1])
    ix2 = min(a[2], b[2])
    iy2 = min(a[3], b[3])
    if ix2 <= ix1 or iy2 <= iy1:
        return 0.0
    inter = (ix2 - ix1) * (iy2 - iy1)
    area_a = (a[2] - a[0]) * (a[3] - a[1])
    area_b = (b[2] - b[0]) * (b[3] - b[1])
    union = area_a + area_b - inter
    return inter / union if union > 0 else 0.0


def _norm_tag(tag: str) -> str:
    return (tag or "").strip().upper().replace(" ", "")


def diff_connections(gt_schema, runtime) -> dict:
    gt_conns = {_norm_conn(c) for c in gt_schema.connections}
    rt_conns = {_norm_conn(c) for c in runtime.connections}
    both = gt_conns & rt_conns
    return {
        "gt_count": len(gt_conns),
        "runtime_count": len(rt_conns),
        "match": len(both),
        "only_gt": sorted(gt_conns - rt_conns),
        "only_runtime": sorted(rt_conns - gt_conns),
    }


def diff_components(gt_schema, runtime, iou_threshold: float = 0.5) -> dict:
    gt_boxes = [(c.id, c.bbox, c.type) for c in gt_schema.components]
    rt_boxes = [(c.id, c.bbox, c.type) for c in runtime.components]
    matched_gt: set[str] = set()
    matched_rt: set[str] = set()
    pairs: list[dict] = []

    for gt_id, gt_bb, gt_type in gt_boxes:
        best_iou = 0.0
        best_rt = None
        for rt_id, rt_bb, rt_type in rt_boxes:
            if rt_id in matched_rt:
                continue
            if gt_type and rt_type and gt_type != rt_type:
                continue
            iou = _bbox_iou(gt_bb, rt_bb)
            if iou > best_iou:
                best_iou = iou
                best_rt = rt_id
        if best_rt and best_iou >= iou_threshold:
            matched_gt.add(gt_id)
            matched_rt.add(best_rt)
            pairs.append({"gt": gt_id, "runtime": best_rt, "iou": round(best_iou, 3)})

    return {
        "gt_count": len(gt_boxes),
        "runtime_count": len(rt_boxes),
        "match": len(pairs),
        "pairs": pairs,
        "only_gt": [g[0] for g in gt_boxes if g[0] not in matched_gt],
        "only_runtime": [r[0] for r in rt_boxes if r[0] not in matched_rt],
    }


def diff_tags(gt_schema, runtime) -> dict:
    gt_tags = {_norm_tag(c.tag) for c in gt_schema.components if c.tag}
    rt_tags = {_norm_tag(c.tag) for c in runtime.components if c.tag}
    return {
        "gt_count": len(gt_tags),
        "runtime_count": len(rt_tags),
        "match": len(gt_tags & rt_tags),
        "only_gt": sorted(gt_tags - rt_tags),
        "only_runtime": sorted(rt_tags - gt_tags),
    }
