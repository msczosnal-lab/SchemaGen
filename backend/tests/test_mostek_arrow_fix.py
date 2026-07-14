"""Testy derive_mostek_terminals i arrow_supplement."""

from __future__ import annotations

import numpy as np

from backend.models.detection import SymbolDetection
from backend.models.schema import Component
from backend.recognize.mostek_terminals import (
    _ring_index_to_uv,
    _stub_rel_positions,
    derive_mostek_terminals,
)
from backend.recognize.net_builder import derive_auto_terminals


def test_ring_index_to_uv_corners() -> None:
    assert _ring_index_to_uv(0, 10, 20) == (0.0, 0.0)
    assert _ring_index_to_uv(19, 10, 20) == (1.0, 0.0)
    assert _ring_index_to_uv(20, 10, 20) == (1.0, 1 / 9)
    assert _ring_index_to_uv(20 + 8, 10, 20) == (1.0, 1.0)


def test_stub_rel_positions_three_sides() -> None:
    """Sztuczny crop: 3 segmenty tuszu na lewo/prawo/dol -> 3 stub rel."""
    h, w = 20, 30
    b = np.zeros((h, w), dtype=np.float32)
    b[5:8, 0] = 1.0  # left
    b[5:8, -1] = 1.0  # right
    b[-1, 10:13] = 1.0  # bottom
    rel = _stub_rel_positions(b)
    assert len(rel) == 3


def test_derive_auto_terminals_merge_tol_not_page_tol() -> None:
    """Duzy tol strony nie scala dwoch stubow ~30px od siebie przy merge_tol=12."""
    from backend.models.schema import GraphicLine

    comp = Component(id="X", type="terminal_block", bbox=[0, 0, 100, 20], source="yolo")
    l1 = GraphicLine(id="l1", points=[[20, 0], [20, -40]], role="wire", semantic_group="cable")
    l2 = GraphicLine(id="l2", points=[[55, 0], [55, -40]], role="wire", semantic_group="cable")
    terms = derive_auto_terminals(comp, [l1, l2], tol=80.0, merge_tol=12.0)
    assert len(terms) == 2


def test_derive_mostek_terminals_from_synthetic_crop() -> None:
    """3 stuby na obwodzie syntetycznego mostka."""
    h, w = 40, 60
    crop = np.full((h, w, 3), 255, dtype=np.uint8)
    # tusz = ciemny
    crop[0, 20:24] = 0
    crop[10:14, -1] = 0
    crop[-1, 25:29] = 0
    crop[12:16, 0] = 0
    # tylko 3 segmenty: left, right, bottom
    crop[0, :] = 255
    crop[12:16, 0] = 0
    crop[10:14, -1] = 0
    crop[-1, 25:29] = 0

    comp = Component(
        id="M1",
        type="mostek",
        bbox=[0, 0, float(w), float(h)],
        source="yolo",
    )
    terms = derive_mostek_terminals(comp, crop)
    assert len(terms) == 3


def test_arrow_supplement_skips_when_yolo_found() -> None:
    from backend.recognize.arrow_supplement import supplement_arrow_detections

    img = np.zeros((200, 200, 3), dtype=np.uint8)
    yolo = [
        SymbolDetection(
            class_id=7,
            class_name="strzalka_potencjalu_wejsciowa",
            confidence=0.9,
            x=10,
            y=10,
            width=20,
            height=10,
        )
    ]
    out = supplement_arrow_detections(img, yolo)
    assert len(out) == 1


def test_refine_arrow_bboxes_tightens_wide_yolo_box(monkeypatch) -> None:
    from backend.recognize import arrow_supplement as mod

    tmpl = np.full((10, 30), 200, dtype=np.uint8)
    tmpl[:, 10:20] = 30
    monkeypatch.setattr(mod, "_template_gallery", lambda: {"strzalka_potencjalu_wejsciowa": [tmpl]})
    monkeypatch.setattr(
        mod,
        "arrow_supplement_settings",
        lambda: {
            "refine_enabled": True,
            "refine_min_score": 0.5,
            "refine_roi_margin": 0.5,
            "scales": [1.0],
        },
    )

    img = np.full((80, 120, 3), 255, dtype=np.uint8)
    img[25:35, 40:70] = 30
    wide = SymbolDetection(
        class_id=7,
        class_name="strzalka_potencjalu_wejsciowa",
        confidence=0.9,
        x=20,
        y=15,
        width=80,
        height=40,
    )
    [refined] = mod.refine_arrow_bboxes(img, [wide])
    assert refined.width < wide.width
    assert refined.height <= wide.height


def test_coarse_peak_hits_limits_duplicates(monkeypatch) -> None:
    """Peak NMS zwraca jedno trafienie na lokalne maksimum, nie setke z np.where."""
    from backend.recognize import arrow_supplement as mod

    tmpl = np.full((10, 30), 200, dtype=np.uint8)
    tmpl[:, 12:18] = 30
    gray = np.full((60, 80), 220, dtype=np.uint8)
    gray[20:30, 25:55] = 30
    hits = mod._coarse_peak_hits(
        gray,
        {"strzalka_potencjalu_wejsciowa": [tmpl], "strzalka_potencjalu_wyjsciowa": []},
        ["strzalka_potencjalu_wejsciowa"],
        coarse_score=0.5,
        roi_frac=1.0,
        scales=[1.0],
        downscale=1.0,
        max_peaks_per_template=8,
    )
    assert 1 <= len(hits) <= 4

    """Skala szablonu przy downscale < 1 musi sledzic skale obrazu."""
    from backend.recognize.arrow_supplement import _template_scale

    assert _template_scale(1.0, 0.5) == 0.5
    assert _template_scale(1.0, 1.0) == 1.0
    assert _template_scale(0.8, 0.5) == 0.4
