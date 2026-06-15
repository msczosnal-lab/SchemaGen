"""Testy licznika uzycia hasel."""

import sqlite3

from backend.db import bump_tag_usage, get_tag_usage_map, init_db
from backend.tag_usage import record_tag_usage


def test_bump_tag_usage_counts(tmp_path, monkeypatch):
    db = tmp_path / "test.db"
    monkeypatch.setattr("backend.db.DB_PATH", db)
    init_db()

    assert bump_tag_usage(["Stycznik", "stycznik", ""]) == 2
    usage = get_tag_usage_map()
    assert len(usage) == 1
    label, count = usage["stycznik"]
    assert count == 2
    assert label == "stycznik"


def test_record_tag_usage_registers_catalog(tmp_path, monkeypatch):
    db = tmp_path / "test.db"
    cat = tmp_path / "element-catalog.yaml"
    cat.write_text("elements: []\n", encoding="utf-8")
    monkeypatch.setattr("backend.db.DB_PATH", db)
    monkeypatch.setattr("backend.catalog.CATALOG_PATH", cat)
    init_db()

    stats = record_tag_usage(["Modul zasilania RUPS1"])
    assert stats["bumped"] == 1
    assert stats["catalog_added"] == 1

    usage = get_tag_usage_map()
    assert usage["modul zasilania rups1"][1] == 1

    data = cat.read_text(encoding="utf-8")
    assert "Modul zasilania RUPS1" in data
