"""Diagnose runtime graphic_line excess vs GT (loop 033).

Runs recognize_file, assigns each runtime line to one category:
  cat1_noise, cat2_duplicate, cat3_titleblock, cat4_split, matched

Usage:
    python scripts/diag_lines_excess.py --page p028
    python scripts/diag_lines_excess.py --page p028 --out data/output/diag_lines_excess/p028.json
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from backend.paths import RAW
from backend.recognize.pipeline import recognize_file
from backend.runtime_config import hough_params, line_match_tol, roi_bottom_cut_frac
from backend.validate.diff_metrics import _build_grid, _coverage, _sample_polyline, page_id
from labeler.gt_loader import load_gt_schema


def _polyline_length(points: list[list[float]]) -> float:
    pts = [(float(p[0]), float(p[1])) for p in points if len(p) >= 2]
    if len(pts) < 2:
        return 0.0
    return sum(math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(pts, pts[1:]))


def _endpoints(line) -> tuple[tuple[float, float], tuple[float, float]]:
    pts = [(float(p[0]), float(p[1])) for p in line.points if len(p) >= 2]
    if len(pts) < 2:
        p = pts[0] if pts else (0.0, 0.0)
        return p, p
    return pts[0], pts[-1]


def _angle_deg(p0: tuple[float, float], p1: tuple[float, float]) -> float:
    return math.degrees(math.atan2(p1[1] - p0[1], p1[0] - p0[0])) % 180.0


def _overlap_frac_1d(a0: float, a1: float, b0: float, b1: float) -> float:
    lo_a, hi_a = sorted((a0, a1))
    lo_b, hi_b = sorted((b0, b1))
    inter = max(0.0, min(hi_a, hi_b) - max(lo_a, lo_b))
    span = max(hi_a - lo_a, hi_b - lo_b, 1e-6)
    return inter / span


def _nearly_duplicate(a, b, tol: float, angle_tol_deg: float = 6.0) -> bool:
    (ax0, ay0), (ax1, ay1) = _endpoints(a)
    (bx0, by0), (bx1, by1) = _endpoints(b)
    la = math.hypot(ax1 - ax0, ay1 - ay0)
    lb = math.hypot(bx1 - bx0, by1 - by0)
    if la < 1e-3 or lb < 1e-3:
        return False
    ang_a = _angle_deg((ax0, ay0), (ax1, ay1))
    ang_b = _angle_deg((bx0, by0), (bx1, by1))
    d_ang = abs(ang_a - ang_b)
    d_ang = min(d_ang, 180.0 - d_ang)
    if d_ang > angle_tol_deg:
        return False
    # odleglosc prostopadla srodka B od osi A
    mx, my = (bx0 + bx1) / 2, (by0 + by1) / 2
  # project mx,my onto A
    dx, dy = ax1 - ax0, ay1 - ay0
    norm = math.hypot(dx, dy) or 1.0
    t = ((mx - ax0) * dx + (my - ay0) * dy) / (norm * norm)
    px, py = ax0 + t * dx, ay0 + t * dy
    if math.hypot(mx - px, my - py) > tol:
        return False
    ux, uy = dx / norm, dy / norm
    pa0 = (ax0 - ax0) * ux + (ay0 - ay0) * uy
    pa1 = (ax1 - ax0) * ux + (ay1 - ay0) * uy
    pb0 = (bx0 - ax0) * ux + (by0 - ay0) * uy
    pb1 = (bx1 - ax0) * ux + (by1 - ay0) * uy
    if _overlap_frac_1d(pa0, pa1, pb0, pb1) < 0.35:
        return False
    gap = min(
        math.hypot(ax0 - bx0, ay0 - by0),
        math.hypot(ax0 - bx1, ay0 - by1),
        math.hypot(ax1 - bx0, ay1 - by0),
        math.hypot(ax1 - bx1, ay1 - by1),
    )
    return gap <= max(tol * 2, 16.0)


def _rt_on_gt_coverage(rt_line, gt_line, step: float, tol: float) -> float:
    rt_pts = _sample_polyline(rt_line.points, step)
    gt_pts = _sample_polyline(gt_line.points, step)
    if not rt_pts or not gt_pts:
        return 0.0
    return _coverage(rt_pts, _build_grid(gt_pts, tol), tol)


def _entirely_below_roi(line, cutoff_y: float) -> bool:
    if not line.points:
        return False
    top_y = min(float(p[1]) for p in line.points if len(p) >= 2)
    return top_y >= cutoff_y


def categorize_page(pid: str) -> dict:
    img = RAW / f"{pid}.png"
    if not img.exists():
        raise FileNotFoundError(img)

    gt_schema = load_gt_schema(pid)
    if not gt_schema:
        raise RuntimeError(f"Brak GT dla {pid}")

    runtime = recognize_file(str(img))
    rt_lines = list(runtime.graphic_lines)
    gt_lines = list(gt_schema.graphic_lines)

    import cv2

    im = cv2.imread(str(img))
    if im is None:
        raise RuntimeError(f"Nie wczytano {img}")
    h, w = im.shape[:2]
    size_max = max(w, h)

    hp = hough_params()
    min_len = max(float(hp["min_len_floor"]), float(hp["min_len_frac"]) * size_max)
    tol = line_match_tol()
    step = max(2.0, tol / 2.0)
    roi_frac = roi_bottom_cut_frac()
    cutoff_y = roi_frac * h

    # cat3
    cat3: set[int] = set()
    for i, ln in enumerate(rt_lines):
        if _entirely_below_roi(ln, cutoff_y):
            cat3.add(i)

    # cat2 (pairs -> mark shorter as duplicate; longer kept for further cats)
    cat2: set[int] = set()
    lengths = [_polyline_length(ln.points) for ln in rt_lines]
    for i in range(len(rt_lines)):
        if i in cat3:
            continue
        for j in range(i + 1, len(rt_lines)):
            if j in cat3:
                continue
            if _nearly_duplicate(rt_lines[i], rt_lines[j], tol):
                if lengths[i] <= lengths[j]:
                    cat2.add(i)
                else:
                    cat2.add(j)

    # GT assignment for remaining
    gt_assign: list[int | None] = [None] * len(rt_lines)
    gt_cov: list[float] = [0.0] * len(rt_lines)
    global_cov: list[float] = [0.0] * len(rt_lines)

    all_gt_pts = [p for gl in gt_lines for p in _sample_polyline(gl.points, step)]
    gt_grid = _build_grid(all_gt_pts, tol) if all_gt_pts else {}

    for i, ln in enumerate(rt_lines):
        if i in cat3 or i in cat2:
            continue
        rt_pts = _sample_polyline(ln.points, step)
        global_cov[i] = _coverage(rt_pts, gt_grid, tol) if rt_pts else 0.0
        best_g, best_c = None, 0.0
        for gi, gl in enumerate(gt_lines):
            c = _rt_on_gt_coverage(ln, gl, step, tol)
            if c > best_c:
                best_c, best_g = c, gi
        if best_c >= 0.5:
            gt_assign[i] = best_g
            gt_cov[i] = best_c

    # group by gt for cat4 vs matched
    by_gt: dict[int, list[int]] = {}
    for i, g in enumerate(gt_assign):
        if g is None:
            continue
        by_gt.setdefault(g, []).append(i)

    categories: list[str] = ["unassigned"] * len(rt_lines)
    for i in cat3:
        categories[i] = "cat3_titleblock"
    for i in cat2:
        categories[i] = "cat2_duplicate"

    for i, ln in enumerate(rt_lines):
        if categories[i] != "unassigned":
            continue
        g = gt_assign[i]
        if g is not None:
            if len(by_gt.get(g, [])) > 1:
                categories[i] = "cat4_split"
            else:
                categories[i] = "matched"
            continue
        # no GT geometry match
        if lengths[i] < min_len and global_cov[i] < 0.5:
            categories[i] = "cat1_noise"
        elif global_cov[i] < 0.5:
            categories[i] = "cat1_noise"
        else:
            # rare: global hit but no single GT >= 0.5
            categories[i] = "matched"

    counts = {
        "cat1_noise": 0,
        "cat2_duplicate": 0,
        "cat3_titleblock": 0,
        "cat4_split": 0,
        "matched": 0,
    }
    for c in categories:
        if c in counts:
            counts[c] += 1
        else:
            counts[c] = counts.get(c, 0) + 1

    per_line = []
    for i, ln in enumerate(rt_lines):
        per_line.append(
            {
                "id": ln.id,
                "category": categories[i],
                "length_px": round(lengths[i], 2),
                "role": ln.role,
                "gt_index": gt_assign[i],
                "gt_coverage": round(gt_cov[i], 4),
                "global_gt_coverage": round(global_cov[i], 4),
            }
        )

    return {
        "page_id": pid,
        "image_size": [w, h],
        "params": {
            "tol": tol,
            "min_len_px": round(min_len, 2),
            "roi_bottom_cut_frac": roi_frac,
            "roi_cutoff_y": round(cutoff_y, 2),
        },
        "gt_line_count": len(gt_lines),
        "runtime_line_count": len(rt_lines),
        "counts": counts,
        "per_line": per_line,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--page", default="p028")
    ap.add_argument(
        "--out",
        default="",
        help="sciezka JSON (domyslnie data/output/diag_lines_excess/<pid>.json)",
    )
    args = ap.parse_args()

    pid = page_id(args.page)
    try:
        report = categorize_page(pid)
    except Exception as exc:
        print(f"[BLAD] {exc}", file=sys.stderr)
        return 1

    out_path = Path(args.out) if args.out else _ROOT / "data" / "output" / "diag_lines_excess" / f"{pid}.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(out_path)
    print(json.dumps({"page_id": pid, "counts": report["counts"], "runtime_line_count": report["runtime_line_count"]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
