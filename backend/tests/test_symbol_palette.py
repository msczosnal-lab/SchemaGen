"""Testy palety haseł labelera."""

from backend.symbol_palette import list_palette_entries, load_symbol_palette, search_palette


def test_load_symbol_palette():
    data = load_symbol_palette()
    assert "symbols" in data
    assert len(data["symbols"]) >= 40


def test_list_palette_entries():
    entries = list_palette_entries()
    assert all("label_pl" in e and "id" in e for e in entries)


def test_search_by_label_pl():
    hits = search_palette("stycznik")
    assert any(h["id"] == "contactor" for h in hits)


def test_search_by_alias():
    hits = search_palette("topikowy")
    assert any(h["id"] == "fuse" for h in hits)


def test_search_empty_returns_all_capped():
    hits = search_palette("")
    assert len(hits) >= 40
    assert len(hits) <= 30


def test_search_no_match():
    assert search_palette("xyznieistnieje123") == []
