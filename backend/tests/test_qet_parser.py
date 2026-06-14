"""Testy parsera .elmt QElectroTech — uzywaja fixture z schema/fixtures/atlas/."""

from pathlib import Path

import pytest

from backend.atlas.qet_parser import parse_elmt

FIXTURES = Path(__file__).parents[2] / "schema" / "fixtures" / "atlas"


def test_parse_fuse_names():
    el = parse_elmt(FIXTURES / "fuse.elmt")
    assert el.name_en() == "Fuse"
    assert el.name_pl() == "Bezpiecznik"


def test_parse_fuse_geometry():
    el = parse_elmt(FIXTURES / "fuse.elmt")
    assert len(el.geometry.lines) == 2
    assert len(el.geometry.rects) == 1
    assert len(el.geometry.terminals) == 2


def test_parse_fuse_slug():
    el = parse_elmt(FIXTURES / "fuse.elmt")
    assert el.slug() == "fuse"
    assert " " not in el.slug()


def test_parse_contactor_terminals():
    el = parse_elmt(FIXTURES / "contactor.elmt")
    assert len(el.geometry.terminals) == 6
    assert el.name_en() == "Contactor"
    assert el.name_pl() == "Stycznik"


def test_parse_terminal_block():
    el = parse_elmt(FIXTURES / "terminal_block.elmt")
    assert el.name_en() == "Terminal block"
    assert el.name_pl() == "Listwa zaciskowa"
    assert el.slug() == "terminal_block"


@pytest.mark.parametrize("fname", ["fuse.elmt", "contactor.elmt", "terminal_block.elmt"])
def test_bounding_box_valid(fname):
    el = parse_elmt(FIXTURES / fname)
    bb = el.geometry.bounding_box()
    assert bb is not None
    x_min, y_min, x_max, y_max = bb
    assert x_max >= x_min
    assert y_max >= y_min


@pytest.mark.parametrize("fname", ["fuse.elmt", "contactor.elmt", "terminal_block.elmt"])
def test_definition_attributes_loaded(fname):
    el = parse_elmt(FIXTURES / fname)
    assert el.width > 0
    assert el.height > 0
    assert el.hotspot_x >= 0
    assert el.hotspot_y >= 0
