"""Testy modulu orientacji mostka (D4 + eksemplarz)."""

from __future__ import annotations

import numpy as np
import pytest

from train.mostek_orient import (
    CAYLEY,
    CLASS_NAMES,
    D4,
    augment_d4,
    classify_crop,
    compose,
    count_edge_crossings,
    transform_bbox_wh,
)


def _asym_crop(size: int = 24) -> np.ndarray:
    """Asymetryczny 'mostek-podobny' crop: 3 stuby + chiralne wnetrze."""
    img = np.full((size, size), 255, dtype=np.uint8)
    c = size // 2
    # trzon poziomy
    img[c, 2 : size - 2] = 0
    # stub w gore (lewo) i w dol (prawo) — lamie symetrie i chiralnosc
    img[2:c, size // 3] = 0
    img[c:-2, 2 * size // 3] = 0
    # znacznik chiralny w rogu
    img[3, 3] = 0
    img[4, 3] = 0
    return img


# --- grupa D4 -------------------------------------------------------------

def test_eight_distinct_classes():
    assert len(CLASS_NAMES) == 8
    assert len(set(CLASS_NAMES)) == 8


def test_cayley_is_group():
    # zamknietosc
    assert CAYLEY.shape == (8, 8)
    assert set(CAYLEY.ravel().tolist()) == set(range(8))
    # element neutralny (indeks 0 = r0,m0) nie zmienia klasy
    for k in range(8):
        assert compose(0, k) == k
    # kazdy wiersz i kolumna to permutacja (wlasnosc grupy / kwadrat laciński)
    for i in range(8):
        assert sorted(CAYLEY[i, :].tolist()) == list(range(8))
        assert sorted(CAYLEY[:, i].tolist()) == list(range(8))


def test_every_element_has_inverse():
    for g in range(8):
        assert any(compose(g, h) == 0 and compose(h, g) == 0 for h in range(8))


# --- augmentacja ----------------------------------------------------------

def test_augment_d4_covers_all_classes():
    crop = _asym_crop()
    for src in range(8):
        produced = [cls for _, cls in augment_d4(crop, src)]
        assert sorted(produced) == list(range(8)), f"src={src} niepelna orbita"


def test_augment_image_matches_element():
    crop = _asym_crop()
    pairs = list(augment_d4(crop, source_class=0))
    # obraz dla elementu g musi = D4[g].apply(crop)
    for g, (img, _) in enumerate(pairs):
        assert np.array_equal(img, D4[g].apply_image(crop))


# --- klasyfikacja eksemplarzem -------------------------------------------

def test_classify_recovers_orientation():
    base = _asym_crop()
    templates = [D4[g].apply_image(base) for g in range(8)]  # 8 eksemplarzy
    # kazdy szablon rozpoznany jako wlasna klasa
    for k in range(8):
        idx, score = classify_crop(templates[k], templates)
        assert idx == k
        assert score > 0.99


def test_classify_chirality_distinguished():
    """Lustro (m0) nie moze byc mylone z zadnym czystym obrotem."""
    base = _asym_crop()
    templates = [D4[g].apply_image(base) for g in range(8)]
    mirrored = D4[4].apply_image(base)  # m0
    idx, _ = classify_crop(mirrored, templates)
    assert CLASS_NAMES[idx] == "mostek_m0"


def test_classify_requires_eight_templates():
    with pytest.raises(ValueError):
        classify_crop(_asym_crop(), [_asym_crop()] * 3)


# --- pomocnicze -----------------------------------------------------------

def test_transform_bbox_wh_swaps_on_rotation():
    assert transform_bbox_wh(10, 4, D4[0]) == (10, 4)   # r0
    assert transform_bbox_wh(10, 4, D4[1]) == (4, 10)   # r90
    assert transform_bbox_wh(10, 4, D4[2]) == (10, 4)   # r180
    assert transform_bbox_wh(10, 4, D4[3]) == (4, 10)   # r270


def test_count_edge_crossings_three_stubs():
    crop = _asym_crop()
    # trzy stuby: lewy koniec trzonu, prawy koniec trzonu, dol prawego stubu,
    # gora lewego stubu -> zbudujmy kontrolowany crop z dokladnie 3 wyjsciami
    img = np.full((20, 20), 255, dtype=np.uint8)
    img[10, 0:18] = 0      # trzon dochodzi do lewej krawedzi (1)
    img[10, 18] = 0
    img[0:10, 10] = 0      # stub do gornej krawedzi (2)
    img[10:20, 15] = 0     # stub do dolnej krawedzi (3)
    assert count_edge_crossings(img) == 3


def test_count_edge_crossings_zero_on_blank():
    assert count_edge_crossings(np.full((20, 20), 255, dtype=np.uint8)) == 0
