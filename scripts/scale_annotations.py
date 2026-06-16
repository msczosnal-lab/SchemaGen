"""Skaluj adnotacje w SQLite do aktualnych PNG (bboxy, linie, teksty).

Uzycie:
    python scripts/scale_annotations.py --dry-run
    python scripts/scale_annotations.py --apply
    python scripts/scale_annotations.py --apply --factor 2.0
"""

from __future__ import annotations

import argparse
import json
import sqlite3
from pathlib import Path

from backend.db import save_annotation
from backend.geometry.coord_scale import (
    detect_low_dpi_factor,
    detect_scale_factor,
    scale_label_record,
    sync_image_dimensions,
)
from backend.models.label import LabelRecord
from backend.paths import DB_PATH, RAW, ROOT
from backend.runtime_config import legacy_pdf_dpi, pdf_dpi

ANNOTATION_DPI_MARKER = ROOT / "data" / ".annotation_dpi"


def _annotation_dpi_applied() -> int:
    if ANNOTATION_DPI_MARKER.exists():
        return int(ANNOTATION_DPI_MARKER.read_text(encoding="utf-8").strip())
    return legacy_pdf_dpi()


def _mark_annotation_dpi(dpi: int) -> None:
    ANNOTATION_DPI_MARKER.parent.mkdir(parents=True, exist_ok=True)
    ANNOTATION_DPI_MARKER.write_text(str(dpi), encoding="utf-8")


def _dpi_factor() -> float | None:
    applied = _annotation_dpi_applied()
    target = pdf_dpi()
    if applied >= target:
        return None
    return target / applied


def scale_all(
    apply: bool,
    factor_override: float | None = None,
    use_dpi_fallback: bool = True,
) -> int:
    if not DB_PATH.exists():
        print(f"Brak bazy: {DB_PATH}")
        return 0

    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute("SELECT page_id, payload_json FROM annotations").fetchall()
    conn.close()

    updated = 0
    dpi_factor = _dpi_factor() if use_dpi_fallback else None

    for page_id, payload_json in rows:
        data = json.loads(payload_json)
        record = LabelRecord.model_validate(data)
        if not record.bboxes and not record.lines and not record.texts:
            continue

        factor = factor_override or detect_scale_factor(record, RAW)
        source = "png"
        if factor is None:
            factor = detect_low_dpi_factor(record)
            source = "extent"
        if factor is None and dpi_factor is not None and not record.image_width:
            factor = dpi_factor
            source = "dpi"

        if factor is None:
            synced = sync_image_dimensions(record, RAW)
            if (
                synced.image_width != record.image_width
                or synced.image_height != record.image_height
            ):
                print(
                    f"{page_id}: sync wymiary -> "
                    f"{synced.image_width}x{synced.image_height} (bez skalowania bbox)"
                )
                if apply:
                    save_annotation(page_id, synced.model_dump())
            continue

        scaled = scale_label_record(record, factor)
        scaled = sync_image_dimensions(scaled, RAW)
        n_bbox = len(scaled.bboxes)
        n_line_pts = sum(len(ln.points) for ln in scaled.lines)
        n_text = len(scaled.texts)
        print(
            f"{page_id}: x{factor:.3f} ({source}) -> "
            f"{scaled.image_width}x{scaled.image_height}, "
            f"{n_bbox} bbox, {n_line_pts} pkt linii, {n_text} tekstow"
        )
        updated += 1
        if apply:
            save_annotation(page_id, scaled.model_dump())

    if apply and updated and use_dpi_fallback and dpi_factor is not None:
        _mark_annotation_dpi(pdf_dpi())

    action = "Zaktualizowano" if apply else "Do skalowania"
    print(f"\n{action}: {updated} stron")
    if not apply and updated:
        print("Dodaj --apply aby zapisac do SQLite.")
    return updated


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true")
    parser.add_argument(
        "--factor",
        type=float,
        default=None,
        help="Wymuszony wspolczynnik (np. 2.0 przy 200->400 DPI)",
    )
    parser.add_argument(
        "--no-dpi-fallback",
        action="store_true",
        help="Tylko porownanie PNG vs image_width w rekordzie",
    )
    args = parser.parse_args()

    print(
        f"DPI config: {pdf_dpi()} (marker adnotacji: {_annotation_dpi_applied()})"
    )
    scale_all(
        apply=args.apply,
        factor_override=args.factor,
        use_dpi_fallback=not args.no_dpi_fallback,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
