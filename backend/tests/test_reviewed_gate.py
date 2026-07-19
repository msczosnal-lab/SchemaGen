"""Bramka przegladu: do treningu ida tylko klasy oznaczone "przejrzana".

Asymetria wzgledem symbol-symmetry.yaml jest CELOWA i tu testowana:
- symetria: brak wpisu = ZAKAZ (bledna zgoda psuje etykiety),
- przeglad: pusta lista = bramka NIEAKTYWNA (pusty plik nie moze wyzerowac
  calego datasetu i wywrocic treningu bez czytelnej przyczyny).
"""

from __future__ import annotations

import pytest

from backend import class_map
from backend.class_map import build_class_map, is_reviewed
from backend.models.label import BboxAnnotation, LabelRecord


def _rec(page_id: str, types: list[str]) -> LabelRecord:
    return LabelRecord(
        page_id=page_id, image_path=f"{page_id}.png",
        image_width=1000, image_height=1000,
        bboxes=[
            BboxAnnotation(id=f"{page_id}_{i}", class_name=t, x=i * 10, y=0,
                           width=5, height=5)
            for i, t in enumerate(types)
        ],
    )


@pytest.fixture
def records():
    # 6x zlaczka, 6x lampka, 6x przycisk — wszystkie >= min_count 5
    return [_rec("p1", ["zlaczka"] * 6 + ["lampka"] * 6 + ["przycisk"] * 6)]


def _clear():
    # po monkeypatch to zwykla funkcja bez lru_cache — teardown nie moze na tym padac
    clear = getattr(class_map.load_reviewed_classes, "cache_clear", None)
    if clear:
        clear()


@pytest.fixture(autouse=True)
def _clear_cache():
    _clear()
    yield
    _clear()


def _set_reviewed(monkeypatch, names):
    monkeypatch.setattr(class_map, "load_reviewed_classes", lambda: frozenset(names))


def test_pusta_lista_nie_blokuje_niczego(records, monkeypatch):
    """Brak pliku = bramka nieaktywna. Pusty plik NIE MOZE wyzerowac datasetu."""
    _set_reviewed(monkeypatch, [])
    cmap, _dist = build_class_map(records, min_count=5, bucket_rare=False)
    assert set(cmap) == {"zlaczka", "lampka", "przycisk"}


def test_bramka_przepuszcza_tylko_zatwierdzone(records, monkeypatch):
    _set_reviewed(monkeypatch, ["zlaczka", "lampka"])
    cmap, _dist = build_class_map(records, min_count=5, bucket_rare=False)
    assert set(cmap) == {"zlaczka", "lampka"}
    assert "przycisk" not in cmap


def test_dist_zostaje_pelny_mimo_bramki(records, monkeypatch):
    """Rozklad ma pokazywac WSZYSTKO — inaczej znika slad po odrzuconych klasach."""
    _set_reviewed(monkeypatch, ["zlaczka"])
    _cmap, dist = build_class_map(records, min_count=5, bucket_rare=False)
    assert dist["przycisk"] == 6
    assert dist["lampka"] == 6


def test_zatwierdzenie_klasy_ktorej_nie_ma_nie_psuje(records, monkeypatch):
    _set_reviewed(monkeypatch, ["zlaczka", "nie_ma_takiej"])
    cmap, _dist = build_class_map(records, min_count=5, bucket_rare=False)
    assert set(cmap) == {"zlaczka"}


def test_bramka_nie_omija_progu_min_count(monkeypatch):
    """Zatwierdzenie nie podnosi klasy ponizej min_count."""
    _set_reviewed(monkeypatch, ["rzadka", "zlaczka"])
    recs = [_rec("p1", ["zlaczka"] * 6 + ["rzadka"] * 2)]
    cmap, _dist = build_class_map(recs, min_count=5, bucket_rare=False)
    assert set(cmap) == {"zlaczka"}


def test_is_reviewed_domyslnie_przepuszcza():
    assert is_reviewed("cokolwiek", frozenset())
    assert is_reviewed("zlaczka", frozenset(["zlaczka"]))
    assert not is_reviewed("lampka", frozenset(["zlaczka"]))
