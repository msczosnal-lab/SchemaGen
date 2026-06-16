"""Skalowanie wspolrzednych adnotacji przy zmianie rozdzielczosci PNG."""

from __future__ import annotations

from pathlib import Path

from PIL import Image

from backend.geometry.bbox_layout import enrich_label_record
from backend.models.label import LabelRecord
from labeler.export import find_raw_image


def round_coord(value: float) -> float:
    return round(value, 2)


def scale_label_record(record: LabelRecord, factor: float) -> LabelRecord:
    """Przeskaluj bboxy, teksty, linie i wymiary obrazu; przelicz hierarchie."""
    if abs(factor - 1.0) < 1e-6:
        return record

    scaled = record.model_copy(deep=True)
    for b in scaled.bboxes:
        b.x = round_coord(b.x * factor)
        b.y = round_coord(b.y * factor)
        b.width = round_coord(b.width * factor)
        b.height = round_coord(b.height * factor)

    for t in scaled.texts:
        t.x = round_coord(t.x * factor)
        t.y = round_coord(t.y * factor)
        t.width = round_coord(t.width * factor)
        t.height = round_coord(t.height * factor)

    for line in scaled.lines:
        line.points = [
            [round_coord(pt[0] * factor), round_coord(pt[1] * factor)]
            for pt in line.points
            if len(pt) >= 2
        ]

    if scaled.image_width:
        scaled.image_width = int(round(scaled.image_width * factor))
    if scaled.image_height:
        scaled.image_height = int(round(scaled.image_height * factor))

    return enrich_label_record(scaled)


def image_size(path: Path) -> tuple[int, int] | None:
    if not path.exists():
        return None
    with Image.open(path) as im:
        return im.size


def detect_scale_factor(
    record: LabelRecord,
    raw_dir: Path | None = None,
    actual_size: tuple[int, int] | None = None,
) -> float | None:
    """Wspolczynnik actual/stored gdy PNG ma inne wymiary niz zapisane w rekordzie."""
    size = actual_size
    if size is None:
        src = find_raw_image(record, raw_dir)
        if src is None:
            return None
        size = image_size(src)
    if size is None:
        return None

    aw, ah = size
    sw, sh = record.image_width, record.image_height
    if not sw or not sh:
        return None

    fx = aw / sw
    fy = ah / sh
    if abs(fx - fy) > 0.02:
        return None
    if abs(fx - 1.0) < 0.01:
        return None
    return fx


def detect_low_dpi_factor(
    record: LabelRecord,
    extent_threshold: float = 0.52,
) -> float | None:
    """Heurystyka: wymiary PNG OK, ale bboxy obejmuja tylko maly fragment strony.

    Wystepuje gdy image_width zostal zsynchronizowany bez przeskalowania wspolrzednych
    po re-rasterze 200->400 DPI.
    """
    from backend.runtime_config import legacy_pdf_dpi, pdf_dpi

    target = pdf_dpi()
    legacy = legacy_pdf_dpi()
    if target <= legacy:
        return None
    dpi_factor = target / legacy

    if not record.bboxes or not record.image_width or not record.image_height:
        return None

    max_right = max(b.x + b.width for b in record.bboxes)
    max_bottom = max(b.y + b.height for b in record.bboxes)
    rx = max_right / record.image_width
    ry = max_bottom / record.image_height
    if rx >= extent_threshold or ry >= extent_threshold:
        return None
    # Pomijaj strony z diagramem w waskim pasie (np. tylko gorna polowa szerokosci).
    if min(rx, ry) < 0.38:
        return None
    return dpi_factor


def sync_image_dimensions(
    record: LabelRecord,
    raw_dir: Path | None = None,
    actual_size: tuple[int, int] | None = None,
) -> LabelRecord:
    """Ustaw image_width/height na rzeczywiste wymiary PNG (bez skalowania bboxow)."""
    size = actual_size
    if size is None:
        src = find_raw_image(record, raw_dir)
        if src is None:
            return record
        size = image_size(src)
    if size is None:
        return record

    synced = record.model_copy(deep=True)
    synced.image_width, synced.image_height = size
    return synced
