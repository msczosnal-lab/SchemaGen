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
    try:
    from backend.runtime_config import hough_params

    frac = float(hough_params().get("bus_gap_frac", 0.004))
    except Exception:
    frac = 0.004
    return max(12.0, frac * max(page_size))


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
          s.x1, s.y1, s.x2, s.y2,
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
