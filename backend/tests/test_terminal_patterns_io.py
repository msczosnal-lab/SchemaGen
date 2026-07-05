"""Testy zapisu wzorcow terminali per klasa."""

from pathlib import Path

from backend.recognize.terminal_patterns_io import (
    build_pattern_from_bboxes,
    load_patterns,
    rel_to_edge_frac,
    save_class_pattern,
)


def test_rel_to_edge_frac_left_right() -> None:
    assert rel_to_edge_frac(0.0, 0.5) == ("left", 0.5)
    assert rel_to_edge_frac(1.0, 0.5) == ("right", 0.5)


def test_build_pattern_averages_zlaczka() -> None:
    bboxes = [
        {"terminals": [{"x": 0.0, "y": 0.5}, {"x": 1.0, "y": 0.5}]},
        {"terminals": [{"x": 0.0, "y": 0.48}, {"x": 1.0, "y": 0.52}]},
    ]
    pat = build_pattern_from_bboxes(bboxes)
    assert pat["method"] == "line-contact"
    edges = {s["edge"]: s["frac"] for s in pat["expected"]}
    assert abs(edges["left"] - 0.49) < 0.02
    assert abs(edges["right"] - 0.51) < 0.02
    assert all(s["required"] for s in pat["expected"])


def test_save_class_pattern_roundtrip(tmp_path: Path) -> None:
    p = tmp_path / "terminal-patterns.yaml"
    pat = {"method": "delegate"}
    save_class_pattern("mostek", pat, path=p)
    loaded = load_patterns(p)
    assert loaded["classes"]["mostek"]["method"] == "delegate"
