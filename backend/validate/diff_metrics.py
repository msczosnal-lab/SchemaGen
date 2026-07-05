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


def _parse_ref(ref: str) -> tuple[str, str | None]:
    if ":" in ref:
        sym, tid = ref.split(":", 1)
        return sym, tid
    return ref, None


def _terminal_abs_xy(comp, term) -> tuple[float, float]:
    if len(comp.bbox) < 4:
        return (0.0, 0.0)
    x1, y1, x2, y2 = comp.bbox[:4]
    return (x1 + term.x * (x2 - x1), y1 + term.y * (y2 - y1))


def _infer_page_size(gt_schema, runtime) -> tuple[int, int]:
    max_x = max_y = 0.0
    for c in list(gt_schema.components) + list(runtime.components):
        if len(c.bbox) >= 4:
            max_x = max(max_x, float(c.bbox[2]))
            max_y = max(max_y, float(c.bbox[3]))
    return (max(1, int(max_x)), max(1, int(max_y)))


def _terminal_match_tol(size: tuple[int, int]) -> float:
    """Tolerancja dopasowania terminali GT↔runtime (pattern_tol z runtime.yaml)."""
    try:
        from backend.runtime_config import (
            terminal_tol_pattern_frac,
            terminal_tol_pattern_min,
        )

        frac = terminal_tol_pattern_frac()
        tmin = terminal_tol_pattern_min()
    except Exception:
        frac, tmin = 0.008, 8.0
    w, h = size
    return max(tmin, frac * max(w, h))


def pair_components(
    gt_schema,
    runtime,
    iou_threshold: float = 0.5,
) -> dict:
    """Parowanie komponentow GT↔runtime po IoU bbox (greedy malejaco, 1:1)."""
    gt_boxes = [(c.id, c.bbox, c.type) for c in gt_schema.components]
    rt_boxes = [(c.id, c.bbox, c.type) for c in runtime.components]

    candidates: list[tuple[float, str, str]] = []
    for gt_id, gt_bb, gt_type in gt_boxes:
        for rt_id, rt_bb, rt_type in rt_boxes:
            if gt_type and rt_type and gt_type != rt_type:
                continue
            iou = _bbox_iou(gt_bb, rt_bb)
            if iou >= iou_threshold:
                candidates.append((iou, gt_id, rt_id))

    candidates.sort(key=lambda x: -x[0])
    matched_gt: set[str] = set()
    matched_rt: set[str] = set()
    rt_to_gt: dict[str, str] = {}
    pairs: list[dict] = []

    for iou, gt_id, rt_id in candidates:
        if gt_id in matched_gt or rt_id in matched_rt:
            continue
        matched_gt.add(gt_id)
        matched_rt.add(rt_id)
        rt_to_gt[rt_id] = gt_id
        pairs.append({"gt": gt_id, "runtime": rt_id, "iou": round(iou, 3)})

    return {
        "rt_to_gt": rt_to_gt,
        "gt_to_rt": {gt: rt for rt, gt in rt_to_gt.items()},
        "pairs": pairs,
        "matched_gt": matched_gt,
        "matched_rt": matched_rt,
        "only_gt": [g[0] for g in gt_boxes if g[0] not in matched_gt],
        "only_runtime": [r[0] for r in rt_boxes if r[0] not in matched_rt],
    }


def _build_terminal_remap(gt_comp, rt_comp, tol: float) -> dict[str, str]:
    """Mapuje id terminala runtime -> id terminala GT po pozycji absolutnej."""
    candidates: list[tuple[float, str, str]] = []
    for rt_t in rt_comp.terminals:
        rt_xy = _terminal_abs_xy(rt_comp, rt_t)
        for gt_t in gt_comp.terminals:
            gt_xy = _terminal_abs_xy(gt_comp, gt_t)
            dist = math.hypot(rt_xy[0] - gt_xy[0], rt_xy[1] - gt_xy[1])
            if dist <= tol:
                candidates.append((dist, rt_t.id, gt_t.id))

    candidates.sort(key=lambda x: x[0])
    used_gt: set[str] = set()
    used_rt: set[str] = set()
    remap: dict[str, str] = {}
    for _dist, rt_id, gt_id in candidates:
        if rt_id in used_rt or gt_id in used_gt:
            continue
        used_rt.add(rt_id)
        used_gt.add(gt_id)
        remap[rt_id] = gt_id
    return remap


