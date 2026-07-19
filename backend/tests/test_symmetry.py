"""Testy symetrii symboli (prompt 028, Czesc B).

Najwazniejszy kontrakt: BRAK WPISU = BRAK ZGODY. Odwrotny domysl (milczenie =
zgoda) cicho zatrulby dataset, bo `strzalka_potencjalu_wejsciowa` odbita
lustrzanie to `strzalka_potencjalu_wyjsciowa`.
"""

from __future__ import annotations

import pytest
import yaml

from backend.symmetry import (
    ALLOWED_ROTATIONS,
    NO_SYMMETRY,
    TRANSFORM_KEYS,
    SymmetryConfig,
    SymmetrySpec,
    dump_symmetry,
    load_symmetry_file,
    parse_symmetry,
)


# --- fail-safe: brak wpisu = brak zgody -------------------------------------

def test_brak_wpisu_zabrania_wszystkiego():
    cfg = parse_symmetry({"symmetry": {"zlaczka": {"mirror_h": True}}})
    spec = cfg.get("klasa_ktorej_nie_ma")
    assert spec is NO_SYMMETRY
    assert not spec.any_allowed
    for t in TRANSFORM_KEYS:
        assert not spec.allows(t), f"{t} nie moze byc dozwolone bez wpisu"


def test_pusty_plik_zabrania_wszystkiego():
    cfg = parse_symmetry(None)
    assert not cfg.get("zlaczka").any_allowed
    assert not cfg.allows("cokolwiek", "mirror_h")


def test_none_i_pusta_klasa_to_brak_zgody():
    cfg = parse_symmetry({"symmetry": {"lampka": None}})
    assert "lampka" in cfg
    assert not cfg.get("lampka").any_allowed
    assert not cfg.get(None).any_allowed
    assert not cfg.get("").any_allowed


def test_jawne_false_zostaje_false():
    cfg = parse_symmetry(
        {"symmetry": {"strzalka_potencjalu_wejsciowa": {
            "mirror_h": False, "mirror_v": False, "rotations": []}}}
    )
    assert not cfg.allows("strzalka_potencjalu_wejsciowa", "mirror_h")
    assert not cfg.get("strzalka_potencjalu_wejsciowa").any_allowed


# --- odczyt poprawnych wpisow ------------------------------------------------

def test_czyta_lustra_i_rotacje():
    cfg = parse_symmetry(
        {"symmetry": {"zlaczka": {
            "mirror_h": True, "mirror_v": True,
            "rotations": [90, 180, 270], "note": "okragla"}}}
    )
    spec = cfg.get("zlaczka")
    assert spec.mirror_h and spec.mirror_v
    assert spec.rotations == (90, 180, 270)
    assert spec.note == "okragla"
    assert spec.transforms() == list(TRANSFORM_KEYS)


def test_transforms_zachowuje_kolejnosc_i_podzbior():
    cfg = parse_symmetry(
        {"symmetry": {"styk_nc": {"mirror_h": True, "rotations": [180]}}}
    )
    assert cfg.get("styk_nc").transforms() == ["mirror_h", "rot180"]
    assert cfg.allows("styk_nc", "rot180")
    assert not cfg.allows("styk_nc", "rot90")
    assert not cfg.allows("styk_nc", "mirror_v")


# --- walidacja: ostrzezenie, nie wyjatek ------------------------------------

@pytest.mark.parametrize("bad_rot", [45, 30, 1, 135, -90])
def test_rotacja_spoza_wielokrotnosci_90_odrzucona_z_ostrzezeniem(bad_rot):
    cfg = parse_symmetry({"symmetry": {"x": {"rotations": [bad_rot, 180]}}})
    assert cfg.get("x").rotations == (180,)
    assert any(str(bad_rot) in w for w in cfg.warnings)


def test_rotacja_0_i_360_to_identycznosc():
    cfg = parse_symmetry({"symmetry": {"x": {"rotations": [0, 360, 90]}}})
    assert cfg.get("x").rotations == (90,)
    assert len(cfg.warnings) == 2


def test_wszystkie_dozwolone_rotacje_przechodza():
    cfg = parse_symmetry({"symmetry": {"x": {"rotations": list(ALLOWED_ROTATIONS)}}})
    assert cfg.get("x").rotations == tuple(sorted(ALLOWED_ROTATIONS))
    assert not cfg.warnings


