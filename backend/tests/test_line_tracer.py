"""Testy LineTracer — wykrywanie segmentow + sampling koloru + auto-progi."""

import numpy as np

from backend.recognize.line_tracer import (
    LineSegment,
    LineTracer,
    auto_bus_line_params,
    auto_line_params,
    _is_axial,
    _is_page_border,
    _merge_collinear,
)


def _blank(w: int = 120, h: int = 120) -> np.ndarray:
    return np.full((h, w, 3), 255, dtype=np.uint8)


def test_trace_horizontal_black_line() -> None:
    img = _blank()
    img[60, 10:110] = (0, 0, 0)  # czarna linia pozioma (BGR)
    segments = LineTracer(min_line_length=20).trace(img)
    assert len(segments) >= 1
    longest = max(segments, key=lambda s: s.length)
    assert longest.length >= 50
    # blisko poziomu
    assert longest.angle_deg <= 8 or longest.angle_deg >= 172


def test_trace_samples_color() -> None:
    img = _blank()
    # fioletowa linia (#9933FF) -> BGR (255, 51, 153); pasek 3px by sampling trafil w srodek
    img[29:32, 10:110] = (255, 51, 153)
    segments = LineTracer(min_line_length=20).trace(img)
    assert segments
    hexes = {s.detected_color for s in segments}
    # przynajmniej jeden segment z silnym kanalem czerwonym i niebieskim (fiolet), nie biel/czern
    assert any(h not in ("", "#ffffff", "#000000") and h[1] in "89ab" for h in hexes)


def test_trace_path_not_found() -> None:
    import pytest

    with pytest.raises(FileNotFoundError):
        LineTracer().trace("__nie_istnieje__.png")


def test_merge_collinear_joins_segments() -> None:
    a = LineSegment(0, 10, 50, 10, "#000000")
    b = LineSegment(52, 10, 100, 10, "#000000")
    merged = _merge_collinear([a, b], angle_tol_deg=6, gap_tol=12)
    assert len(merged) == 1
    assert merged[0].length >= 99


def test_merge_keeps_separate_lines() -> None:
    a = LineSegment(0, 10, 50, 10, "#000000")
    b = LineSegment(0, 90, 50, 90, "#000000")  # daleko, rownolegla
    merged = _merge_collinear([a, b], angle_tol_deg=6, gap_tol=12)
    assert len(merged) == 2


def test_auto_params_scale_with_resolution() -> None:
    # frac 0.02 (skalibrowane wzrokowo na p040/p035). Adamed 6617 -> min_line_length ~132.
    min_len, hough, gap = auto_line_params(6617, 4678)
    assert min_len == round(0.02 * 6617)  # 132
    assert hough == min_len               # hough auto = max(50, min_len)
    assert gap == round(0.0015 * 6617)    # 10

    # mala strona -> podlogi (floory), nie zera
    small_len, small_hough, small_gap = auto_line_params(120, 120)
    assert small_len == 20 and small_hough == 50 and small_gap == 4


def test_explicit_params_override_auto() -> None:
    # jawny min_line_length nie jest nadpisywany przez auto-skalowanie
    tracer = LineTracer(min_line_length=20)
    assert tracer._params(6617, 4678)[0] == 20


def test_merge_collinear_bridges_node_gap() -> None:
    # Przerwa kolka wezla ~21px: stala gap_tol=12 NIE sklei, skalowany gap_tol=25 sklei.
    a = LineSegment(0, 10, 73, 10, "#000000")
    b = LineSegment(94, 10, 167, 10, "#000000")  # przerwa 21px (94-73)
    assert len(_merge_collinear([a, b], gap_tol=12)) == 2
    merged = _merge_collinear([a, b], gap_tol=25)
    assert len(merged) == 1
    assert merged[0].length >= 160


def test_bus_params_looser_than_primary() -> None:
    # Drugi przebieg (szyna): krotsza min dlugosc i wiekszy gap niz przebieg glowny.
    p_len, _p_h, p_gap = auto_line_params(6617, 4678)
    b_len, _b_h, b_gap = auto_bus_line_params(6617, 4678)
    assert b_len < p_len          # 66 < 132 -> lapie segmenty tuszu 67-76px
    assert b_gap > p_gap          # 26 > 10  -> mostkuje przerwy kolek 21-22px


def test_is_axial() -> None:
    assert _is_axial(0, 0, 100, 0, 6.0)      # poziom
    assert _is_axial(0, 0, 0, 100, 6.0)      # pion
    assert not _is_axial(0, 0, 100, 100, 6.0)  # 45 stopni


def test_trace_drops_diagonal_segments() -> None:
    img = _blank(120, 120)
    img[10:110, 10:110] = (0, 0, 0)  # skos 45°
    segments = LineTracer(min_line_length=20).trace(img)
    assert all(_is_axial(s.x1, s.y1, s.x2, s.y2, 6.0) for s in segments)


def test_second_pass_recovers_bus_rail() -> None:
    # Szyna listwy w pelnej skali: segmenty tuszu 73px z przerwami 21px (kolka wezlow).
    # Przebieg glowny (min_line_length=120 > 73) jej NIE widzi; drugi przebieg + merge
    # odtwarzaja ciagla linie pozioma na ~calej szerokosci (odtworzenie objawu p027).
    w, h = 6000, 60
    img = np.full((h, w, 3), 255, dtype=np.uint8)
    y = 30
    seg, gap = 73, 21
    x = 0
    while x < w:
        img[y - 1 : y + 2, x : min(x + seg, w)] = (0, 0, 0)
        x += seg + gap
    segments = LineTracer().trace(img)
    horiz = [s for s in segments if s.angle_deg <= 6 or s.angle_deg >= 174]
    assert horiz, "brak segmentow poziomych — drugi przebieg nie zadzialal"
    assert max(s.length for s in horiz) >= 0.7 * w


def test_page_border_segment_dropped() -> None:
    seg = LineSegment(0, 0, 5999, 0, "#000000")
    assert _is_page_border(seg, 6000, 60)
    inner = LineSegment(100, 30, 5000, 30, "#000000")
    assert not _is_page_border(inner, 6000, 60)
