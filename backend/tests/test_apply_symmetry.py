"""Testy scripts/apply_symmetry.py (prompt 028, Czesc B).

Kluczowe: DRY-RUN nie dotyka pliku, scalanie nie kasuje wiedzy o klasach spoza
symmetry.json (przeglad jednej klasy przez `--class` nie moze wyczyscic reszty),
zapis jest atomowy.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest
import yaml

from backend.symmetry import SymmetryConfig, SymmetrySpec, dump_symmetry, load_symmetry_file

_SCRIPT = Path(__file__).resolve().parents[2] / "scripts" / "apply_symmetry.py"


@pytest.fixture(scope="module")
def aps():
    spec = importlib.util.spec_from_file_location("apply_symmetry", _SCRIPT)
    if spec is None or spec.loader is None:  # pragma: no cover
        pytest.skip("brak scripts/apply_symmetry.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_parse_incoming_odrzuca_rotacje_spoza_90(aps):
    specs, warn = aps.parse_incoming(
        {"x": {"mirror_h": True, "rotations": [90, 45, 180]}}, set()
    )
    assert specs["x"].rotations == (90, 180)
    assert any("45" in w for w in warn)


def test_parse_incoming_zly_wpis_pomijany(aps):
    specs, warn = aps.parse_incoming({"x": "napis", "y": {"mirror_v": True}}, set())
    assert "x" not in specs and specs["y"].mirror_v
    assert warn


def test_parse_incoming_brak_pol_to_brak_zgody(aps):
    specs, _ = aps.parse_incoming({"x": {}}, set())
    assert not specs["x"].any_allowed


def test_merge_scala_nie_nadpisuje(aps):
    current = SymmetryConfig(specs={
        "zlaczka": SymmetrySpec(True, True, (90,), "okragla"),
        "lampka": SymmetrySpec(True),
    })
    incoming = {"lampka": SymmetrySpec(mirror_v=True)}
    merged, changes = aps.merge(current, incoming)
    assert merged.get("zlaczka").mirror_h, "klasa spoza symmetry.json musi przetrwac"
    assert merged.get("lampka").mirror_v and not merged.get("lampka").mirror_h
    assert [c[0] for c in changes] == ["lampka"]


def test_merge_replace_kasuje_reszte(aps):
    current = SymmetryConfig(specs={"zlaczka": SymmetrySpec(True), "lampka": SymmetrySpec(True)})
    merged, changes = aps.merge(current, {"lampka": SymmetrySpec(True)}, replace=True)
    assert set(merged.specs) == {"lampka"}
    assert any(c[0] == "zlaczka" and c[2] == "(usuniete)" for c in changes)


def test_merge_zachowuje_note_z_yaml(aps):
    """UI nie odsyla `note` — uzasadnienie z pliku nie moze zginac."""
    current = SymmetryConfig(specs={"x": SymmetrySpec(True, note="powod z repo")})
    merged, _ = aps.merge(current, {"x": SymmetrySpec(mirror_h=True, mirror_v=True)})
    assert merged.get("x").note == "powod z repo"
    assert merged.get("x").mirror_v


def test_merge_bez_zmian_daje_pusta_liste(aps):
    current = SymmetryConfig(specs={"x": SymmetrySpec(True, False, (180,))})
    _merged, changes = aps.merge(current, {"x": SymmetrySpec(True, False, (180,))})
    assert changes == []


def test_konflikt_z_jawnym_zakazem_jest_wykrywany(aps):
    """Regresja: klik w UI nadał zgodę strzałce potencjału (2026-07-19)."""
    current = SymmetryConfig(specs={
        "strzalka_potencjalu_wejsciowa": SymmetrySpec(note="kierunek = znaczenie"),
    })
    incoming = {"strzalka_potencjalu_wejsciowa": SymmetrySpec(True, True, (90, 180, 270))}
    assert aps.find_denied_conflicts(current, incoming) == ["strzalka_potencjalu_wejsciowa"]


def test_zakaz_bez_uzasadnienia_nie_blokuje(aps):
    """Wpis bez `note` to nie jest udokumentowana decyzja — nie blokujemy."""
    current = SymmetryConfig(specs={"x": SymmetrySpec()})
    assert aps.find_denied_conflicts(current, {"x": SymmetrySpec(True)}) == []


def test_klasa_bez_wpisu_nie_jest_konfliktem(aps):
    """Nadanie zgody klasie bez wpisu to normalna praca przegladu."""
    current = SymmetryConfig(specs={})
    assert aps.find_denied_conflicts(current, {"lampka": SymmetrySpec(True)}) == []


def test_zgodne_potwierdzenie_zakazu_nie_jest_konfliktem(aps):
    """symmetry.json potwierdzajacy zakaz (same false) nie moze blokowac zapisu."""
    current = SymmetryConfig(specs={"x": SymmetrySpec(note="powod")})
    assert aps.find_denied_conflicts(current, {"x": SymmetrySpec()}) == []


def test_write_atomic_nie_zostawia_tmp(tmp_path, aps):
    out = tmp_path / "symbol-symmetry.yaml"
    aps.write_atomic(out, "symmetry: {}\n")
    assert out.read_text(encoding="utf-8") == "symmetry: {}\n"
    assert not list(tmp_path.glob("*.tmp")), "plik tymczasowy musi zniknac"


def test_write_atomic_nadpisuje_istniejacy(tmp_path, aps):
    out = tmp_path / "s.yaml"
    out.write_text("stare\n", encoding="utf-8")
    aps.write_atomic(out, "nowe\n")
    assert out.read_text(encoding="utf-8") == "nowe\n"


def test_pelny_cykl_dump_i_odczyt(tmp_path, aps):
    """symmetry.json -> merge -> zapis -> odczyt daje ten sam stan."""
    current = load_symmetry_file(tmp_path / "brak.yaml")
    incoming, _ = aps.parse_incoming(
        {"zlaczka": {"mirror_h": True, "mirror_v": True, "rotations": [90, 180, 270]},
         "lampka": {"mirror_h": False, "rotations": []}},
        set(),
    )
    merged, _ = aps.merge(current, incoming)
    out = tmp_path / "symbol-symmetry.yaml"
    aps.write_atomic(out, dump_symmetry(merged))

    back = load_symmetry_file(out)
    assert not back.warnings
    assert back.get("zlaczka").rotations == (90, 180, 270)
    assert not back.get("lampka").any_allowed
    assert yaml.safe_load(out.read_text(encoding="utf-8"))["symmetry"]
