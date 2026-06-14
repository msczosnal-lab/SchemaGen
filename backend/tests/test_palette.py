"""Testy palety kolorow semantycznych."""

from backend.colors.palette import load_palette


def test_palette_loads_groups() -> None:
    palette = load_palette()
    assert "cable" in palette.groups
    assert "inverter" in palette.groups


def test_match_color_cable_black() -> None:
    palette = load_palette()
    assert palette.match_color("#000000") == "cable"


def test_match_color_inverter_purple() -> None:
    palette = load_palette()
    assert palette.match_color("#9933FF") == "inverter"


def test_resolve_stroke_cable() -> None:
    palette = load_palette()
    style = palette.resolve_stroke("cable", role="wire")
    assert style.stroke == "#000000"
    assert style.style == "solid"


def test_group_for_motor() -> None:
    palette = load_palette()
    assert palette.group_for_component_type("motor") == "motor_device"
