"""Sito po klasyfikacji: usuwa z kandydatow Connection linie, ktore NIE sa przewodami."""

from __future__ import annotations

import math

from backend.models.schema import Component, GraphicLine
from backend.recognize.line_classifier import LineClassifier

AXIS_TOL_DEG = 8.0
EDGE_OVERLAP_MIN = 0.6


def apply_sieve(lines, components, text_bboxes, *, edge_tol=6.0, text_margin=2.0, inside_margin=2.0):
    out = []
    for ln in lines:
        if not LineClassifier.is_connection_candidate(ln):
            out.append(ln); continue
        if _is_box_edge(ln, components, edge_tol):
            out.append(ln.model_copy(update={"role": "frame"}))
        elif _is_inside_component(ln, components, inside_margin):
            out.append(ln.model_copy(update={"role": "other"}))
        elif _is_text_artifact(ln, text_bboxes, text_margin):
            out.append(ln.model_copy(update={"role": "other"}))
        else:
            out.append(ln)
    return out


def _endpoints(line):
    if len(line.points) < 2:
        return None
    return line.points[0], line.points[-1]


def _orientation(p, q):
    ang = math.degrees(math.atan2(abs(q[1]-p[1]), abs(q[0]-p[0])))
    if ang <= AXIS_TOL_DEG: return "h"
    if ang >= 90.0-AXIS_TOL_DEG: return "v"
    return None


def _overlap_frac(a0, a1, b0, b1):
    lo, hi = max(min(a0,a1), min(b0,b1)), min(max(a0,a1), max(b0,b1))
    inter = hi-lo
    if inter <= 0: return 0.0
    shortest = min(abs(a1-a0), abs(b1-b0))
    return inter/shortest if shortest > 0 else 0.0


def _is_box_edge(line, components, tol):
    ep = _endpoints(line)
    if ep is None: return False
    p, q = ep
    orient = _orientation(p, q)
    if orient is None: return False
    for c in components:
        if len(c.bbox) < 4: continue
        x1, y1, x2, y2 = c.bbox[0], c.bbox[1], c.bbox[2], c.bbox[3]
        if orient == "h":
            yline = (p[1]+q[1])/2
            for yside in (y1, y2):
                if abs(yline-yside) <= tol and _overlap_frac(p[0], q[0], x1, x2) >= EDGE_OVERLAP_MIN:
                    return True
        else:
            xline = (p[0]+q[0])/2
            for xside in (x1, x2):
                if abs(xline-xside) <= tol and _overlap_frac(p[1], q[1], y1, y2) >= EDGE_OVERLAP_MIN:
                    return True
    return False


def _is_inside_component(line, components, margin):
    lb = _line_bbox(line.points)
    for c in components:
        b = c.bbox
        if len(b) < 4: continue
        if (lb[0] >= b[0]-margin and lb[1] >= b[1]-margin and lb[2] <= b[2]+margin and lb[3] <= b[3]+margin):
            return True
    return False


def _line_bbox(points):
    xs = [pt[0] for pt in points]; ys = [pt[1] for pt in points]
    return [min(xs), min(ys), max(xs), max(ys)]


def _is_text_artifact(line, text_bboxes, margin):
    if not text_bboxes: return False
    lb = _line_bbox(line.points)
    for tb in text_bboxes:
        if len(tb) < 4: continue
        if (lb[0] >= tb[0]-margin and lb[1] >= tb[1]-margin and lb[2] <= tb[2]+margin and lb[3] <= tb[3]+margin):
            return True
    return False
