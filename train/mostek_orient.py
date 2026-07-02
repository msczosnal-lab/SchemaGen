# COWORK_TASK: sync/prompts/012-mostek-orientacja.md
"""Orientacja mostka — grupa D4 (8 klas) + klasyfikacja eksemplarzem.

Problem: mostek (3 terminale) wystepuje w 8 orientacjach (4 obroty x lustro).
Detekcja YOLO ma zwracac orientacje wprost (osobna klasa na orientacje), a
podzial potencjalow wynika z tego, ktory z 3 stubow jest wspolny.

Ten modul dostarcza CZESC ALGORYTMICZNA, niezalezna od pipeline'u eksportu:

1. `D4` — 8 elementow grupy dihedralnej (obrot 90 CCW ^ r, po lustrze ^ m).
   Dzialaja na obraz (numpy) i na bbox wzgledny cropa.
2. `CAYLEY` — tabliczka mnozenia grupy, budowana samo-weryfikujaco z pikseli
   (bez recznej algebry -> bez pomylek). Sklada etykiete: transform g na cropie
   klasy k daje klase `compose(g, k)`.
3. `classify_crop` — realny crop -> 1 z 8 klas przez dopasowanie do 8 eksemplarzy
   (znormalizowana korelacja na binaryzacji). Zwraca (klasa, score).
4. `augment_d4` — z jednego realnego cropa (i jego klasy) generuje 8 par
   (obraz, klasa) pokrywajacych wszystkie orientacje — zbalansowany dataset.
5. `count_edge_crossings` — asercja jakosci bboxa: ile czarnych stubow przecina
   krawedz cropa. Mostek = dokladnie 3, inaczej [SKIP] w eksporcie.

Zaleznosci: tylko numpy (rdzen). Skalowanie cropow -> PIL (leniwy import).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterator

import numpy as np

# Nazwy 8 klas orientacji (kolejnosc = indeks w grupie / kanon palety).
# r = rotacja 90 CCW ^ r ; m = najpierw lustro (fliplr) gdy m=1.
CLASS_NAMES: tuple[str, ...] = (
    "mostek_r0",
    "mostek_r90",
    "mostek_r180",
    "mostek_r270",
    "mostek_m0",
    "mostek_m90",
    "mostek_m180",
    "mostek_m270",
)
NAME_TO_INDEX: dict[str, int] = {n: i for i, n in enumerate(CLASS_NAMES)}


@dataclass(frozen=True)
class D4Element:
    """Element grupy D4: mirror^m po rot90CCW^r. Indeks = m*4 + r."""

    r: int  # 0..3 obroty 90 CCW
    m: int  # 0/1 lustro w poziomie (fliplr) PRZED obrotem

    @property
    def index(self) -> int:
        return self.m * 4 + self.r

    def apply_image(self, img: np.ndarray) -> np.ndarray:
        """Zastosuj element do obrazu (H,W) lub (H,W,C). Lustro, potem obrot."""
        out = img
        if self.m:
            out = np.fliplr(out)
        if self.r:
            out = np.rot90(out, k=self.r)  # rot90 = CCW
        return np.ascontiguousarray(out)


# 8 elementow w kolejnosci indeksu = kolejnosc CLASS_NAMES.
D4: tuple[D4Element, ...] = tuple(
    D4Element(r=i % 4, m=i // 4) for i in range(8)
)


def _canonical_marker(size: int = 8) -> np.ndarray:
    """Maly, w pelni ASYMETRYCZNY wzor — kazdy z 8 elementow D4 daje inny obraz.

    Uzywany do zbudowania tabliczki grupy z faktycznych transformacji pikseli
    (samo-weryfikacja zamiast recznej algebry D4).
    """
    a = np.arange(size * size, dtype=np.int32).reshape(size, size)
    # dodatkowe zerwanie symetrii ukosnej:
    a = a * 2 + (np.tri(size, dtype=np.int32) * 1)
    return a


def _match_index(img: np.ndarray, gallery: list[np.ndarray]) -> int:
    for i, g in enumerate(gallery):
        if g.shape == img.shape and np.array_equal(g, img):
            return i
    raise ValueError("orbita D4 niespojna — obraz spoza galerii 8 elementow")


def _build_cayley() -> np.ndarray:
    """CAYLEY[g, k] = indeks klasy po nalozeniu elementu g na crop klasy k.

    Budowane z pikseli: galeria = {D4[j].apply(marker)}; dla kazdej pary
    (g, k) liczymy D4[g].apply(D4[k].apply(marker)) i szukamy w galerii.
    """
    marker = _canonical_marker()
    gallery = [D4[j].apply_image(marker) for j in range(8)]
    table = np.zeros((8, 8), dtype=np.int64)
    for g in range(8):
        for k in range(8):
            composed = D4[g].apply_image(gallery[k])
            table[g, k] = _match_index(composed, gallery)
    return table


CAYLEY: np.ndarray = _build_cayley()


def compose(g: int, k: int) -> int:
    """Klasa wynikowa: transform g nalozony na crop klasy k."""
    return int(CAYLEY[g, k])


# ---------------------------------------------------------------------------
# Binaryzacja / dopasowanie eksemplarzy
# ---------------------------------------------------------------------------

def _to_gray(img: np.ndarray) -> np.ndarray:
    if img.ndim == 3:
        img = img[..., :3].mean(axis=2)
    return img.astype(np.float32)


def binarize(img: np.ndarray, thresh: float | None = None) -> np.ndarray:
    """Tusz=1, tlo=0. Prog: podany albo srodek zakresu (schemat = wysoki kontrast)."""
    g = _to_gray(img)
    if thresh is None:
        lo, hi = float(g.min()), float(g.max())
        thresh = (lo + hi) / 2.0
    return (g < thresh).astype(np.float32)  # ciemny tusz -> 1


def _resize_bin(img: np.ndarray, size: int) -> np.ndarray:
    from PIL import Image

    b = binarize(img)
    im = Image.fromarray((b * 255).astype(np.uint8))
    im = im.resize((size, size), Image.NEAREST)
    return (np.asarray(im, dtype=np.float32) / 255.0 >= 0.5).astype(np.float32)


def _ncc(a: np.ndarray, b: np.ndarray) -> float:
    """Znormalizowana korelacja dwoch binarnych masek tego samego rozmiaru."""
    av, bv = a.ravel() - a.mean(), b.ravel() - b.mean()
    da, db = np.linalg.norm(av), np.linalg.norm(bv)
    if da == 0 or db == 0:
        return -1.0
    return float(np.dot(av, bv) / (da * db))


def classify_crop(
    crop: np.ndarray,
    templates: list[np.ndarray],
    size: int = 48,
) -> tuple[int, float]:
    """Przypisz realny crop mostka do 1 z 8 klas przez dopasowanie do eksemplarzy.

    `templates` — 8 czystych cropow (po jednym na klase, kolejnosc = CLASS_NAMES).
    Zwraca (indeks_klasy, score NCC). Rozroznia CHIRALNOSC z pikseli, czego sama
    geometria stubow nie potrafi.
    """
    if len(templates) != 8:
        raise ValueError(f"potrzeba 8 eksemplarzy, jest {len(templates)}")
    tb = [_resize_bin(t, size) for t in templates]
    cb = _resize_bin(crop, size)
    scores = [_ncc(cb, t) for t in tb]
    best = int(np.argmax(scores))
    return best, float(scores[best])


# ---------------------------------------------------------------------------
# Augmentacja D4
# ---------------------------------------------------------------------------

def augment_d4(
    crop: np.ndarray,
    source_class: int,
) -> Iterator[tuple[np.ndarray, int]]:
    """Z jednego realnego cropa klasy `source_class` -> 8 par (obraz, klasa).

    Kazdy element g grupy: obraz = g.apply(crop), klasa = compose(g, source_class).
    Orbita jest pelna i bijektywna -> dokladnie po jednej probce na kazda z 8 klas.
    """
    for g in range(8):
        yield D4[g].apply_image(crop), compose(g, source_class)


def transform_bbox_wh(
    w: float, h: float, elem: D4Element
) -> tuple[float, float]:
    """Zamiana wymiarow bboxa: obroty 90/270 zamieniaja w<->h; lustro nie zmienia."""
    return (h, w) if elem.r in (1, 3) else (w, h)


# ---------------------------------------------------------------------------
# Kontrola jakosci bboxa (asercja eksportu)
# ---------------------------------------------------------------------------

def count_edge_crossings(crop: np.ndarray, border: int = 1) -> int:
    """Ile ciagow tuszu przecina krawedz cropa (stuby terminali).

    Mostek = dokladnie 3. Liczymy spojne segmenty tuszu na obwodzie ramki o
    grubosci `border`. Rozny od 3 -> [SKIP] w eksporcie (bbox za luzny/za ciasny).
    """
    b = binarize(crop)
    h, wdt = b.shape
    if h <= 2 * border or wdt <= 2 * border:
        return 0
    # obwod jako uporzadkowany pierscien pikseli (zewnetrzna ramka)
    top = b[0, :]
    right = b[:, -1]
    bottom = b[-1, ::-1]
    left = b[::-1, 0]
    ring = np.concatenate([top, right[1:], bottom[1:], left[1:-1]])
    if ring.max() == 0:
        return 0
    # licz przejscia 0->1 na pierscieniu cyklicznym
    shifted = np.roll(ring, 1)
    rising = int(np.sum((ring == 1) & (shifted == 0)))
    # przypadek: caly pierscien = 1 (brak przejsc, a jest tusz) -> 1 segment
    return rising if rising > 0 else 1
