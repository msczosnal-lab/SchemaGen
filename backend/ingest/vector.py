"""Ekstrakcja wektorowa linii i tekstu z PDF (PyMuPDF get_drawings / get_text).

Wspolrzedne w pikselach PNG (dpi/72) — ten sam uklad co pdf_to_png i GT.
"""

from __future__ import annotations

import math
import re
from dataclasses import dataclass, field
from pathlib import Path

from backend.paths import RAW, ROOT
from backend.recognize.line_tracer import (
    LineSegment,
    _is_axial,
    _is_page_border,
    _merge_collinear,
)

SOURCES = ROOT / "sync" / "sources"
_GRID_MAX_WIDTH_PT = 0.1
_FRAME_MIN_WIDTH_PT = 0.65
_DASH_EMPTY = "[] 0"


@dataclass(frozen=True)
class VectorSegment:
    x1: float
    y1: float
    x2: float
    y2: float
    color_hex: str = "#000000"
    width_pt: float = 0.0
    dashed: bool = False

    @property
    def length(self) -> float:
        return math.hypot(self.x2 - self.x1, self.y2 - self.y1)


@dataclass(frozen=True)
class VectorWord:
    text: str
    bbox: tuple[float, float, float, float]


@dataclass
class VectorPage:
    width: int
    height: int
    lines: list[VectorSegment] = field(default_factory=list)
    curves: int = 0
    words: list[VectorWord] = field(default_factory=list)


@dataclass
class FilterStats:
    raw_lines: int = 0
    after_border: int = 0
    after_roi: int = 0
    after_grid: int = 0
    after_frame: int = 0
    after_dashed: int = 0
    after_color: int = 0


def _rgb01_to_hex(rgb: tuple[float, ...] | None) -> str:
    if not rgb:
        return "#000000"
    r, g, b = (float(rgb[0]), float(rgb[1]), float(rgb[2]))
    return f"#{int(round(r * 255)):02x}{int(round(g * 255)):02x}{int(round(b * 255)):02x}"


def _is_dashed(dashes: object) -> bool:
    text = str(dashes or "").strip()
    return bool(text) and text != _DASH_EMPTY


def _rect_edges(rect) -> list[tuple[float, float, float, float]]:
    x0, y0, x1, y1 = float(rect.x0), float(rect.y0), float(rect.x1), float(rect.y1)
    return [
        (x0, y0, x1, y0),
        (x1, y0, x1, y1),
        (x1, y1, x0, y1),
        (x0, y1, x0, y0),
    ]


def extract_vector_page(
    pdf_path: str | Path,
    page_no: int,
    dpi: int | None = None,
) -> VectorPage:
    """Odczyt sciezek 'l' i bokow 're' + slowa z PDF w pikselach PNG."""
    import fitz

    from backend.runtime_config import pdf_dpi

    pdf_path = Path(pdf_path)
    dpi = pdf_dpi() if dpi is None else int(dpi)
    scale = dpi / 72.0

    doc = fitz.open(pdf_path)
    try:
        page = doc[int(page_no)]
        w_px = int(round(page.rect.width * scale))
        h_px = int(round(page.rect.height * scale))
        out = VectorPage(width=w_px, height=h_px)

        for drawing in page.get_drawings():
            color_hex = _rgb01_to_hex(drawing.get("color"))
            width_pt = float(drawing.get("width") or 0.0)
            dashed = _is_dashed(drawing.get("dashes"))
            for item in drawing.get("items", []):
                kind = item[0]
                if kind == "l":
                    p1, p2 = item[1], item[2]
                    out.lines.append(
                        VectorSegment(
                            p1.x * scale,
                            p1.y * scale,
                            p2.x * scale,
                            p2.y * scale,
                            color_hex=color_hex,
                            width_pt=width_pt,
                            dashed=dashed,
                        )
                    )
                elif kind == "re":
                    rect = item[1]
                    for x1, y1, x2, y2 in _rect_edges(rect):
                        out.lines.append(
                            VectorSegment(
                                x1 * scale,
                                y1 * scale,
                                x2 * scale,
                                y2 * scale,
                                color_hex=color_hex,
                                width_pt=width_pt,
                                dashed=dashed,
                            )
                        )
                elif kind == "c":
                    out.curves += 1

        for word in page.get_text("words"):
            x0, y0, x1, y1, text, *_ = word
            out.words.append(
                VectorWord(
                    text=str(text),
                    bbox=(x0 * scale, y0 * scale, x1 * scale, y1 * scale),
                )
            )
        return out
    finally:
        doc.close()