def test_nieznana_klasa_daje_ostrzezenie_nie_wyjatek():
    cfg = parse_symmetry(
        {"symmetry": {"nie_ma_takiej": {"mirror_h": True}}},
        known_classes={"zlaczka", "lampka"},
    )
    assert cfg.get("nie_ma_takiej").mirror_h  # wpis zachowany
    assert any("nie_ma_takiej" in w for w in cfg.warnings)


def test_nieznane_klucze_ignorowane_z_ostrzezeniem():
    cfg = parse_symmetry({"symmetry": {"x": {"mirror_h": True, "flip_diag": True}}})
    assert cfg.get("x").mirror_h
    assert any("flip_diag" in w for w in cfg.warnings)


def test_zly_typ_wartosci_nie_wywraca_parsera():
    cfg = parse_symmetry(
        {"symmetry": {"a": {"mirror_h": "tak"}, "b": {"rotations": "90"}, "c": ["lista"]}}
    )
    assert not cfg.get("a").mirror_h  # "tak" != True -> fail-safe false
    assert cfg.get("b").rotations == ()
    assert not cfg.get("c").any_allowed
    assert len(cfg.warnings) >= 3


def test_zly_korzen_nie_wywraca_parsera():
    assert parse_symmetry(["lista"]).warnings
    assert parse_symmetry({"symmetry": "napis"}).warnings
    assert parse_symmetry({"inny_klucz": {}}).warnings


def test_brak_pliku_daje_ostrzezenie_i_zero_zgody(tmp_path):
    cfg = load_symmetry_file(tmp_path / "nie-ma.yaml")
    assert cfg.warnings
    assert not cfg.get("zlaczka").any_allowed


def test_zepsuty_yaml_nie_wywraca_narzedzia(tmp_path):
    p = tmp_path / "symmetry.yaml"
    p.write_text("symmetry: [niedomkniete\n", encoding="utf-8")
    cfg = load_symmetry_file(p)
    assert any("YAML" in w for w in cfg.warnings)
    assert not cfg.specs


# --- serializacja ------------------------------------------------------------

def test_dump_parse_roundtrip():
    cfg = SymmetryConfig(specs={
        "zlaczka": SymmetrySpec(True, True, (90, 180, 270), "okragla"),
        "strzalka_potencjalu_wejsciowa": SymmetrySpec(note="kierunek = znaczenie"),
    })
    text = dump_symmetry(cfg)
    back = parse_symmetry(yaml.safe_load(text))
    assert back.get("zlaczka").as_dict() == cfg.get("zlaczka").as_dict()
    assert not back.get("strzalka_potencjalu_wejsciowa").any_allowed
    assert back.get("strzalka_potencjalu_wejsciowa").note == "kierunek = znaczenie"
    assert not back.warnings


def test_dump_ma_stabilna_kolejnosc():
    cfg = SymmetryConfig(specs={
        "zlaczka": SymmetrySpec(True), "lampka": SymmetrySpec(), "aaa": SymmetrySpec()})
    text = dump_symmetry(cfg)
    assert text.index("aaa") < text.index("lampka") < text.index("zlaczka")


# --- plik w repo -------------------------------------------------------------

def test_repozytoryjny_plik_jest_poprawny():
    """config/symbol-symmetry.yaml musi sie wczytywac bez ostrzezen."""
    cfg = load_symmetry_file()
    assert not cfg.warnings, f"symbol-symmetry.yaml ma problemy: {cfg.warnings}"
    assert cfg.specs, "plik nie moze byc pusty — to udokumentowana wiedza domenowa"


def test_strzalki_potencjalu_maja_zakaz_w_repo():
    """Regresja domenowa: lustro zamienia strzalke wejsciowa w wyjsciowa."""
    cfg = load_symmetry_file()
    for cls in ("strzalka_potencjalu_wejsciowa", "strzalka_potencjalu_wyjsciowa"):
        assert cls in cfg, f"{cls} musi miec JAWNY wpis z uzasadnieniem"
        assert not cfg.get(cls).any_allowed, f"{cls} nie moze byc transformowana"
        assert cfg.get(cls).note, f"{cls}: brak uzasadnienia w note"
