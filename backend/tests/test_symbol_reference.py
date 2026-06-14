"""Testy walidacji config/symbol-reference.yaml oraz modulu reference.py."""

import pytest

from backend.atlas.reference import load_symbol_reference, lookup_by_alias, lookup_by_id

REQUIRED_FIELDS = {"id", "yolo_class", "default_description", "atlas_crop", "source_refs"}
VALID_YOLO_CLASSES = {"element"}


def test_yaml_loads():
    data = load_symbol_reference()
    assert isinstance(data, dict)
    assert "symbols" in data
    assert "meta" in data
    assert isinstance(data["symbols"], list)


def test_has_symbols():
    data = load_symbol_reference()
    assert len(data["symbols"]) >= 1, "symbol-reference.yaml nie ma zadnych wpisow"


def test_ids_unique():
    data = load_symbol_reference()
    ids = [s.get("id") for s in data["symbols"]]
    assert len(ids) == len(set(filter(None, ids))), "Zduplikowane ID symboli"


def test_required_fields_present():
    data = load_symbol_reference()
    for sym in data["symbols"]:
        missing = REQUIRED_FIELDS - set(sym.keys())
        assert not missing, f"Symbol {sym.get('id')!r} brakuje pol: {missing}"


def test_source_refs_non_empty():
    data = load_symbol_reference()
    for sym in data["symbols"]:
        refs = sym.get("source_refs", [])
        assert isinstance(refs, list) and len(refs) > 0, (
            f"Symbol {sym.get('id')!r} ma puste source_refs"
        )


def test_yolo_class_valid():
    data = load_symbol_reference()
    for sym in data["symbols"]:
        cls = sym.get("yolo_class")
        assert cls in VALID_YOLO_CLASSES, f"Nieznana yolo_class={cls!r} w {sym.get('id')!r}"


def test_lookup_by_id_found():
    data = load_symbol_reference()
    if not data["symbols"]:
        pytest.skip("Brak symboli")
    sym = data["symbols"][0]
    result = lookup_by_id(sym["id"])
    assert result is not None
    assert result["id"] == sym["id"]


def test_lookup_by_id_missing():
    result = lookup_by_id("__nie_istnieje__")
    assert result is None


def test_lookup_by_alias_pl():
    data = load_symbol_reference()
    for sym in data["symbols"]:
        aliases = sym.get("aliases_pl", [])
        if aliases:
            result = lookup_by_alias(aliases[0])
            assert result is not None
            assert result["id"] == sym["id"]
            # Case-insensitive
            result2 = lookup_by_alias(aliases[0].upper())
            assert result2 is not None
            return
    pytest.skip("Brak symboli z aliases_pl")


def test_lookup_by_alias_missing():
    result = lookup_by_alias("__brak_takiego_aliasu__")
    assert result is None


def test_meta_structure():
    data = load_symbol_reference()
    meta = data["meta"]
    assert meta.get("version") == 1
    assert "sources" in meta
    assert isinstance(meta["sources"], list)
    assert len(meta["sources"]) >= 1
