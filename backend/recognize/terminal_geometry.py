"""Geometria terminali: przeciecie linii z krawedzia bbox + tusz na obwodzie cropa.

Reguly (Filip):
1. Runtime: terminal TYLKO na przecieciu wire z krawedzia bbox.
2. GT/labeler: segmenty nie-bialego tuszu na obwodzie bbox (jak mostek).
3. Wire laczy terminale miedzy bboxami (ortho — net-builder + terminal-gate).
"""

from __future__ import annotations

import math

from backend.models.schema import Component, GraphicLine, Terminal
from backend.recognize.line_classifier import LineClassifier


def line_bbox_edge_contacts(
    component: Component,
    lines: list[GraphicLine],
    tol: float,
    *,
    merge_tol: float | None = None,
) -> list[tuple[float, float]]:
    """Punkty przeciecia wire z krawedzia bbox (wsp. bezwzgledne strony)."""
    b = component.bbox
    if len(b) < 4:
        return []
    dedup = merge_tol if merge_tol is not None else min(tol, 15.0)
    x1, y1, x2, y2 = b[0], b[1], b[2], b[3]
    edges = (
        ((x1, y1), (x2, y1)),  # top
        ((x2, y1), (x2, y2)),  # right
        ((x2, y2), (x1, y2)),  # bottom
        ((x1, y2), (x1, y1)),  # left
    )
    contacts: list[tuple[float, float]] = []
    for ln in lines:
        if not LineClassifier.is_connection_candidate(ln) or len(ln.points) < 2:
            continue
        pts = ln.points
        for i in range(len(pts) - 1):
            p0, p1 = pts[i], pts[i + 1]
            for e0, e1 in edges:
                hit = _segment_intersection(p0, p1, list(e0), list(e1), tol)
                if hit is not None:
                    _append_dedup(contacts, hit, dedup)
            for ep, other in ((p0, p1), (p1, p0)):
                snap = _endpoint_on_bbox_edge(
                    ep, other, x1, y1, x2, y2, tol
                )
                if snap is not None:
                    _append_dedup(contacts, snap, dedup)
    return contacts


def contacts_to_terminals(
    component: Component, contacts: list[tuple[float, float]]
) -> list[Terminal]:
    """Kontakty abs -> Terminal(rel 0..1), posortowane po obwodzie."""
    b = component.bbox
    if len(b) < 4 or not contacts:
        return []
    x1, y1, x2, y2 = b[0], b[1], b[2], b[3]
    w = (x2 - x1) or 1.0
    h = (y2 - y1) or 1.0
    contacts.sort(key=lambda p: (round(p[1], 1), round(p[0], 1)))
    out: list[Terminal] = []
    for i, (ax, ay) in enumerate(contacts):
        out.append(
            Terminal(id=str(i + 1), x=round((ax - x1) / w, 4), y=round((ay - y1) / h, 4))
        )
    return out


def perimeter_ink_contacts(
    component: Component, image_bgr, *, pad_px: int = 2
) -> list[tuple[float, float]]:
    """Srodki segmentow nie-bialego tuszu na obwodzie cropa -> abs xy."""
    from backend.recognize.mostek_terminals import _stub_rel_positions
    from train.mostek_orient import binarize

    b = component.bbox
    if len(b) < 4:
        return []
    h_img, w_img = image_bgr.shape[:2]
    x1 = max(0, int(b[0]) - pad_px)
    y1 = max(0, int(b[1]) - pad_px)
    x2 = min(w_img, int(b[2]) + pad_px)
    y2 = min(h_img, int(b[3]) + pad_px)
    if x2 <= x1 or y2 <= y1:
        return []
    crop = image_bgr[y1:y2, x1:x2]
    rel = _stub_rel_positions(binarize(crop))
    bw = (x2 - x1) or 1.0
    bh = (y2 - y1) or 1.0
    return [(x1 + u * bw, y1 + v * bh) for u, v in rel]


def _append_dedup(
    contacts: list[tuple[float, float]], pt: tuple[float, float], dedup: float
) -> None:
    if any(math.hypot(pt[0] - c[0], pt[1] - c[1]) <= dedup for c in contacts):
        return
    contacts.append(pt)


def _segment_intersection(
    p0: list[float],
    p1: list[float],
    q0: list[float],
    q1: list[float],
    tol: float,
) -> tuple[float, float] | None:
    """Przeciecie odcinkow p0-p1 i q0-q1 (w granicach tol)."""
    x1, y1, x2, y2 = p0[0], p0[1], p1[0], p1[1]
    x3, y3, x4, y4 = q0[0], q0[1], q1[0], q1[1]
    denom = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)
    if abs(denom) < 1e-9:
        return None
    t = ((x1 - x3) * (y3 - y4) - (y1 - y3) * (x3 - x4)) / denom
    u = -((x1 - x2) * (y1 - y3) - (y1 - y2) * (x1 - x3)) / denom
    if -1e-6 <= t <= 1.0 + 1e-6 and -1e-6 <= u <= 1.0 + 1e-6:
        return (x1 + t * (x2 - x1), y1 + t * (y2 - y1))
    return None


def _endpoint_on_bbox_edge(
    ep: list[float],
    other: list[float],
    x1: float,
    y1: float,
    x2: float,
    y2: float,
    tol: float,
) -> tuple[float, float] | None:
    """Koniec linii przy krawedzi bbox — tylko gdy TO ten koniec dotyka (nie drugi)."""
    b = [x1, y1, x2, y2]
    d_ep = _point_bbox_dist(ep, b)
    d_other = _point_bbox_dist(other, b)
    if d_ep > tol or d_other <= d_ep:
        return None
    px, py = ep[0], ep[1]
    px_cl = min(max(px, x1), x2)
    py_cl = min(max(py, y1), y2)
    d = {"l": px_cl - x1, "r": x2 - px_cl, "t": py_cl - y1, "b": y2 - py_cl}
    edge = min(d, key=d.get)
    if d[edge] > tol:
        return None
    if edge == "l":
        return (x1, py_cl)
    if edge == "r":
        return (x2, py_cl)
    if edge == "t":
        return (px_cl, y1)
    return (px_cl, y2)


def _point_bbox_dist(point: list[float], bbox: list[float]) -> float:
    if len(bbox) < 4:
        return float("inf")
    px, py = point[0], point[1]
    dx = max(bbox[0] - px, 0.0, px - bbox[2])
    dy = max(bbox[1] - py, 0.0, py - bbox[3])
    return (dx * dx + dy * dy) ** 0.5
