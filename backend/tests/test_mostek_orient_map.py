"""Testy mapowania klas orientacji mostka (runtime)."""

from __future__ import annotations

from backend.recognize.mostek_orient_map import (
    ORIENT_CLASSES,
    base_symbol,
    common_terminal_side,
    is_mostek_class,
    orientation_of,
)


def test_eight_orientation_classes():
    assert len(ORIENT_CLASSES) == 8


def test_is_mostek_class():
    assert is_mostek_class("mostek")
    assert is_mostek_class("mostek_r90")
    assert is_mostek_class("mostek_m270")
    assert not is_mostek_class("relay")
    assert not is_mostek_class("mostek_xx")


def test_base_symbol_collapses_orientation():
    assert base_symbol("mostek_r180") == "mostek"
    assert base_symbol("mostek") == "mostek"
    assert base_symbol("relay") == "relay"


def test_orientation_of():
    assert orientation_of("mostek_r90") == "r90"
    assert orientation_of("mostek_m0") == "m0"
    assert orientation_of("mostek") is None          # generyczny
    assert orientation_of("relay") is None


def test_common_terminal_side_uses_mapping():
    mapping = {"r0": "left", "r90": "top"}
    assert common_terminal_side("mostek_r0", mapping) == "left"
    assert common_terminal_side("mostek_r90", mapping) == "top"
    assert common_terminal_side("mostek_r180", mapping) is None   # brak wpisu
    assert common_terminal_side("mostek", mapping) is None        # generyczny
