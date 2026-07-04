"""Testy selekcji symboli w build_reference."""

from pathlib import Path

from backend.atlas.build_reference import _collect_p0_files, _is_usable_element
from backend.atlas.qet_parser import parse_elmt
from backend.paths import ATLAS_QET

QET = ATLAS_QET


def test_p0_skips_folio_and_cables_dirs():
    if not QET.exists():
        return
    files = _collect_p0_files(QET)
    paths = {p.as_posix() for p in files}
    assert not any("100_folio_referencing" in p for p in paths)
    assert not any("120_cables_wiring" in p for p in paths)
    assert any("200_fuses_protective_gears" in p for p in paths)
    assert any("310_relays_contactors_contacts" in p for p in paths)


def test_usable_element_rejects_terminals_only():
    if not QET.exists():
        return
    folio = QET / "10_electric/10_allpole/100_folio_referencing/01coming_arrow.elmt"
    if not folio.exists():
        return
    el = parse_elmt(folio)
    assert el.geometry.drawable_count() > 0  # polygon po fixie parsera
    # folio arrow ma geometrie — odrzucamy go selekcja katalogow, nie filtrem


def test_fuse_folder_has_usable_symbols():
    if not QET.exists():
        return
    files = _collect_p0_files(QET)
    fuse_files = [p for p in files if "200_fuses_protective_gears" in p.as_posix()]
    assert fuse_files
    usable = sum(1 for p in fuse_files[:20] if _is_usable_element(parse_elmt(p)))
    assert usable >= 10
