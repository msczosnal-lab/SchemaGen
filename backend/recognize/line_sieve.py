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
# Obramowka jednego symbolu ma dlugosc ~ szerokosc/wysokosc bbox. Szyna przez rzad
# zlaczek (p027) biegnie wzdluz wielu bboxow — line_span >> box_span -> wire, nie frame.
EDGE_FRAME_MAX_SPAN_RATIO = 1.25
# Krotkie segmenty w bbox OCR; dluzsze to przewody (szyna przez pasek tytulowy itd.).
TEXT_ARTIFACT_MAX_LEN = 120.0
# Grafika wewnetrzna symbolu jest krotka; przewod na ~calą szerokosc bboxa to nie tabelka.
INSIDE_MAX_SPAN_RATIO = 0.85


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
        if inside is not None and _spans_most_of_box(ln, inside.bbox):
            inside = None
        if inside is not None:
            if _bridges_two_terminals(ln, inside, bridge_tol):
                out.append(ln)  # mostek terminal<->terminal — zostaje kandydatem
            elif _components_crossed_by_wire(ln, components, edge_tol) >= 2:
                out.append(ln)  # szyna przez rzad symboli — nie grafika wewnetrzna
            else:
                out.append(ln.model_copy(update={"role": "other"}))
        elif _is_text_artifact(ln, text_bboxes, text_margin):
            out.append(ln.model_copy(update={"role": "other"}))
        else:
            out.append(ln)
    return out


def apply_terminal_gate(
    lines: list[GraphicLine],
    components: list[Component],
    *,
    tol: float = 8.0,
    probe_tol: float | None = None,
) -> list[GraphicLine]:
    """Drugie sito: wire/bus zostaje przewodem tylko gdy oba konce maja terminal (OD-DO).

    Wolane PO wyprowadzeniu terminali. Wyjatki: mostek wewnetrzny, szyna z >=2 terminalami
    na sciezce. Gdy jeden koniec nie trafia — probe_tol szuka bboxa / kontaktu z krawedzia.
    """
    probe = probe_tol if probe_tol is not None else max(tol * 2.5, tol + 12.0)
    wire_cands = [ln for ln in lines if LineClassifier.is_connection_candidate(ln)]
    out: list[GraphicLine] = []
    for ln in lines:
        if not LineClassifier.is_connection_candidate(ln):
            out.append(ln)
            continue
        if _passes_terminal_gate(ln, components, wire_cands, tol, probe):
            out.append(ln)
            continue
        out.append(ln.model_copy(update={"role": "other"}))
    return out


def _passes_terminal_gate(
    line: GraphicLine,
    components: list[Component],
    wire_lines: list[GraphicLine],
    tol: float,
    probe_tol: float,
) -> bool:
    inside = _containing_component(line, components, 2.0)
    if inside is not None and _bridges_two_terminals(line, inside, tol):
        return True
    if _components_with_terminals_on_path(line, components, tol) >= 2:
        return True
    if _components_crossed_by_wire(line, components, tol) >= 2:
        return True
    ep = _endpoints(line)
    if ep is None:
        return False
    ok0 = _endpoint_hits_terminal(ep[0], components, tol)
    ok1 = _endpoint_hits_terminal(ep[1], components, tol)
    if not ok0:
        ok0 = _probe_open_endpoint(ep[0], components, wire_lines, tol, probe_tol)
    if not ok1:
        ok1 = _probe_open_endpoint(ep[1], components, wire_lines, tol, probe_tol)
    return ok0 and ok1


def _endpoint_hits_terminal(
    point: list[float], components: list[Component], tol: float
) -> bool:
    from backend.recognize.net_builder import _nearest_component, _nearest_terminal

    c = _nearest_component(point, components, tol)
    if c is None or not c.terminals:
        return False
    return _nearest_terminal(point, c, tol) is not None


def _probe_open_endpoint(
    point: list[float],
    components: list[Component],
    wire_lines: list[GraphicLine],
    tol: float,
    probe_tol: float,
) -> bool:
    """Jeden koniec bez terminala — szerszy promien: bbox mogl byc ledwo poza tol."""
    if _endpoint_hits_terminal(point, components, probe_tol):
        return True
    from backend.recognize.net_builder import (
        _nearest_component,
        _nearest_terminal,
        derive_auto_terminals,
    )
    from backend.recognize.terminal_geometry import line_bbox_edge_contacts

    c = _nearest_component(point, components, probe_tol)
    if c is None:
        return False
    if c.terminals:
        return _nearest_terminal(point, c, probe_tol) is not None
    contacts = line_bbox_edge_contacts(c, wire_lines, tol)
    if not contacts:
        return False
    for cx, cy in contacts:
        if math.hypot(point[0] - cx, point[1] - cy) <= probe_tol:
            return True
    for t in derive_auto_terminals(c, wire_lines, tol):
        if len(c.bbox) < 4:
            break
        x1, y1, x2, y2 = c.bbox[:4]
        w = (x2 - x1) or 1.0
        h = (y2 - y1) or 1.0
        ax = x1 + t.x * w
        ay = y1 + t.y * h
        if math.hypot(point[0] - ax, point[1] - ay) <= probe_tol:
            return True
    return False


