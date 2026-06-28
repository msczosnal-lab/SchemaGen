"""Sito po klasyfikacji: usuwa z kandydatow Connection linie, ktore NIE sa przewodami.

Przecieki przy progu frac 0.02 (kalibracja 2026-06-27, feedback Filip):
1. Obramowki urzadzen/terminali — biegna WZDLUZ krawedzi bbox symbolu (rownolegle,
   duze pokrycie). Realny przewod DOTYKA krawedzi punktowo i idzie prostopadle na
   zewnatrz — to je rozroznia. -> rola "frame".
2. Grafika WEWNATRZ bbox (tabelki w terminalach, obrysy wewnetrzne) — cala linia
   miesci sie w bbox symbolu. Przewod laczacy wychodzi poza bbox. -> rola "other".
3. Artefakty tekstu — krotkie segmenty wpadajace w bbox OCR. -> rola "other".

WYJATEK (mostek w listwie): linia w calosci w bbox, ktorej KONCE trafiaja w 2 ROZNE
terminale tego samego komponentu, to mostek terminal<->terminal — NIE demotujemy
(zostaje wire -> net-builder zrobi z niej Connection kind="link"). Bez tego sito
zjadalo wewnetrzne mostki listwy zanim dotarly do net-buildera.

Czyste funkcje (bez I/O). Nie rusza linii niebedacych kandydatami (wire/bus).
"""

from __future__ import annotations

import math

from backend.models.schema import Component, GraphicLine
from backend.recognize.line_classifier import LineClassifier

AXIS_TOL_DEG = 8.0
EDGE_OVERLAP_MIN = 0.6   # min. pokrycie wspolnego zakresu (linia wzdluz boku bbox)


def apply_sieve(
    lines: list[GraphicLine],
    components: list[Component],
    text_bboxes: list[list[float]],
    *,
    edge_tol: float = 6.0,
    text_margin: float = 2.0,
    inside_margin: float = 2.0,
    bridge_tol: float = 8.0,
) -> list[GraphicLine]:
    """Linie z poprawiona rola: bok bbox->frame, wnetrze bbox->other, tekst->other.

    Kolejnosc: bok > wnetrze > tekst > bez zmian. Nie-kandydaci (poza wire/bus) nietknieci.
    WYJATEK: mostek (konce w 2 roznych terminalach tego samego komponentu) zostaje wire.
    `bridge_tol` = maks. odleglosc konca linii od terminala (px).
    """
    out: list[GraphicLine] = []
    for ln in lines:
        if not LineClassifier.is_connection_candidate(ln):
            out.append(ln)
            continue
        if _is_box_edge(ln, components, edge_tol):
            out.append(ln.model_copy(update={"role": "frame"}))
            continue
        inside = _containing_component(ln, components, inside_margin)
        if inside is not None:
            if _bridges_two_terminals(ln, inside, bridge_tol):
                out.append(ln)  # mostek terminal<->terminal — zostaje kandydatem
            else:
                out.append(ln.model_copy(update={"role": "other"}))
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


def _containing_component(
    line: GraphicLine, components: list[Component], margin: float
) -> Component | None:
    """Komponent, ktorego bbox w CALOSCI zawiera linie (grafika wewnetrzna), albo None.

    Przewod laczacy wychodzi poza bbox (dotyka brzegu i idzie dalej) -> nie zlapany.
    """
    lb = _line_bbox(line.points)
    for c in components:
        b = c.bbox
        if len(b) < 4:
            continue
        if (
            lb[0] >= b[0] - margin
            and lb[1] >= b[1] - margin
            and lb[2] <= b[2] + margin
            and lb[3] <= b[3] + margin
        ):
            return c
    return None


def _bridges_two_terminals(line: GraphicLine, comp: Component, tol: float) -> bool:
    """True gdy oba konce linii trafiaja w 2 ROZNE terminale `comp` (mostek w listwie)."""
    if len(comp.terminals) < 2 or len(comp.bbox) < 4:
        return False
    ep = _endpoints(line)
    if ep is None:
        return False
    x1, y1, x2, y2 = comp.bbox[0], comp.bbox[1], comp.bbox[2], comp.bbox[3]
    w = (x2 - x1) or 1.0
    h = (y2 - y1) or 1.0

    def nearest_term_id(pt: list[float]) -> str | None:
        best_id, best_d = None, tol
        for t in comp.terminals:
            ax = x1 + t.x * w
            ay = y1 + t.y * h
            d = math.hypot(pt[0] - ax, pt[1] - ay)
            if d <= best_d:
                best_d = d
                best_id = t.id
        return best_id

    a_id = nearest_term_id(ep[0])
    b_id = nearest_term_id(ep[1])
    return a_id is not None and b_id is not None and a_id != b_id


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