def page_has_vectors(pdf_path: str | Path, page_no: int) -> bool:
    import fitz

    doc = fitz.open(pdf_path)
    try:
        return len(doc[int(page_no)].get_drawings()) > 0
    finally:
        doc.close()


def resolve_pdf_for_image(image_path: str | Path) -> tuple[Path, int] | None:
    """Mapuje data/raw/<stem>.png -> (pdf, page_index). Sufiks _pNNN = indeks enumerate."""
    stem = Path(image_path).stem
    m = re.search(r"_p(\d+)$", stem)
    if not m:
        return None
    page_index = int(m.group(1))
    pdf_stem = stem[: m.start()]
    for directory in (SOURCES, RAW):
        candidate = directory / f"{pdf_stem}.pdf"
        if candidate.exists():
            return candidate, page_index
    return None


def _drop_page_border(
    segments: list[VectorSegment], w: float, h: float
) -> list[VectorSegment]:
    out: list[VectorSegment] = []
    for seg in segments:
        ls = LineSegment(seg.x1, seg.y1, seg.x2, seg.y2, seg.color_hex)
        if not _is_page_border(ls, int(w), int(h)):
            out.append(seg)
    return out


def _drop_roi_bottom(
    segments: list[VectorSegment], h: float, frac: float
) -> list[VectorSegment]:
    if frac >= 1.0:
        return segments
    cutoff = frac * h
    out: list[VectorSegment] = []
    for seg in segments:
        top_y = min(seg.y1, seg.y2)
        if top_y < cutoff:
            out.append(seg)
    return out


def _wire_color_allowed(hex_color: str) -> bool:
    """Kolor z PDF -> grupa semantyczna; odrzuc obrysy/frame/dash (nie wire)."""
    from backend.colors.palette import load_palette

    palette = load_palette()
    group = palette.match_color(hex_color)
    if not group:
        return True
    grp = palette.groups.get(group, {})
    hint = grp.get("hint_role")
    if hint and str(hint) != "wire":
        return False
    roles = [str(r) for r in (grp.get("roles") or [])]
    if roles and "wire" not in roles:
        return False
    return True


def filter_scheme_segments(
    segments: list[VectorSegment],
    *,
    page_size: tuple[int, int],
    roi_bottom_frac: float,
    stats: FilterStats | None = None,
) -> list[VectorSegment]:
    """034b: ramka, ROI, siatka (cienki width), grube ramki, linie przerywane, kolor."""
    st = stats or FilterStats()
    w, h = page_size
    st.raw_lines = len(segments)

    kept = _drop_page_border(segments, float(w), float(h))
    st.after_border = len(kept)

    kept = _drop_roi_bottom(kept, float(h), roi_bottom_frac)
    st.after_roi = len(kept)

    kept = [s for s in kept if s.width_pt >= _GRID_MAX_WIDTH_PT]
    st.after_grid = len(kept)

    kept = [s for s in kept if s.width_pt < _FRAME_MIN_WIDTH_PT]
    st.after_frame = len(kept)

    kept = [s for s in kept if not s.dashed]
    st.after_dashed = len(kept)

    kept = [s for s in kept if _wire_color_allowed(s.color_hex)]
    st.after_color = len(kept)
    return kept


def _merge_gap_tol(page_size: tuple[int, int]) -> float:
    """Tolerancja przerwy miedzy koliniarnymi segmentami PDF (034c).

    Skala: bus_gap_frac * max(W,H) z runtime.yaml (ten sam rzad wielkosci co Hough).
    """
    w, h = page_size
    big = max(w, h)
    try:
        from backend.runtime_config import hough_params

        frac = float(hough_params().get("bus_gap_frac", 0.004))
    except Exception:
        frac = 0.004
    return max(12.0, frac * big)