def _components_crossed_by_wire(
    line: GraphicLine, components: list[Component], tol: float
) -> int:
    """Ile bboxow przecina osiowy przewod (szyna bez wyprowadzonych terminali)."""
    ep = _endpoints(line)
    if ep is None:
        return 0
    p, q = ep
    count = 0
    for c in components:
        if len(c.bbox) < 4:
            continue
        if _segment_crosses_bbox(p, q, c.bbox, tol):
            count += 1
    return count


def _segment_crosses_bbox(
    p: list[float], q: list[float], bbox: list[float], margin: float
) -> bool:
    x1, y1, x2, y2 = bbox[0], bbox[1], bbox[2], bbox[3]
    orient = _orientation(p, q)
    if orient == "h":
        y = (p[1] + q[1]) / 2
        if y < y1 - margin or y > y2 + margin:
            return False
        return _overlap_frac(p[0], q[0], x1, x2) > 0.05
    if orient == "v":
        x = (p[0] + q[0]) / 2
        if x < x1 - margin or x > x2 + margin:
            return False
        return _overlap_frac(p[1], q[1], y1, y2) > 0.05
    lb = _line_bbox([p, q])
    return not (
        lb[2] < x1 - margin
        or lb[0] > x2 + margin
        or lb[3] < y1 - margin
        or lb[1] > y2 + margin
    )


def _components_with_terminals_on_path(
    line: GraphicLine, components: list[Component], tol: float
) -> int:
    """Ile roznych bboxow ma terminal na polilinii (szyna przez rzad zlaczek)."""
    from backend.recognize.net_builder import _point_on_line_path

    seen: set[str] = set()
    for c in components:
        if not c.terminals or len(c.bbox) < 4:
            continue
        x1, y1, x2, y2 = c.bbox[0], c.bbox[1], c.bbox[2], c.bbox[3]
        w = (x2 - x1) or 1.0
        h = (y2 - y1) or 1.0
        for t in c.terminals:
            ax = x1 + t.x * w
            ay = y1 + t.y * h
            if _point_on_line_path([ax, ay], line, tol):
                seen.add(c.id)
                break
    return len(seen)


def recover_terminal_gated_wires(
    lines: list[GraphicLine],
    components: list[Component],
    *,
    tol: float = 8.0,
    probe_tol: float | None = None,
) -> list[GraphicLine]:
    """Promuj other->wire gdy linia spelnia terminal gate (zdemotowana przez sito, ale prawdziwy przewod)."""
    probe = probe_tol if probe_tol is not None else max(tol * 2.5, tol + 12.0)
    wire_cands = [
        ln for ln in lines if LineClassifier.is_connection_candidate(ln) or ln.role == "other"
    ]
    out: list[GraphicLine] = []
    for ln in lines:
        if ln.role != "other":
            out.append(ln)
            continue
        if _passes_terminal_gate(ln, components, wire_cands, tol, probe):
            out.append(ln.model_copy(update={"role": "wire"}))
        else:
            out.append(ln)
    return out


def merge_collinear_wires(
    lines: list[GraphicLine],
    *,
    gap_tol: float = 12.0,
    perp_tol: float = 6.0,
) -> list[GraphicLine]:
    """Scal kolinearne wire po pipeline — tylko emisja graphic_lines (connections juz zbudowane)."""
    wires = [ln for ln in lines if LineClassifier.is_connection_candidate(ln)]
    rest = [ln for ln in lines if not LineClassifier.is_connection_candidate(ln)]
    if len(wires) < 2:
        return lines

    remaining = sorted(wires, key=lambda ln: -_line_span(ln))
    merged: list[GraphicLine] = []
    used = [False] * len(remaining)

    for i, base in enumerate(remaining):
        if used[i]:
            continue
        ep = _endpoints(base)
        if ep is None:
            used[i] = True
            merged.append(base)
            continue
        x0, y0 = ep[0][0], ep[0][1]
        x1, y1 = ep[1][0], ep[1][1]
        for j in range(i + 1, len(remaining)):
            if used[j]:
                continue
            other = remaining[j]
            if not _collinear_mergeable((x0, y0, x1, y1), other, gap_tol, perp_tol):
                continue
            x0, y0, x1, y1 = _extend_segment_coords(x0, y0, x1, y1, other)
            used[j] = True
        used[i] = True
        merged.append(base.model_copy(update={"points": [[x0, y0], [x1, y1]]}))
    return rest + merged


def _collinear_mergeable(
    seg: tuple[float, float, float, float],
    other: GraphicLine,
    gap_tol: float,
    perp_tol: float,
) -> bool:
    ep = _endpoints(other)
    if ep is None:
        return False
    pa, qa = ep
    orient = _orientation(pa, qa)
    if orient is None:
        return False
    x0, y0, x1, y1 = seg
    if orient == "h":
        yline = (pa[1] + qa[1]) / 2.0
        if abs((y0 + y1) / 2.0 - yline) > perp_tol:
            return False
        a0, a1 = sorted((x0, x1))
        b0, b1 = sorted((pa[0], qa[0]))
    else:
        xline = (pa[0] + qa[0]) / 2.0
        if abs((x0 + x1) / 2.0 - xline) > perp_tol:
            return False
        a0, a1 = sorted((y0, y1))
        b0, b1 = sorted((pa[1], qa[1]))
    if b0 > a1:
        gap = b0 - a1
    elif a0 > b1:
        gap = a0 - b1
    else:
        gap = 0.0
    return gap <= gap_tol


