# COWORK_TASK: sync/prompts/012-mostek-orientacja.md
"""Kafelki syntetyczne + ekspansja orientacji mostka (integracja z eksportem).

Detektor 8-klasowy zwraca orientacje. Pipeline eksportu dziala na CALYCH stronach
— augmentacja D4 wchodzi jako male obrazy (kafelki), nie przez obrot stron.

Zrodlo orientacji (dwa tryby, auto ma priorytet gdy brak eksemplarzy):
  A) AUTO z bboxow (domyslny) — orientacje wyprowadzamy z samych oznaczonych
     cropow mostka (assign_orientations_auto, kanonikalizacja C4 + 2 rodziny
     chiralnosci). Zero recznych eksemplarzy.
  B) EKSEMPLARZE — 8 czystych cropow w data/mostek_exemplars/ (opcjonalny
     override, gdy auto myli warianty rysunku).

Oba tryby przepisuja tag `mostek` -> `mostek_rXX` PRZED build_class_map, wiec
reszta pipeline'u (class_map, yolo_label_lines) dziala bez zmian. Picker labelera
bez zmian. Niepewne / bbox != 3 stuby -> tag zostaje `mostek` + log.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

from train.mostek_orient import (
    CLASS_NAMES,
    D4,
    assign_orientations_auto,
    augment_d4,
    classify_crop,
    count_edge_crossings,
)

MIN_SCORE = 0.55  # prog NCC (tryb eksemplarzy) — ponizej: orientacja niepewna
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
    resolved: dict = field(default_factory=dict)  # klasa -> licznik
    skipped_crossings: int = 0
    skipped_lowscore: int = 0
    no_image: int = 0
    tiles: int = 0
    mode: str = ""
    families: int = 0

    def as_dict(self) -> dict:
        return {
            "mode": self.mode,
            "families": self.families,
            "resolved": self.resolved,
            "skipped_crossings": self.skipped_crossings,
            "skipped_lowscore": self.skipped_lowscore,
            "no_image": self.no_image,
            "tiles": self.tiles,
        }


def _find_exemplar(exemplar_dir: Path, name: str):
    from PIL import Image

    for ext in (".png", ".jpg", ".jpeg"):
        p = Path(exemplar_dir) / f"{name}{ext}"
        if p.exists():
            return np.asarray(Image.open(p).convert("L"))
    return None


def _orbit_from_base(r0: np.ndarray, m0: np.ndarray) -> list:
    """8 eksemplarzy z 2 baz: rot90(r0,k) dla r-family, rot90(m0,k) dla m-family
    (kolejnosc = CLASS_NAMES, indeks = m*4 + r)."""
    out = []
    for m in (0, 1):
        base = r0 if m == 0 else m0
        for r in range(4):
            out.append(np.ascontiguousarray(np.rot90(base, r)))
    return out


def load_exemplars(exemplar_dir: Path) -> "list[np.ndarray] | None":
    """Eksemplarze (kolejnosc CLASS_NAMES). Priorytet:
      1) komplet 8 plikow (mostek_r0..mostek_m270),
      2) mostek_r0 + mostek_m0 -> generuj 8 przez D4 (rekomendowane, 2 cropy),
      3) sam mostek_r0 -> m0 = lustro(r0), generuj 8 (1 crop).
    Brak -> None (tryb auto)."""
    if not exemplar_dir or not Path(exemplar_dir).exists():
        return None
    full = [_find_exemplar(exemplar_dir, n) for n in CLASS_NAMES]
    if all(x is not None for x in full):
        return full
    r0 = _find_exemplar(exemplar_dir, "mostek_r0")
    if r0 is None:
        return None
    m0 = _find_exemplar(exemplar_dir, "mostek_m0")
    if m0 is None:
        m0 = np.fliplr(r0)
    return _orbit_from_base(r0, m0)


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
    templates: list,
) -> tuple:
    """Tryb eksemplarzy: crop -> (nazwa, score, liczba_stubow). ZAWSZE najlepsza
    klasa (argmax NCC) — nie gubimy mostkow. Niska pewnosc / zle stuby raportowane
    w logu, ale przypisanie i tak nastepuje (D4-kafelki dominuja w treningu)."""
    crossings = count_edge_crossings(crop)
    idx, score = classify_crop(crop, templates)
    return CLASS_NAMES[idx], score, crossings


def _iter_mostek_bboxes(records, images_by_page, log):
    """Wspolne: iteruj (rec, bbox, crop) dla tagow `mostek` z dostepnym obrazem."""
    for rec in records:
        page = images_by_page.get(rec.page_id)
        for b in rec.bboxes:
            if b.tag.strip().lower() != MOSTEK_TAG:
                continue
            if page is None:
                log.no_image += 1
                continue
            yield rec, b, crop_bbox(page, b.x, b.y, b.width, b.height)


def expand_mostek_orientations(records, images_by_page, templates, log=None):
    """Tryb EKSEMPLARZE: tag `mostek` -> `mostek_rXX` przez dopasowanie do 8 wzorcow."""
    log = log or MostekLog()
    log.mode = "exemplar"
    for _rec, b, crop in _iter_mostek_bboxes(records, images_by_page, log):
        if crop.size == 0:
            log.no_image += 1
            continue
        name, score, crossings = resolve_orientation(crop, templates)
        if crossings != 3:
            log.skipped_crossings += 1   # tylko diagnostyka (nie odrzuca)
        if score < MIN_SCORE:
            log.skipped_lowscore += 1    # niska pewnosc (nadal przypisane)
        b.tag = name
        log.resolved[name] = log.resolved.get(name, 0) + 1
    return log


def expand_mostek_orientations_auto(records, images_by_page, size=48, log=None):
    """Tryb AUTO: orientacje wyprowadzone z samych bboxow (bez eksemplarzy).

    Do klasteryzacji ida tylko cropy z DOKLADNIE 3 stubami (czyste bboxy);
    reszta -> tag zostaje `mostek` + log skip.
    """
    log = log or MostekLog()
    log.mode = "auto"
    good = []  # (bbox, crop)
    for _rec, b, crop in _iter_mostek_bboxes(records, images_by_page, log):
        if crop.size == 0:
            log.no_image += 1
            continue
        # bramka 3-stubow tylko DIAGNOSTYCZNIE (nie odrzuca) — klasteryzacja
        # orientacji dziala niezaleznie od dokladnej ciasnosci bboxa.
        if count_edge_crossings(crop) != 3:
            log.skipped_crossings += 1
        good.append((b, crop))
    if not good:
        return log
    names, diag = assign_orientations_auto([c for _b, c in good], size=size)
    log.families = diag.get("families", 0)
    for (b, _crop), name in zip(good, names):
        if name is None:
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
    templates: "list | None" = None,
    src_classes: "list | None" = None,
    tile_size: int = 96,
    margin: int = 8,
    log=None,
) -> list:
    """Dla kazdego realnego mostka -> 8 kafelkow D4.

    Zrodlo klasy zrodlowej: `src_classes[i]` (indeks 0..7, np. z tagu) albo
    dopasowanie do `templates`. Zwraca (obraz_kafelka, indeks_klasy, bbox_norm).
    """
    log = log or MostekLog()
    out: list = []
    for i, (x, y, w, h) in enumerate(mostek_bboxes):
        crop = crop_bbox(page, x, y, w, h)
        if src_classes is not None:
            src_idx = src_classes[i]
        elif templates is not None:
            name, _s, crossings = resolve_orientation(crop, templates)
            if name is None:
                if crossings != 3:
                    log.skipped_crossings += 1
                else:
                    log.skipped_lowscore += 1
                continue
            src_idx = CLASS_NAMES.index(name)
        else:
            continue
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
                    Image.fromarray(gray.astype(np.uint8)).resize((nw, nh), Image.NEAREST)
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


def write_tiles(tiles, images_dir: Path, labels_dir: Path, prefix: str, class_id_map=None) -> int:
    """Zapisz kafelki jako obraz+label YOLO (jedna linia). Zwraca liczbe."""
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
    return {i: class_map[name] for i, name in enumerate(CLASS_NAMES) if name in class_map}