def merge_vector_segments(
    segments: list[VectorSegment],
    *,
    page_size: tuple[int, int],
    gap_tol: float | None = None,
    axis_only: bool | None = None,
    axis_tol_deg: float = 6.0,
) -> list[VectorSegment]:
    """034c: scal kolinearne o tym samym kolorze i width_pt."""
    if not segments:
        return []
    gap = gap_tol if gap_tol is not None else _merge_gap_tol(page_size)
    if axis_only is None:
        try:
            from backend.runtime_config import wire_axis_only

            axis_only = wire_axis_only()
        except Exception:
            axis_only = True

    by_style: dict[tuple[str, float], list[LineSegment]] = {}
    for seg in segments:
        key = (seg.color_hex, round(seg.width_pt, 4))
        by_style.setdefault(key, []).append(
            LineSegment(seg.x1, seg.y1, seg.x2, seg.y2, seg.color_hex)
        )

    merged: list[VectorSegment] = []
    for (color_hex, width_pt), group in by_style.items():
        parts = _merge_collinear(group, gap_tol=gap)
        if axis_only:
            parts = [
                s
                for s in parts
                if _is_axial(s.x1, s.y1, s.x2, s.y2, axis_tol_deg)
            ]
        for s in parts:
            merged.append(
                VectorSegment(
                    s.x1,
                    s.y1,
                    s.x2,
                    s.y2,
                    color_hex=color_hex,
                    width_pt=width_pt,
                    dashed=False,
                )
            )
    return merged


def vector_segments_to_line_segments(segments: list[VectorSegment]) -> list[LineSegment]:
    return [
        LineSegment(s.x1, s.y1, s.x2, s.y2, detected_color=s.color_hex)
        for s in segments
    ]


def _is_mostek_type(type_name: str) -> bool:
    return "mostek" in str(type_name or "").lower()


def _line_endpoints(line) -> tuple[tuple[float, float], tuple[float, float]]:
    pts = [(float(p[0]), float(p[1])) for p in line.points if len(p) >= 2]
    if len(pts) < 2:
        p = pts[0] if pts else (0.0, 0.0)
        return p, p
    return pts[0], pts[-1]


def _point_on_segment_interior(
    px: float,
    py: float,
    ax: float,
    ay: float,
    bx: float,
    by: float,
    tol: float,
    *,
    endpoint_margin_frac: float = 0.08,
) -> bool:
    """Punkt na odcinku AB, z dala od koncow (srodek = kolanko T)."""
    dx, dy = bx - ax, by - ay
    length_sq = dx * dx + dy * dy
    if length_sq < 1e-6:
        return False
    t = ((px - ax) * dx + (py - ay) * dy) / length_sq
    if t <= endpoint_margin_frac or t >= 1.0 - endpoint_margin_frac:
        return False
    proj_x = ax + t * dx
    proj_y = ay + t * dy
    return math.hypot(px - proj_x, py - proj_y) <= tol


def _point_in_bbox(
    x: float, y: float, bbox: list[float], margin: float = 0.0
) -> bool:
    if len(bbox) < 4:
        return False
    x1, y1, x2, y2 = bbox[:4]
    return (
        x >= x1 - margin
        and x <= x2 + margin
        and y >= y1 - margin
        and y <= y2 + margin
    )


def _near_mostek(x: float, y: float, components, tol: float) -> bool:
    for c in components:
        if not _is_mostek_type(c.type):
            continue
        if _point_in_bbox(x, y, c.bbox, margin=tol):
            return True
    return False


