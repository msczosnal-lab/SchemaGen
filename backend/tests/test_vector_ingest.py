"""Testy ekstrakcji wektorowej z PDF (zadanie 034)."""

from __future__ import annotations

from pathlib import Path

import pytest

from backend.ingest.vector import (
    FilterStats,
    VectorSegment,
    _rgb01_to_hex,
    _wire_color_allowed,
    drop_t_stubs_at_mostek,
    extract_vector_page,
    filter_scheme_segments,
    filter_vector_through_wires,
    merge_l_corners,
    merge_vector_segments,
    resolve_pdf_for_image,
    vector_segments_to_line_segments,
)
from backend.models.schema import Component, GraphicLine
from backend.paths import RAW, ROOT
from backend.recognize.line_tracer import LineSegment

PDF = ROOT / "sync" / "sources" / "22_A_153_PL_Adamed_AGV_SA2_20250706.pdf"
P028 = RAW / "22_A_153_PL_Adamed_AGV_SA2_20250706_p028.png"


def test_rgb01_to_hex_black() -> None:
    assert _rgb01_to_hex((0.0, 0.0, 0.0)) == "#000000"


def test_wire_color_black_allowed() -> None:
    assert _wire_color_allowed("#000000") is True


def test_resolve_pdf_for_p028() -> None:
    if not P028.exists():
        pytest.skip("brak PNG p028")
    resolved = resolve_pdf_for_image(P028)
    assert resolved is not None
    pdf, page_no = resolved
    assert pdf.name.endswith(".pdf")
    assert page_no == 28


@pytest.mark.skipif(not PDF.exists(), reason="brak PDF w sync/sources")
def test_extract_vector_page_p028_scale() -> None:
    page = extract_vector_page(PDF, 28)
    assert page.width in (6616, 6617)
    assert page.height in (4677, 4678)
    assert len(page.lines) > 100
    assert len(page.words) > 100


@pytest.mark.skipif(not PDF.exists(), reason="brak PDF w sync/sources")
def test_filter_border_roi_sanity_p028() -> None:
    """Sanity 034a: po odsianiu ramki i tabliczki rzad wielkosci ~42 linii GT."""
    from labeler.gt_loader import load_gt_schema

    page = extract_vector_page(PDF, 28)
    stats = FilterStats()
    filtered = filter_scheme_segments(
        page.lines,
        page_size=(page.width, page.height),
        roi_bottom_frac=0.93,
        stats=stats,
    )
    gt = load_gt_schema("22_A_153_PL_Adamed_AGV_SA2_20250706_p028")
    gt_n = len(gt.graphic_lines) if gt else 42
    assert stats.after_roi < stats.raw_lines
    assert stats.after_color < 800
    assert stats.after_color > gt_n // 3


def test_merge_collinear_same_style() -> None:
    segs = [
        VectorSegment(0, 10, 50, 10, "#000000", 0.368),
        VectorSegment(52, 10, 100, 10, "#000000", 0.368),
        VectorSegment(0, 90, 50, 90, "#000000", 0.368),
    ]
    merged = merge_vector_segments(segs, page_size=(200, 200), gap_tol=12.0)
    assert len(merged) == 2
    horiz = max(merged, key=lambda s: s.length)
    assert horiz.length >= 98


def test_vector_segments_to_line_segments() -> None:
    out = vector_segments_to_line_segments(
        [VectorSegment(1, 2, 3, 4, "#112233", 0.5)]
    )
    assert len(out) == 1
    assert isinstance(out[0], LineSegment)
    assert out[0].detected_color == "#112233"


def test_merge_l_corners_joins_orthogonal() -> None:
    h = GraphicLine(id="h", points=[[0, 0], [100, 0]], role="wire")
    v = GraphicLine(id="v", points=[[100, 0], [100, 80]], role="wire")
    out = merge_l_corners([h, v], gap_tol=5.0)
    wires = [ln for ln in out if ln.role == "wire"]
    assert len(wires) == 1
    assert len(wires[0].points) == 3


def test_filter_vector_through_wires_keeps_l_with_one_symbol() -> None:
    elbow = GraphicLine(
        id="elbow",
        points=[[0, 0], [100, 0], [100, 80]],
        role="wire",
    )
    sym = Component(id="a", type="zlaczka", bbox=[80, -20, 120, 40])
    out = filter_vector_through_wires([elbow], [sym], tol=20.0)
    assert len(out) == 1 and out[0].role == "wire"


def test_filter_vector_through_wires_demotes_orphan_stub() -> None:
    stub = GraphicLine(id="stub", points=[[0, 0], [50, 0]], role="wire")
    out = filter_vector_through_wires([stub], [], tol=8.0)
    assert out[0].role == "other"


def test_drop_t_stub_at_mostek() -> None:
    bus = GraphicLine(id="bus", points=[[0, 50], [200, 50]], role="wire")
    stub = GraphicLine(id="stub", points=[[100, 50], [100, 70]], role="wire")
    mostek = Component(
        id="m1",
        type="mostek",
        bbox=[90, 45, 110, 75],
    )
    out = drop_t_stubs_at_mostek([bus, stub], [mostek], tol=10.0)
    assert len([ln for ln in out if ln.role == "wire"]) == 1
