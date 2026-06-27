"""Sito po klasyfikacji: usuwa z kandydatow Connection linie, ktore NIE sa przewodami.

Dwa przecieki przy progu frac 0.02 (kalibracja 2026-06-27):
1. Obramowki urzadzen/terminali — biegna WZDLUZ krawedzi bbox symbolu (rownolegle,
   duze pokrycie). Realny przewod DOTYKA krawedzi punktowo i idzie prostopadle na
   zewnatrz — to je rozroznia. Taka linia -> rola "frame".
2. Artefakty tekstu — krotkie segmenty wpadajace w bbox OCR. -> rola "other".

Czyste funkcje (bez I/O). Nie rusza linii niebedacych kandydatami (wire/bus).
"""

from __future__ import annotations

import math

from backend.models.schema import Component, GraphicLine
from backend.recognize.line_classifier import LineClassifier

AXIS_TOL_DEG = 8.0
EDGE_OVERLAP_MIN = 0.6   # min. pokrycie wspolnego zakresu (linia ∩ bok bbox)


def apply_sieve(
    lines: list[GraphicLine],
    components: list[Component],
    text_bboxes: list[list[float]],
    *,
    edge_tol: float = 6.0,
    text_margin: float = 2.0,
) -> list[GraphicLine]:
    """Zwraca linie z poprawiona rola: obramowki->frame, tekst->other. Reszta bez zmian."""
    out: list[GraphicLine] = []
    for ln in lines:
        if not LineClassifier.is_connection_candidate(ln):
            out.append(ln)
            continue
        if _is_box_edge(ln, components, edge_tol):
            out.append(ln.model_copy(update={"role": "frame"}))
        elif _is_text_artifact(ln, text_bboxes, text_margin):
            out.append(ln.model_copy(update={"role": "other"}))
        else:
            out.append(ln)
    return out


def _endpoints(line: GraphicLine) -> tuple[list[float], list[float]] | None:
    if len(line.points) < 2:
        return None
    return line.points[0], line.points[-1]


def _orientation(p: list[float], q: list[float]) -> str | None:
    """'h' / 'v' / None — czy segment jest w osi (poziom/pion)."""
    ang = math.degrees(math.atan2(abs(q[1] - p[1]), abs(q[0] - p[0])))
    if ang <= AXIS_TOL_DEG:
        return "h"
    if ang >= 90.0 - AXIS_TOL_DEG:
        return "v"
    return None


def _overlap_frac(a0: float, a1: float, b0: float, b1: float) -> float:
    """Pokrycie wzgledem KROTSZEGO z zakresow [a0,a1] i [b0,b1]."""
    lo, hi = max(min(a0, a1), min(b0, b1)), min(max(a0, a1), max(b0, b1))
    inter = hi - lo
    if inter <= 0:
        return 0.0
    shortest = min(abs(a1 - a0), abs(b1 - b0))
    return inter / shortest if shortest > 0 else 0.0


def _is_box_edge(line: GraphicLine, components: list[Component], tol: float) -> bool:
    """True gdy linia biegnie wzdluz boku ktoregos bbox (obramowka, nie przewod)."""
    ep = _endpoints(line)
    if ep is None:
        return False
    p, q = ep
    orient = _orientation(p, q)
    if orient is None:
        return False
    for c in components:
        if len(c.bbox) < 4:
            continue
        x1, y1, x2, y2 = c.bbox[0], c.bbox[1], c.bbox[2], c.bbox[3]
        if orient == "h":
            yline = (p[1] + q[1]) / 2
            for yside in (y1, y2):  # gora / dol
                if abs(yline - yside) <= tol and _overlap_frac(p[0], q[0], x1, x2) >= EDGE_OVERLAP_MIN:
                    return True
        else:  # 'v'
            xline = (p[0] + q[0]) / 2
            for xside in (x1, x2):  # lewa / prawa
                if abs(xline - xside) <= tol and _overlap_frac(p[1], q[1], y1, y2) >= EDGE_OVERLAP_MIN:
                    return True
    return False


def _line_bbox(points: list[list[float]]) -> list[float]:
    xs = [pt[0] for pt in points]
    ys = [pt[1] for pt in points]
    return [min(xs), min(ys), max(xs), max(ys)]


def _is_text_artifact(line: GraphicLine, text_bboxes: list[list[float]], margin: float) -> bool:
    """True gdy bbox linii miesci sie (z marginesem) w ktoryms bbox tekstu OCR."""
    if not text_bboxes:
        return False
    lb = _line_bbox(line.points)
    for tb in text_bboxes:
        if len(tb) < 4:
            continue
        if (
            lb[0] >= tb[0] - margin
            and lb[1] >= tb[1] - margin
            and lb[2] <= tb[2] + margin
            and lb[3] <= tb[3] + margin
        ):
            return True
    return False