def drop_t_stubs_at_mostek(lines: list, components, *, tol: float) -> list:
    """Odrzuc odnoge T przy mostku — polaczenie jest bboxem YOLO, nie linia."""
    from backend.recognize.line_classifier import LineClassifier

    mosteks = [c for c in components if _is_mostek_type(c.type)]
    if not mosteks:
        return lines

    wires = [ln for ln in lines if LineClassifier.is_connection_candidate(ln)]
    others = [ln for ln in lines if not LineClassifier.is_connection_candidate(ln)]
    drop: set[int] = set()

    for i, stub in enumerate(wires):
        s0, s1 = _line_endpoints(stub)
        for host in wires:
            h0, h1 = _line_endpoints(host)
            for tip in (s0, s1):
                if not _point_on_segment_interior(
                    tip[0], tip[1], h0[0], h0[1], h1[0], h1[1], tol
                ):
                    continue
                if _near_mostek(tip[0], tip[1], mosteks, tol):
                    drop.add(i)
                    break
            if i in drop:
                break
        if i in drop:
            continue
        for m in mosteks:
            if len(m.bbox) < 4:
                continue
            x1, y1, x2, y2 = m.bbox[:4]
            if (
                min(s0[0], s1[0]) >= x1 - 2
                and max(s0[0], s1[0]) <= x2 + 2
                and min(s0[1], s1[1]) >= y1 - 2
                and max(s0[1], s1[1]) <= y2 + 2
            ):
                drop.add(i)
                break

    kept = [ln for idx, ln in enumerate(wires) if idx not in drop]
    return kept + others


def _corner_angle_deg(
    prev: tuple[float, float],
    corner: tuple[float, float],
    nxt: tuple[float, float],
) -> float:
    v1 = (prev[0] - corner[0], prev[1] - corner[1])
    v2 = (nxt[0] - corner[0], nxt[1] - corner[1])
    a1 = math.degrees(math.atan2(v1[1], v1[0])) % 180.0
    a2 = math.degrees(math.atan2(v2[1], v2[0])) % 180.0
    d = abs(a1 - a2)
    return min(d, 180.0 - d)


def merge_l_corners(
    lines: list,
    *,
    gap_tol: float,
    corner_angle_tol_deg: float = 12.0,
    min_corner_angle_deg: float = 45.0,
) -> list:
    """Sklej ortogonalne odcinki w polilinie L (wspolny wierzcholek)."""
    cur = lines
    for _ in range(8):
        nxt = _merge_l_corners_once(
            cur,
            gap_tol=gap_tol,
            corner_angle_tol_deg=corner_angle_tol_deg,
            min_corner_angle_deg=min_corner_angle_deg,
        )
        if len(nxt) == len(cur):
            return nxt
        cur = nxt
    return cur


def _merge_l_corners_once(
    lines: list,
    *,
    gap_tol: float,
    corner_angle_tol_deg: float,
    min_corner_angle_deg: float,
) -> list:
    from backend.recognize.line_classifier import LineClassifier

    wires = [ln for ln in lines if LineClassifier.is_connection_candidate(ln)]
    others = [ln for ln in lines if not LineClassifier.is_connection_candidate(ln)]
    if len(wires) < 2:
        return lines

    def snap_key(p: tuple[float, float]) -> tuple[int, int]:
        return (int(round(p[0] / gap_tol)), int(round(p[1] / gap_tol)))

    buckets: dict[
        tuple[int, int], list[tuple[int, tuple[float, float], tuple[float, float]]]
    ] = {}
    for idx, ln in enumerate(wires):
        p0, p1 = _line_endpoints(ln)
        buckets.setdefault(snap_key(p0), []).append((idx, p0, p1))
        buckets.setdefault(snap_key(p1), []).append((idx, p1, p0))

    used: set[int] = set()
    merged: list = []

    for i, base in enumerate(wires):
        if i in used:
            continue
        b0, b1 = _line_endpoints(base)
        best: tuple[int, list[list[float]], float] | None = None

        for corner, tip in ((b0, b1), (b1, b0)):
            for j, c_corner, c_out in buckets.get(snap_key(corner), []):
                if j == i or j in used:
                    continue
                ang = _corner_angle_deg(tip, corner, c_out)
                if ang < min_corner_angle_deg or ang > 180.0 - min_corner_angle_deg:
                    continue
                if ang <= corner_angle_tol_deg or ang >= 180.0 - corner_angle_tol_deg:
                    continue
                score = abs(ang - 90.0)
                pts = [list(tip), list(corner), list(c_out)]
                if best is None or score < best[2]:
                    best = (j, pts, score)

        if best is not None:
            j, pts, _ = best
            used.add(i)
            used.add(j)
            merged.append(base.model_copy(update={"points": pts}))
        else:
            used.add(i)
            merged.append(base)

    return merged + others


