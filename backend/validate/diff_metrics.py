"""Wspolne metryki diff GT vs runtime — uzywane przez skrypty eval/diff."""

from __future__ import annotations

import math

from backend.paths import resolve_page_id as page_id

#: warstwy wchodzace do aggregate_score
SCORE_LAYERS = ("components", "lines", "connections", "tags")


def _prf(match: int, gt: int, rt: int) -> dict:
    """Precision/recall/f1 z licznikow match/gt/rt."""
    precision = match / rt if rt else 0.0
    recall = match / gt if gt else 0.0
    f1 = (
        2 * precision * recall / (precision + recall)
        if (precision + recall) > 0
        else 0.0
    )
    return {
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1": round(f1, 4),
    }


def _norm_conn(c) -> tuple[str, str, str]:
    return (str(c.from_ref), str(c.to), str(getattr(c, "kind", "power")))


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
    out = {
        "gt_count": len(gt_conns),
        "runtime_count": len(rt_conns),
        "match": len(both),
        "only_gt": sorted(gt_conns - rt_conns),
        "only_runtime": sorted(rt_conns - gt_conns),
    }
    out.update(_prf(len(both), len(gt_conns), len(rt_conns)))
    return out


def _sample_polyline(points: list[list[float]], step: float) -> list[tuple[float, float]]:
    """Probkuje polilinie co ~step px (wierzcholki zawsze wlaczone)."""
    if not points:
        return []
    pts = [(float(p[0]), float(p[1])) for p in points if len(p) >= 2]
    if len(pts) == 1:
        return pts
    out: list[tuple[float, float]] = []
    for (x1, y1), (x2, y2) in zip(pts, pts[1:]):
        seg_len = math.hypot(x2 - x1, y2 - y1)
        n = max(1, int(seg_len / step))
        for i in range(n):
            t = i / n
            out.append((x1 + (x2 - x1) * t, y1 + (y2 - y1) * t))
    out.append(pts[-1])
    return out