def _remap_conn_ref(
    ref: str,
    rt_to_gt: dict[str, str],
    terminal_remaps: dict[str, dict[str, str]],
    gt_by_id: dict,
) -> str | None:
    sym_id, term_id = _parse_ref(ref)
    if sym_id in rt_to_gt:
        gt_sym = rt_to_gt[sym_id]
        if term_id is None:
            return gt_sym
        tmap = terminal_remaps.get(sym_id, {})
        if term_id in tmap:
            return f"{gt_sym}:{tmap[term_id]}"
        gt_comp = gt_by_id.get(gt_sym)
        if gt_comp and any(t.id == term_id for t in gt_comp.terminals):
            return f"{gt_sym}:{term_id}"
        return None
    if sym_id in gt_by_id:
        gt_sym = sym_id
        if term_id is None:
            return gt_sym
        gt_comp = gt_by_id[gt_sym]
        if any(t.id == term_id for t in gt_comp.terminals):
            return f"{gt_sym}:{term_id}"
        return None
    if not rt_to_gt and term_id is None:
        return ref
    return None


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


def diff_connections(
    gt_schema,
    runtime,
    iou_threshold: float = 0.5,
    terminal_tol: float | None = None,
) -> dict:
    """Porownanie connections po remapie id symboli (IoU) i terminali (pozycja)."""
    pairing = pair_components(gt_schema, runtime, iou_threshold=iou_threshold)
    rt_to_gt = pairing["rt_to_gt"]
    gt_by_id = {c.id: c for c in gt_schema.components}
    rt_by_id = {c.id: c for c in runtime.components}

    if terminal_tol is None:
        terminal_tol = _terminal_match_tol(_infer_page_size(gt_schema, runtime))

    terminal_remaps: dict[str, dict[str, str]] = {}
    for rt_id, gt_id in rt_to_gt.items():
        terminal_remaps[rt_id] = _build_terminal_remap(
            gt_by_id[gt_id], rt_by_id[rt_id], terminal_tol
        )

    gt_conns = {_norm_conn(c) for c in gt_schema.connections}
    rt_remapped: set[tuple[str, str, str]] = set()
    rt_only: set[tuple[str, str, str]] = set()
    for c in runtime.connections:
        raw = _norm_conn(c)
        from_gt = _remap_conn_ref(
            raw[0], rt_to_gt, terminal_remaps, gt_by_id
        )
        to_gt = _remap_conn_ref(raw[1], rt_to_gt, terminal_remaps, gt_by_id)
        if from_gt is None or to_gt is None:
            rt_only.add(raw)
            continue
        remapped = (from_gt, to_gt, raw[2])
        rt_remapped.add(remapped)
        if remapped not in gt_conns:
            rt_only.add(remapped)

    both = gt_conns & rt_remapped
    out = {
        "gt_count": len(gt_conns),
        "runtime_count": len(runtime.connections),
        "match": len(both),
        "only_gt": sorted(gt_conns - rt_remapped),
        "only_runtime": sorted(rt_only),
    }
    out.update(_prf(len(both), len(gt_conns), len(runtime.connections)))
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
    pairing = pair_components(gt_schema, runtime, iou_threshold=iou_threshold)
    pairs = pairing["pairs"]
    matched_gt = pairing["matched_gt"]
    matched_rt = pairing["matched_rt"]

    out = {
        "gt_count": len(gt_boxes),
        "runtime_count": len(rt_boxes),
        "match": len(pairs),
        "pairs": pairs,
        "only_gt": pairing["only_gt"],
        "only_runtime": pairing["only_runtime"],
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
