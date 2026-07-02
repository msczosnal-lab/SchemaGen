# COWORK_TASK: sync/prompts/012-mostek-orientacja.md
"""Kafelki syntetyczne + ekspansja orientacji mostka (integracja z eksportem).

Strategia (decyzja Filipa 2026-07-02): detektor 8-klasowy zwraca orientacje.
Pipeline eksportu dziala na CALYCH stronach — augmentacja D4 na cropie wchodzi
jako dodatkowe MALE obrazy (kafelki), nie przez obrot stron.

Dwa punkty integracji, oba NIE ruszaja backend/class_map.py:

1. expand_mostek_orientations — przed budowa class_map przepisuje tag mostka
   `mostek` -> `mostek_rXX` (klasyfikacja eksemplarzem z pikseli strony). Dalej
   caly pipeline dziala bez zmian. Niepewne (stuby != 3 albo score < prog) ->
   tag zostaje `mostek` + wpis w logu.

2. generate_tiles / write_tiles — z realnych cropow generuje 8 orientacji D4 na
   tle probkowanym ze strony, jako extra obrazy train (balans klas).

Eksemplarze: 8 czystych cropow w data/mostek_exemplars/ (nazwa pliku = nazwa
klasy). Brak kompletu -> modul no-op (degradacja do pojedynczej klasy `mostek`).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

from train.mostek_orient import (
    CLASS_NAMES,
    D4,
    augment_d4,
    classify_crop,
    count_edge_crossings,
)

MIN_SCORE = 0.55  # prog NCC — ponizej: orientacja niepewna -> generyczny mostek
MOSTEK_TAG = "mostek"


def load_mostek_config() -> dict:
    """Wczytaj config/mostek-orient.yaml (parametry ekspansji + kafelkow)."""
    import yaml

    from backend.paths import CONFIG

    path = CONFIG / "mostek-orient.yaml"
    if not path.exists():
        return {}
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


@dataclass
class MostekLog:
    resolved: dict[str, int] = field(default_factory=dict)  # klasa -> licznik
    skipped_crossings: int = 0
    skipped_lowscore: int = 0
    no_image: int = 0
    tiles: int = 0

    def as_dict(self) -> dict:
        return {
            "resolved": self.resolved,
            "skipped_crossings": self.skipped_crossings,
            "skipped_lowscore": self.skipped_lowscore,
            "no_image": self.no_image,
            "tiles": self.tiles,
        }


def load_exemplars(exemplar_dir: Path) -> list[np.ndarray] | None:
    """8 eksemplarzy (kolejnosc CLASS_NAMES). Brak kompletu -> None (no-op)."""
    if not exemplar_dir or not Path(exemplar_dir).exists():
        return None
    from PIL import Image

    out: list[np.ndarray] = []
    for name in CLASS_NAMES:
        hit = None
        for ext in (".png", ".jpg", ".jpeg"):
            p = Path(exemplar_dir) / f"{name}{ext}"
            if p.exists():
                hit = p
                break
        if hit is None:
            return None  # niepelny komplet -> bezpieczny no-op
        out.append(np.asarray(Image.open(hit).convert("L")))
    return out


def crop_bbox(page: np.ndarray, x: float, y: float, w: float, h: float) -> np.ndarray:
    """Wytnij crop (piksele). x,y,w,h w skali obrazu (jak BboxAnnotation)."""
    H, W = page.shape[:2]
    x0 = max(0, int(round(x)))
    y0 = max(0, int(round(y)))
    x1 = min(W, int(round(x + w)))
    y1 = min(H, int(round(y + h)))
    return page[y0:y1, x0:x1]


def resolve_orientation(
    crop: np.ndarray,
    templates: list[np.ndarray],
) -> tuple[str | None, float, int]:
    """Crop -> (nazwa_klasy | None, score, liczba_stubow).

    None gdy stuby != 3 (bbox zly) albo score < MIN_SCORE (orientacja niepewna).
    """
    crossings = count_edge_crossings(crop)
    if crossings != 3:
        return None, 0.0, crossings
    idx, score = classify_crop(crop, templates)
    if score < MIN_SCORE:
        return None, score, crossings
    return CLASS_NAMES[idx], score, crossings


def expand_mostek_orientations(
    records: list,
    images_by_page: dict,
    templates: list[np.ndarray],
    log: "MostekLog | None" = None,
) -> "MostekLog":
    """In-place: tag `mostek` -> `mostek_rXX` na podstawie cropa strony.

    Niepewne -> tag zostaje `mostek` (trening generyczny) + log. Zwraca log.
    """
    log = log or MostekLog()
    for rec in records:
        page = images_by_page.get(rec.page_id)
        for b in rec.bboxes:
            if b.tag.strip().lower() != MOSTEK_TAG:
                continue
            if page is None:
                log.no_image += 1
                continue
            crop = crop_bbox(page, b.x, b.y, b.width, b.height)
            name, _score, crossings = resolve_orientation(crop, templates)
            if name is None:
                if crossings != 3:
                    log.skipped_crossings += 1
                else:
                    log.skipped_lowscore += 1
                continue
            b.tag = name
            log.resolved[name] = log.resolved.get(name, 0) + 1
    return log


def _sample_background(page: np.ndarray, size: int) -> np.ndarray:
    """Jasne tlo o wartosci = mediana strony (przyblizenie tla schematu)."""
    val = int(np.median(page)) if page.size else 255
    return np.full((size, size), val, dtype=np.uint8)


def generate_tiles(
    page: np.ndarray,
    mostek_bboxes: list,
    templates: list[np.ndarray],
    tile_size: int = 96,
    margin: int = 8,
    log: "MostekLog | None" = None,
) -> list:
    """Dla kazdego realnego mostka -> 8 kafelkow D4.

    Zwraca liste (obraz_kafelka, indeks_klasy, bbox_norm [cx,cy,w,h]).
    """
    log = log or MostekLog()
    out: list = []
    for (x, y, w, h) in mostek_bboxes:
        crop = crop_bbox(page, x, y, w, h)
        name, _s, crossings = resolve_orientation(crop, templates)
        if name is None:
            if crossings != 3:
                log.skipped_crossings += 1
            else:
                log.skipped_lowscore += 1
            continue
        src_idx = CLASS_NAMES.index(name)
        for timg, cls in augment_d4(crop, src_idx):
            tile = _sample_background(page, tile_size)
            th, tw = timg.shape[:2]
            max_in = tile_size - 2 * margin
            gray = timg if timg.ndim == 2 else timg[..., :3].mean(axis=2)
            if th > max_in or tw > max_in:
                from PIL import Image

                scale = max_in / max(th, tw)
                nh, nw = max(1, int(th * scale)), max(1, int(tw * scale))
                gray = np.asarray(
                    Image.fromarray(gray.astype(np.uint8)).resize(
                        (nw, nh), Image.NEAREST
                    )
                )
                th, tw = nh, nw
            oy = (tile_size - th) // 2
            ox = (tile_size - tw) // 2
            tile[oy : oy + th, ox : ox + tw] = gray.astype(np.uint8)
            cx = (ox + tw / 2) / tile_size
            cy = (oy + th / 2) / tile_size
            out.append((tile, cls, (cx, cy, tw / tile_size, th / tile_size)))
            log.tiles += 1
    return out


def write_tiles(
    tiles: list,
    images_dir: Path,
    labels_dir: Path,
    prefix: str,
    class_id_map: "dict[int, int] | None" = None,
) -> int:
    """Zapisz kafelki jako obraz+label YOLO (jedna linia). Zwraca liczbe.

    class_id_map mapuje indeks orbity D4 (0..7 wg CLASS_NAMES) na id klasy w
    datasecie (class_map). Brak -> tozsamosc (test/fixture).
    """
    from PIL import Image

    images_dir.mkdir(parents=True, exist_ok=True)
    labels_dir.mkdir(parents=True, exist_ok=True)
    for i, (img, cls, (cx, cy, bw, bh)) in enumerate(tiles):
        out_cls = class_id_map.get(cls, cls) if class_id_map else cls
        stem = f"{prefix}_{i:05d}"
        Image.fromarray(img).save(images_dir / f"{stem}.png")
        (labels_dir / f"{stem}.txt").write_text(
            f"{out_cls} {cx:.6f} {cy:.6f} {bw:.6f} {bh:.6f}\n", encoding="utf-8"
        )
    return len(tiles)


def build_class_id_map(class_map: dict) -> dict:
    """Orbita D4 (indeks 0..7 wg CLASS_NAMES) -> id klasy w datasecie."""
    return {
        i: class_map[name]
        for i, name in enumerate(CLASS_NAMES)
        if name in class_map
    }
