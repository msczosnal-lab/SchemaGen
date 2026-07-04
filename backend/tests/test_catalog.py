"""Testy katalogu elementow."""

from backend.catalog import load_catalog, register_labels


def test_register_labels_dedupes(tmp_path, monkeypatch):
    cat = tmp_path / "element-catalog.yaml"
    cat.write_text("elements: []\n", encoding="utf-8")
    monkeypatch.setattr("backend.catalog.CATALOG_PATH", cat)

    assert register_labels(["Stycznik -K1"]) == 1
    assert register_labels(["Stycznik -K1", "Silnik =M1"]) == 1

    data = load_catalog()
    labels = {e["label"] for e in data["elements"]}
    assert labels == {"Stycznik -K1", "Silnik =M1"}
    assert all(e.get("id") for e in data["elements"])
