"""Render symbolu QET (.elmt geometry) → PNG przez Pillow (offline, bez sieci)."""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw

from backend.atlas.qet_parser import QetElement

_TARGET = 128
_PADDING = 10
_LINE_W = 2
_TERM_R = 3


def render_element(element: QetElement, size: int = _TARGET) -> Image.Image:
    """Zwraca obraz PIL (biale tlo, czarne linie) dla danego elementu."""
    img = Image.new("RGB", (size, size), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)

    geom = element.geometry
    bb = geom.bounding_box()
    if bb is None:
        return img

    x_min, y_min, x_max, y_max = bb
    geom_w = x_max - x_min
    geom_h = y_max - y_min
    inner = size - 2 * _PADDING

    if geom_w > 0 and geom_h > 0:
        scale = min(inner / geom_w, inner / geom_h)
    elif geom_w > 0:
        scale = inner / geom_w
    elif geom_h > 0:
        scale = inner / geom_h
    else:
        scale = 1.0

    def _t(x: float, y: float) -> tuple[int, int]:
        px = (x - x_min) * scale + _PADDING
        py = (y - y_min) * scale + _PADDING
        return int(round(px)), int(round(py))

    for x1, y1, x2, y2 in geom.lines:
        draw.line([_t(x1, y1), _t(x2, y2)], fill=(0, 0, 0), width=_LINE_W)

    for rx, ry, rw, rh in geom.rects:
        tl = _t(rx, ry)
        br = _t(rx + rw, ry + rh)
        if tl != br:
            draw.rectangle([tl, br], outline=(0, 0, 0), width=_LINE_W)

    for cx, cy, r in geom.circles:
        tl = _t(cx - r, cy - r)
        br = _t(cx + r, cy + r)
        if tl != br:
            draw.ellipse([tl, br], outline=(0, 0, 0), width=_LINE_W)

    for ax, ay, aw, ah, start, span in geom.arcs:
        tl = _t(ax, ay)
        br = _t(ax + aw, ay + ah)
        if tl != br:
            # PIL arc: 0=east, counterclockwise; QET: 0=east, CCW
            draw.arc([tl, br], start=-start - span, end=-start, fill=(0, 0, 0), width=_LINE_W)

    for poly in geom.polygons:
        if len(poly) >= 2:
            pts = [_t(px, py) for px, py in poly]
            draw.polygon(pts, outline=(0, 0, 0))

    for term in geom.terminals:
        pt = _t(term.x, term.y)
        r = _TERM_R
        draw.ellipse(
            [pt[0] - r, pt[1] - r, pt[0] + r, pt[1] + r],
            fill=(180, 180, 180),
            outline=(0, 0, 0),
            width=1,
        )

    return img


def save_crop(element: QetElement, out_path: Path, size: int = _TARGET) -> None:
    """Renderuje element i zapisuje PNG pod out_path."""
    img = render_element(element, size=size)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(str(out_path), "PNG")