def _coverage(
    src: list[tuple[float, float]],
    grid: dict[tuple[int, int], list[tuple[float, float]]],
    tol: float,
) -> float:
    """Ulamek punktow src majacych sasiada w gridzie w odleglosci <= tol."""
    if not src:
        return 0.0
    tol2 = tol * tol
    hit = 0
    for x, y in src:
        cx, cy = int(x // tol), int(y // tol)
        found = False
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                for px, py in grid.get((cx + dx, cy + dy), ()):
                    if (px - x) ** 2 + (py - y) ** 2 <= tol2:
                        found = True
                        break
                if found:
                    break
            if found:
                break
        if found:
            hit += 1
    return hit / len(src)


def _build_grid(
    pts: list[tuple[float, float]], tol: float
) -> dict[tuple[int, int], list[tuple[float, float]]]:
    grid: dict[tuple[int, int], list[tuple[float, float]]] = {}
    for x, y in pts:
        grid.setdefault((int(x // tol), int(y // tol)), []).append((x, y))
    return grid


def _lines_prf(gt_lines, rt_lines, tol: float) -> dict:
    step = max(2.0, tol / 2.0)
    gt_pts = [p for ln in gt_lines for p in _sample_polyline(ln.points, step)]
    rt_pts = [p for ln in rt_lines for p in _sample_polyline(ln.points, step)]
    recall = _coverage(gt_pts, _build_grid(rt_pts, tol), tol) if gt_pts else 0.0
    precision = _coverage(rt_pts, _build_grid(gt_pts, tol), tol) if rt_pts else 0.0
    f1 = (
        2 * precision * recall / (precision + recall)
        if (precision + recall) > 0
        else 0.0
    )
    return {
        "gt_count": len(gt_lines),
        "runtime_count": len(rt_lines),
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1": round(f1, 4),
    }


def diff_lines(gt_schema, runtime, tol: float = 8.0) -> dict:
    """Geometryczne porownanie linii: pokrycie punktow w odleglosci <= tol.

    recall = % probkowanych punktow GT lezacych blisko linii runtime,
    precision = odwrotnie. Nie IoU bboxa — polilinie.
    """
    gt_lines = list(gt_schema.graphic_lines)
    rt_lines = list(runtime.graphic_lines)
    out = _lines_prf(gt_lines, rt_lines, tol)
    out["tol"] = tol

    roles = sorted(
        {ln.role for ln in gt_lines} | {ln.role for ln in rt_lines}
    )
    per_role: dict[str, dict] = {}
    for role in roles:
        per_role[str(role)] = _lines_prf(
            [ln for ln in gt_lines if ln.role == role],
            [ln for ln in rt_lines if ln.role == role],
            tol,
        )
    out["per_role"] = per_role
    return out


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

    out = {
        "gt_count": len(gt_boxes),
        "runtime_count": len(rt_boxes),
        "match": len(pairs),
        "pairs": pairs,
        "only_gt": [g[0] for g in gt_boxes if g[0] not in matched_gt],
        "only_runtime": [r[0] for r in rt_boxes if r[0] not in matched_rt],
    }
    out.update(_prf(len(pairs), len(gt_boxes), len(rt_boxes)))

    # per klasa: liczniki na typie GT (match przypisany do typu gt)
    gt_by_type: dict[str, int] = {}
    rt_by_type: dict[str, int] = {}
    match_by_type: dict[str, int] = {}
    for _gid, _bb, typ in gt_boxes:
        gt_by_type[typ or ""] = gt_by_type.get(typ or "", 0) + 1
    for _rid, _bb, typ in rt_boxes:
        rt_by_type[typ or ""] = rt_by_type.get(typ or "", 0) + 1
    gt_type_by_id = {gid: (typ or "") for gid, _bb, typ in gt_boxes}
    for pair in pairs:
        typ = gt_type_by_id.get(pair["gt"], "")
        match_by_type[typ] = match_by_type.get(typ, 0) + 1

    per_class: dict[str, dict] = {}
    for typ in sorted(set(gt_by_type) | set(rt_by_type)):
        g = gt_by_type.get(typ, 0)
        r = rt_by_type.get(typ, 0)
        m = match_by_type.get(typ, 0)
        per_class[typ] = {"gt": g, "rt": r, "match": m, **_prf(m, g, r)}
    out["per_class"] = per_class

    # klasy obecne w GT, ktorych runtime w ogole nie trafil — strata modelu
    # (retrain YOLO), nie kodu; raportowane oddzielnie
    out["model_gaps"] = [
        typ for typ, d in per_class.items() if d["gt"] > 0 and d["match"] == 0
    ]
    return out


def diff_tags(gt_schema, runtime) -> dict:
    gt_tags = {_norm_tag(c.tag) for c in gt_schema.components if c.tag}
    rt_tags = {_norm_tag(c.tag) for c in runtime.components if c.tag}
    out = {
        "gt_count": len(gt_tags),
        "runtime_count": len(rt_tags),
        "match": len(gt_tags & rt_tags),
        "only_gt": sorted(gt_tags - rt_tags),
        "only_runtime": sorted(rt_tags - gt_tags),
    }
    out.update(_prf(len(gt_tags & rt_tags), len(gt_tags), len(rt_tags)))
    return out


def aggregate_score(report: dict, weights: dict) -> dict:
    """Skalar 0-100: wazona suma f1 warstw components/lines/connections/tags.

    Warstwa bez GT (gt_count=0) jest wylaczana, wagi renormalizowane.
    ``report`` = dict z kluczami warstw (wyniki diff_*), ``weights`` =
    ``eval_weights`` z config/eval-weights.yaml.
    """
    active: dict[str, dict] = {}
    for layer in SCORE_LAYERS:
        d = report.get(layer)
        if not d or d.get("gt_count", 0) <= 0:
            continue
        w = float(weights.get(layer, 0.0))
        if w <= 0:
            continue
        active[layer] = {"f1": float(d.get("f1", 0.0)), "weight": w}

    total_w = sum(v["weight"] for v in active.values())
    per_layer: dict[str, dict] = {}
    score = 0.0
    for layer, v in active.items():
        w_norm = v["weight"] / total_w if total_w > 0 else 0.0
        contribution = 100.0 * w_norm * v["f1"]
        score += contribution
        per_layer[layer] = {
            "f1": round(v["f1"], 4),
            "weight": round(w_norm, 4),
            "contribution": round(contribution, 2),
        }
    return {"score": round(score, 2), "per_layer": per_layer}
