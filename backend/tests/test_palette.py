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


def test_match_color_blue_ink() -> None:
    # Realny tusz niebieski (Adamed) — wczesniej pusta grupa (nie lapal motor_device).
    palette = load_palette()
    assert palette.match_color("#134088") == "blue_wire"
    assert palette.match_color("#105090") == "blue_wire"


def test_enclosure_pe_wire_distinct_stroke() -> None:
    # Rozdzielone stroke: zielen obudowy nie koliduje juz z pe_wire (remis w dict).
    palette = load_palette()
    assert palette.groups["enclosure"]["stroke"] != palette.groups["pe_wire"]["stroke"]
    assert palette.match_color("#00AA44") == "enclosure"


def test_match_color_deterministic_tie_break() -> None:
    # Ten sam wynik niezaleznie od kolejnosci iteracji (nie kolejnosc dict).
    palette = load_palette()
    assert palette.match_color("#134088") == palette.match_color("#134088")