def _polyline_crosses_components(line, components, tol: float) -> int:
    """Ile bboxow przecina dowolny odcinek polilinii."""
    from backend.recognize.line_sieve import _segment_crosses_bbox

    pts = line.points
    if len(pts) < 2:
        return 0
    seen: set[str] = set()
    for i in range(len(pts) - 1):
        p, q = pts[i], pts[i + 1]
        for c in components:
            if len(c.bbox) < 4:
                continue
            if _segment_crosses_bbox(p, q, c.bbox, tol):
                seen.add(c.id)
    return len(seen)


def filter_vector_through_wires(lines: list, components, *, tol: float) -> list:
    """Przewod przechodzi przez tor — bez wymogu konca na terminalu."""
    from backend.recognize.line_classifier import LineClassifier
    from backend.recognize.line_sieve import (
        _components_with_terminals_on_path,
        _containing_component,
    )

    out: list = []
    for ln in lines:
        if not LineClassifier.is_connection_candidate(ln):
            out.append(ln)
            continue
        inside = _containing_component(ln, components, 2.0)
        if inside is not None and not _is_mostek_type(inside.type):
            out.append(ln.model_copy(update={"role": "other"}))
            continue
        crosses = _polyline_crosses_components(ln, components, tol)
        on_path = _components_with_terminals_on_path(ln, components, tol)
        if on_path >= 2 or crosses >= 2:
            out.append(ln)
        else:
            out.append(ln.model_copy(update={"role": "other"}))
    return out


def apply_vector_wire_gate(lines: list, components, *, tol: float) -> list:
    """Kompatybilnosc wsteczna."""
    lines = drop_t_stubs_at_mostek(lines, components, tol=tol)
    return filter_vector_through_wires(lines, components, tol=tol)


def drop_inside_symbol_segments(
    segments: list[LineSegment],
    components,
    *,
    margin: float = 2.0,
    bridge_tol: float = 8.0,
) -> list[LineSegment]:
    """Odrzuc segmenty w calosci w bbox symbolu (kreski wewnetrzne), z wyjatkiem mostka."""
    from backend.models.schema import GraphicLine
    from backend.recognize.line_sieve import _bridges_two_terminals, _containing_component

    out: list[LineSegment] = []
    for seg in segments:
        gl = GraphicLine(
            id="_",
            points=[[seg.x1, seg.y1], [seg.x2, seg.y2]],
            role="wire",
        )
        inside = _containing_component(gl, components, margin)
        if inside is not None:
            if _is_mostek_type(inside.type):
                continue
            if not _bridges_two_terminals(gl, inside, bridge_tol):
                continue
        out.append(seg)
    return out


def trace_vector_page(
    image_path: str | Path,
    *,
    stats: FilterStats | None = None,
) -> list[LineSegment] | None:
    """Pelna sciezka wektorowa dla obrazu strony; None gdy brak PDF/wektorow."""
    from backend.runtime_config import pdf_dpi, roi_bottom_cut_frac

    resolved = resolve_pdf_for_image(image_path)
    if resolved is None:
        return None
    pdf_path, page_no = resolved
    if not page_has_vectors(pdf_path, page_no):
        return None

    page = extract_vector_page(pdf_path, page_no, dpi=pdf_dpi())
    filtered = filter_scheme_segments(
        page.lines,
        page_size=(page.width, page.height),
        roi_bottom_frac=roi_bottom_cut_frac(),
        stats=stats,
    )
    merged = merge_vector_segments(
        filtered,
        page_size=(page.width, page.height),
    )
    return vector_segments_to_line_segments(merged)
