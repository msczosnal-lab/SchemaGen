"""Testy listy typow w pickerze."""

from backend.type_picker import list_type_picker


def test_type_picker_sorts_by_usage(tmp_path, monkeypatch):
    db = tmp_path / "test.db"
    monkeypatch.setattr("backend.db.DB_PATH", db)
    from backend.db import bump_tag_usage, init_db

    init_db()
    bump_tag_usage(["stycznik", "stycznik", "stycznik", "bezpiecznik"])

    results = list_type_picker("", limit=100)
    by_label = {e["label_pl"].casefold(): e for e in results}
    assert by_label["stycznik"]["usage_count"] == 3
    assert by_label["bezpiecznik"]["usage_count"] == 1

    top = [e for e in results if e["usage_count"] > 0]
    assert top[0]["label_pl"].casefold() == "stycznik"


def test_type_picker_includes_custom_catalog(tmp_path, monkeypatch):
    db = tmp_path / "test.db"
    cat = tmp_path / "element-catalog.yaml"
    cat.write_text(
        "elements:\n- id: custom_x\n  label: Zwarta listwa zlaczek\n  yolo_class: element\n",
        encoding="utf-8",
    )
    monkeypatch.setattr("backend.db.DB_PATH", db)
    monkeypatch.setattr("backend.catalog.CATALOG_PATH", cat)
    from backend.db import init_db

    init_db()
    results = list_type_picker("", limit=200)
    labels = {e["label_pl"] for e in results}
    assert "Zwarta listwa zlaczek" in labels
    custom = next(e for e in results if e["label_pl"] == "Zwarta listwa zlaczek")
    assert custom["custom"] is True
