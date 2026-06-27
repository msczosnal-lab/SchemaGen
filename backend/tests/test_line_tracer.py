"""Testy LineTracer — wykrywanie segmentow + sampling koloru."""

import numpy as np

from backend.recognize.line_tracer import (
    LineSegment,
    LineTracer,
    auto_line_params,
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