def _extend_segment_coords(
    x0: float, y0: float, x1: float, y1: float, other: GraphicLine
) -> tuple[float, float, float, float]:
    ep = _endpoints(other)
    assert ep is not None
    pa, qa = ep
    pts = [(x0, y0), (x1, y1), (pa[0], pa[1]), (qa[0], qa[1])]
    orient = _orientation(pa, qa)
    if orient == "h":
        ys = [p[1] for p in pts]
        xs = [p[0] for p in pts]
        y = sum(ys) / len(ys)
        return min(xs), y, max(xs), y
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    x = sum(xs) / len(xs)
    return x, min(ys), x, max(ys)


def recover_terminal_bridges(
    lines: list[GraphicLine],
    components: list[Component],
    *,
    inside_margin: float = 2.0,
    bridge_tol: float = 8.0,
) -> list[GraphicLine]:
    """Promuj z powrotem do 'wire' linie 'other' bedace mostkiem 2 terminali komponentu.

    Wolane PO wyprowadzeniu terminali (auto/GT). W runtime sito biegnie zanim terminale
    istnieja, wiec wewnetrzny mostek zostaje zdemotowany — ten przebieg go odzyskuje.
    Nie rusza linii, ktore juz sa kandydatami, ani nie-other.
    """
    out: list[GraphicLine] = []
    for ln in lines:
        if ln.role != "other":
            out.append(ln)
            continue
        comp = _containing_component(ln, components, inside_margin)
        if comp is not None and _bridges_two_terminals(ln, comp, bridge_tol):
            out.append(ln.model_copy(update={"role": "wire"}))
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
    """True gdy linia biegnie wzdluz boku ktoregos bbox (obramowka, nie przewod).

    Przewod przez rzad symboli (szyna listwy) moze byc rownolegly do krawedzi wielu
    bboxow, ale jest znacznie dluzszy niz pojedynczy symbol — nie demotujemy.
    """
    ep = _endpoints(line)
    if ep is None:
        return False
    p, q = ep
    orient = _orientation(p, q)
    if orient is None:
        return False
    line_span = abs(q[0] - p[0]) if orient == "h" else abs(q[1] - p[1])
    for c in components:
        if len(c.bbox) < 4:
            continue
        x1, y1, x2, y2 = c.bbox[0], c.bbox[1], c.bbox[2], c.bbox[3]
        box_span = (x2 - x1) if orient == "h" else (y2 - y1)
        if box_span <= 0:
            continue
        if line_span > box_span * EDGE_FRAME_MAX_SPAN_RATIO:
            continue
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


def _line_span(line: GraphicLine) -> float:
    ep = _endpoints(line)
    if ep is None:
        return 0.0
    p, q = ep
    orient = _orientation(p, q)
    if orient == "h":
        return abs(q[0] - p[0])
    if orient == "v":
        return abs(q[1] - p[1])
    return math.hypot(q[0] - p[0], q[1] - p[1])


def _spans_most_of_box(line: GraphicLine, bbox: list[float]) -> bool:
    """True gdy linia osiowa zajmuje wiekszosc bboxa (przewod, nie grafika wewnetrzna)."""
    if len(bbox) < 4:
        return False
    ep = _endpoints(line)
    if ep is None:
        return False
    orient = _orientation(ep[0], ep[1])
    if orient is None:
        return False
    x1, y1, x2, y2 = bbox[0], bbox[1], bbox[2], bbox[3]
    box_span = (x2 - x1) if orient == "h" else (y2 - y1)
    if box_span <= 0:
        return False
    return _line_span(line) > box_span * INSIDE_MAX_SPAN_RATIO


def _is_text_artifact(line: GraphicLine, text_bboxes: list[list[float]], margin: float) -> bool:
    """True gdy krotki segment w calosci w bbox tekstu OCR (nie dlugi przewod przy etykiecie)."""
    if not text_bboxes:
        return False
    ep = _endpoints(line)
    if ep is None:
        return False
    seg_len = math.hypot(ep[1][0] - ep[0][0], ep[1][1] - ep[0][1])
    if seg_len > TEXT_ARTIFACT_MAX_LEN:
        return False
    lb = _line_bbox(line.points)
    line_w = lb[2] - lb[0]
    line_h = lb[3] - lb[1]
    for tb in text_bboxes:
        if len(tb) < 4:
            continue
        tw = tb[2] - tb[0]
        th = tb[3] - tb[1]
        if line_w > tw + margin or line_h > th + margin:
            continue
        if (
            lb[0] >= tb[0] - margin
            and lb[1] >= tb[1] - margin
            and lb[2] <= tb[2] + margin
            and lb[3] <= tb[3] + margin
        ):
            return True
    return False
