"""Testy GT jako pliki JSON + cache SQLite (prompt 030)."""

from __future__ import annotations

import json

import pytest

from backend import db, gt_store


@pytest.fixture()
def tmp_db(tmp_path, monkeypatch):
    db_path = tmp_path / "test.db"
    from backend import db as db_mod
    import backend.paths as paths_mod

    monkeypatch.setattr(db_mod, "DB_PATH", db_path)
    monkeypatch.setattr(paths_mod, "DB_PATH", db_path)
    db_mod.init_db()
    yield db_path


def _payload(page_id: str, *, empty: bool = False) -> dict:
    return {
        "version": 2,
        "page_id": page_id,
        "image_width": 1000,
        "image_height": 800,
        "symbols": [] if empty else [{"id": "a", "type": "relay", "bbox": [1, 2, 3, 4], "terminals": []}],
        "lines": [],
    }


def test_sanitize_page_id():
    assert gt_store.sanitize_page_id("p040") == "p040"
    assert gt_store.sanitize_page_id("a b/c") == "a_b_c"
    assert gt_store.sanitize_page_id("") == "_"
    assert gt_store.sanitize_page_id("22_A_153.PL-x") == "22_A_153.PL-x"


def test_round_trip_file_and_load(tmp_db):
    pid = "p100"
    res = db.save_schematic_graph(pid, _payload(pid))
    assert res["status"] == "saved"
    # plik JSON istnieje i parsuje
    path = gt_store.gt_path(pid)
    assert path.exists()
    parsed = json.loads(path.read_text(encoding="utf-8"))
    assert parsed["page_id"] == pid
    # LF, ładny indent
    raw = path.read_text(encoding="utf-8")
    assert "\r\n" not in raw
    assert raw.endswith("\n")
    assert '  "version": 2' in raw
    # load zwraca to samo
    assert db.load_schematic_graph(pid) == _payload(pid)


def test_load_falls_back_to_gt_when_cache_empty(tmp_db):
    pid = "p101"
    db.save_schematic_graph(pid, _payload(pid))
    # wyczyść cache — symulacja świeżej/uszkodzonej bazy
    with db.db_session() as conn:
        conn.execute("DELETE FROM schematic_graph")
    # load musi sięgnąć do pliku gt/ i odbudować cache
    assert db.load_schematic_graph(pid) == _payload(pid)
    with db.db_session() as conn:
        row = conn.execute(
            "SELECT 1 FROM schematic_graph WHERE page_id=?", (pid,)
        ).fetchone()
    assert row is not None  # cache odbudowany


def test_rebuild_cache_from_gt(tmp_db):
    for pid in ("p200", "p201", "p202"):
        db.save_schematic_graph(pid, _payload(pid))
    with db.db_session() as conn:
        conn.execute("DELETE FROM schematic_graph")
    n = db.rebuild_cache_from_gt()
    assert n == 3
    assert db.load_schematic_graph("p201") == _payload("p201")


def test_empty_does_not_overwrite_nonempty(tmp_db):
    pid = "p300"
    db.save_schematic_graph(pid, _payload(pid))
    res = db.save_schematic_graph(pid, _payload(pid, empty=True))
    assert res["status"] == "skipped_empty_overwrite"
    # plik nienaruszony
    assert db.load_schematic_graph(pid)["symbols"]


def test_allow_empty_forces_overwrite(tmp_db):
    pid = "p301"
    db.save_schematic_graph(pid, _payload(pid))
    res = db.save_schematic_graph(pid, _payload(pid, empty=True), allow_empty=True)
    assert res["status"] == "saved"
    assert db.load_schematic_graph(pid)["symbols"] == []


def test_atomic_no_partial_file_on_error(tmp_db, monkeypatch):
    pid = "p400"
    db.save_schematic_graph(pid, _payload(pid))
    before = gt_store.gt_path(pid).read_text(encoding="utf-8")

    # wymuś wyjątek w trakcie zapisu (os.replace)
    def boom(*a, **k):
        raise RuntimeError("disk full")

    monkeypatch.setattr(gt_store.os, "replace", boom)
    with pytest.raises(RuntimeError):
        gt_store.write_gt_json(pid, _payload("p400_new"))
    # plik docelowy niezmieniony, brak plików tmp
    assert gt_store.gt_path(pid).read_text(encoding="utf-8") == before
    leftovers = list(gt_store.gt_dir().glob("*.tmp"))
    assert leftovers == []


def test_list_gt_page_ids(tmp_db):
    db.save_schematic_graph("p500", _payload("p500"))
    db.save_schematic_graph("p501", _payload("p501"))
    assert gt_store.list_gt_page_ids() == ["p500", "p501"]
