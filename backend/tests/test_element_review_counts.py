"""Regresja prompt 028 Czesc A: element_review liczy tak samo jak class_report.

Historyczny blad: `element_review.py` klasyfikowal przez `tag_to_class(tag)`,
a `class_report.py` przez `bbox_class(class_name, tag)`. Bbox z `type=styki`
i tagiem "SAF1" (oznaczenie z rysunku) trafial w przegladarce do pseudoklasy
`saf1`. Stad 163 w raporcie vs 160 w przegladarce — cicha rozbieznosc, na
podstawie ktorej uzytkownik podejmowal decyzje o danych, ktorych nie widzial.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

import numpy as np
import pytest

from backend.class_map import class_distribution, load_palette_map
from backend.models.label import BboxAnnotation, LabelRecord

_SCRIPT = Path(__file__).resolve().parents[2] / "scripts" / "element_review.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("element_review", _SCRIPT)
    if spec is None or spec.loader is None:  # pragma: no cover
        pytest.skip("brak scripts/element_review.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _bbox(bid, class_name, tag, x=0, y=0):
    return BboxAnnotation(
        id=bid, class_name=class_name, x=x, y=y, width=10, height=10, tag=tag
    )


def _rec(bboxes):
    return LabelRecord(
        page_id="p001", image_path="p001.png",
        image_width=200, image_height=200, bboxes=bboxes,
    )


@pytest.fixture(scope="module")
def er():
    return _load_module()


def test_typ_ma_pierwszenstwo_nad_tagiem(er):
    """Trzy bboxy `type=styki` z tagami SAF1/2/3 to JEDNA klasa, nie cztery."""
    rec = _rec([
        _bbox("b0", "styki", "", x=0),
        _bbox("b1", "styki", "SAF1", x=20),
        _bbox("b2", "styki", "SAF2", x=40),
        _bbox("b3", "styki", "SAF3", x=60),
    ])
    page = np.full((200, 200), 255, dtype=np.uint8)
    items, dist, skipped = er.collect_items([rec], {"p001": page})
    assert not skipped
    assert dist["styki"] == 4
    assert {it[0] for it in items} == {"styki"}
    assert not any(c.startswith("saf") for c in dist)


def test_rozklad_zgodny_z_class_report(er):
    """dist_all z collect_items == class_distribution (to samo zrodlo prawdy)."""
    rec = _rec([
        _bbox("b0", "styki", "SAF1", x=0),
        _bbox("b1", "element", "zlaczka", x=20),
        _bbox("b2", "zlaczka", "", x=40),
        _bbox("b3", "lampka", "H1", x=60),
    ])
    page = np.full((200, 200), 255, dtype=np.uint8)
    _items, dist, _skipped = er.collect_items([rec], {"p001": page})
    expected = class_distribution([rec], load_palette_map())
    assert dict(dist) == dict(expected)


def test_brak_png_jest_raportowany_nie_pomijany(er):
    """Bez PNG strony element NIE moze zniknac po cichu — ma trafic do skipped."""
    rec = _rec([_bbox("b0", "styki", "")])
    items, dist, skipped = er.collect_items([rec], {})  # brak obrazu strony
    assert items == []
    assert dist["styki"] == 1, "licznik GT musi zostac, mimo braku obrazu"
    assert len(skipped) == 1
    assert skipped[0][3] == er.SKIP_NO_PAGE_IMAGE


def test_bbox_poza_kadrem_jest_raportowany(er):
    """Bbox poza obrazem daje pusty crop -> jawny powod, nie ciche `continue`."""
    rec = _rec([_bbox("b0", "styki", "", x=5000, y=5000)])
    page = np.full((200, 200), 255, dtype=np.uint8)
    items, dist, skipped = er.collect_items([rec], {"p001": page})
    assert items == []
    assert dist["styki"] == 1
    assert skipped[0][3] == er.SKIP_EMPTY_CROP


def test_bbox_bez_typu_i_tagu_jest_raportowany(er):
    rec = _rec([_bbox("b0", "element", "")])
    page = np.full((200, 200), 255, dtype=np.uint8)
    items, dist, skipped = er.collect_items([rec], {"p001": page})
    assert items == []
    assert sum(dist.values()) == 0
    assert skipped[0][3] == er.SKIP_NO_CLASS


def test_filtr_klasy_nie_psuje_licznika_globalnego(er):
    """--class filtruje siatke, ale dist_all zostaje pelny (porownanie z raportem)."""
    rec = _rec([
        _bbox("b0", "styki", "", x=0),
        _bbox("b1", "lampka", "", x=20),
    ])
    page = np.full((200, 200), 255, dtype=np.uint8)
    items, dist, _skipped = er.collect_items([rec], {"p001": page}, only_class="styki")
    assert {it[0] for it in items} == {"styki"}
    assert dist["styki"] == 1 and dist["lampka"] == 1
