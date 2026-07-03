# COWORK_TASK: sync/prompts/005-train-symbols.md

"""Eksport datasetu YOLO z SQLite -> train/val + kopie PNG.

PC ZW: tylko kod + testy (mock/fixture). Pelny eksport (z prawdziwym
data/schemagen.db i data/raw/*.png) uruchamia Filip lokalnie.

Struktura wynikowa (data/labeled/):
    data.yaml
    export-manifest.json
    images/train/<page>.png   images/val/<page>.png
    labels/train/<page>.txt   labels/val/<page>.txt
"""

from __future__ import annotations

import json
import shutil
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import yaml

from backend.db import list_pages, load_annotation
from backend.models.label import LabelRecord
from backend.paths import LABELED, RAW, ROOT, SYMBOL_CLASSES, VAL_PAGES
from labeler.export import find_raw_image, yolo_label_lines
from backend.class_map import (
    build_class_map,
    load_palette_map,
    load_yolo_exclude_classes,
    tag_to_class,
)


def _load_page_images(records: list[LabelRecord], raw_dir: Path) -> dict:
    """page_id -> tablica obrazu (grayscale) dla rekordow z dostepnym PNG."""
    from PIL import Image
    import numpy as np

    out: dict = {}
    for rec in records:
        src = find_raw_image(rec, raw_dir)
        if src is None:
            continue
        try:
            out[rec.page_id] = np.asarray(Image.open(src).convert("L"))
        except Exception:
            continue  # niecztelny/atrapa pliku -> pomin (mostek dla tej strony no-op)
    return out


def maybe_expand_mostek(records: list[LabelRecord], raw_dir: Path) -> dict | None:
    """Przepisz tagi `mostek` -> orientacja (8 klas).

    Priorytet: eksemplarze (jesli sa) -> dopasowanie do 8 wzorcow; inaczej AUTO
    z samych bboxow (kanonikalizacja C4 + 2 rodziny chiralnosci). Zwraca log/diag.
    """
    from train.mostek_tiles import (
        expand_mostek_orientations,
        expand_mostek_orientations_auto,
        load_exemplars,
        load_mostek_config,
    )

    cfg = load_mostek_config()
    images = _load_page_images(records, raw_dir)
    if not images:
        return None
    templates = load_exemplars(ROOT / cfg.get("exemplar_dir", "data/mostek_exemplars"))
    if templates is not None:
        return expand_mostek_orientations(records, images, templates).as_dict()
    return expand_mostek_orientations_auto(records, images).as_dict()


def maybe_write_mostek_tiles(
    train_records: list[LabelRecord],
    out: Path,
    raw_dir: Path,
    class_map: dict[str, int],
) -> int:
    """Syntetyczne kafelki orientacji mostka -> split train. Klasa zrodlowa z tagu
    (`mostek_rXX`), niezaleznie od trybu ekspansji (auto/eksemplarz)."""
    from train.mostek_orient import CLASS_NAMES
    from train.mostek_tiles import (
        build_class_id_map,
        generate_tiles,
        load_mostek_config,
        write_tiles,
    )

    cfg = load_mostek_config()
    tile_cfg = cfg.get("tile", {}) or {}
    size, margin = int(tile_cfg.get("size", 96)), int(tile_cfg.get("margin", 8))
    name_to_idx = {n: i for i, n in enumerate(CLASS_NAMES)}
    images = _load_page_images(train_records, raw_dir)
    id_map = build_class_id_map(class_map)
    written = 0
    for rec in train_records:
        page = images.get(rec.page_id)
        if page is None:
            continue
        boxes, srcs = [], []
        for b in rec.bboxes:
            if b.tag in name_to_idx:
                boxes.append((b.x, b.y, b.width, b.height))
                srcs.append(name_to_idx[b.tag])
        if boxes:
            tiles = generate_tiles(
                page, boxes, src_classes=srcs, tile_size=size, margin=margin
            )
            written += write_tiles(
                tiles,
                out / "images" / "train",
                out / "labels" / "train",
                f"mostek_tile_{rec.page_id}",
                class_id_map=id_map,
            )
    return written


def load_labeled_records() -> list[LabelRecord]:
    """Rekordy z adnotacjami z SQLite (bbox>0, pomijajac strony `test_*`)."""
    records: list[LabelRecord] = []
    for page in list_pages():
        page_id = page["id"]
        if page_id.startswith("test_") or page_id.startswith("test"):
            continue
        data = load_annotation(page_id)
        if not data:
            continue
        record = LabelRecord.model_validate(data)
        if record.bboxes:
            records.append(record)
    return records


def load_val_page_ids() -> frozenset[str]:
    """page_id ze stalym zestawem val (config/val-pages.yaml)."""
    if not VAL_PAGES.exists():
        return frozenset()
    data = yaml.safe_load(VAL_PAGES.read_text(encoding="utf-8")) or {}
    pages = data.get("val_pages") or []
    return frozenset(str(p) for p in pages if p)


def split_train_val(
    records: list[LabelRecord],
    val_ratio: float = 0.2,
    val_page_ids: frozenset[str] | None = None,
) -> tuple[list[LabelRecord], list[LabelRecord]]:
    """Podzial train/val.

    Gdy ``config/val-pages.yaml`` ma wpisy (lub przekazano ``val_page_ids``),
    strony z tej listy ida wylacznie do val; reszta do train.
    W przeciwnym razie: deterministyczny podzial — ostatnie strony po sortowaniu
    ``page_id`` (``val_ratio``).

    Przy <=1 rekordzie ta sama strona trafia do train i val (za malo danych).
    """
    fixed = val_page_ids if val_page_ids is not None else load_val_page_ids()
    if fixed:
        val = [r for r in records if r.page_id in fixed]
        train = [r for r in records if r.page_id not in fixed]
        if train and val:
            return sorted(train, key=lambda r: r.page_id), sorted(
                val, key=lambda r: r.page_id
            )
        # Brak dopasowania (test/fixture lub val bez adnotacji) — fallback ratio.

    ordered = sorted(records, key=lambda r: r.page_id)
    n = len(ordered)
    if n <= 1:
        return ordered, ordered
    n_val = max(1, round(n * val_ratio))
    n_val = min(n_val, n - 1)  # zostaw min. 1 w train
    n_train = n - n_val
    train = ordered[:n_train]
    val = ordered[n_train:]
    return train, val


def _write_split(
    records: list[LabelRecord],
    out: Path,
    split: str,
    class_map: dict[str, int],
    raw_dir: Path,
    palette_map: dict[str, str] | None = None,
) -> int:
    images_dir = out / "images" / split
    labels_dir = out / "labels" / split
    images_dir.mkdir(parents=True, exist_ok=True)
    labels_dir.mkdir(parents=True, exist_ok=True)
    written = 0
    for record in records:
        src = find_raw_image(record, raw_dir)
        if src is None:
            continue  # bez obrazu nie ma sensu tworzyc labela
        shutil.copy2(src, images_dir / f"{record.page_id}{src.suffix}")
        lines = yolo_label_lines(record, class_map, palette_map)
        label_file = labels_dir / f"{record.page_id}.txt"
        label_file.write_text(
            "\n".join(lines) + ("\n" if lines else ""), encoding="utf-8"
        )
        written += 1
    return written


def persist_class_map(class_map: dict[str, int]) -> None:
    """Zapisz wygenerowana liste klas do config/symbol-classes.yaml (zrodlo prawdy)."""
    names = [name for name, _ in sorted(class_map.items(), key=lambda kv: kv[1])]
    SYMBOL_CLASSES.write_text(
        "# AUTO-GENEROWANE przez train/dataset_export.py (z pola `tag` adnotacji).\n"
        "# Nie edytuj recznie — zostanie nadpisane przy kolejnym eksporcie.\n"
        + yaml.dump({"classes": names}, allow_unicode=True, sort_keys=False),
        encoding="utf-8",
    )


def export_dataset(
    output_dir: Path | None = None,
    val_ratio: float = 0.2,
    records: list[LabelRecord] | None = None,
    raw_dir: Path | None = None,
    min_count: int = 1,
    bucket_rare: bool = False,
) -> dict:
    """Zbuduj dataset YOLO multi-class train/val + data.yaml + export-manifest.json.

    Klasy sa wyprowadzane z pola `tag` WSZYSTKICH adnotacji (paleta jako kanon).
    `min_count` — klasy ponizej tego progu trafiaja do `inny` (domyslnie 1 = wszystkie).
    """
    out = output_dir or LABELED
    raw = raw_dir or RAW
    recs = records if records is not None else load_labeled_records()
    # Filar SYMBOLE: tag `mostek` -> orientacja (8 klas) PRZED budowa class_map.
    mostek_log = maybe_expand_mostek(recs, raw)
    palette_map = load_palette_map()
    exclude = load_yolo_exclude_classes()
    class_map, distribution = build_class_map(
        recs, min_count=min_count, bucket_rare=bucket_rare
    )
    dist_all: Counter = Counter()
    for rec in recs:
        for b in rec.bboxes:
            cls = tag_to_class(b.tag, palette_map)
            if cls:
                dist_all[cls] += 1
    contextual_excluded = {c: dist_all[c] for c in exclude if c in dist_all}
    if not class_map:
        class_map = {"element": 0}
    persist_class_map(class_map)

    fixed_val = load_val_page_ids()
    train, val = split_train_val(recs, val_ratio)
    out.mkdir(parents=True, exist_ok=True)
    # Wyczysc stare obrazy/labele (sieroty po przeniesieniu strony train<->val
    # albo po usunieciu strony) — inaczej dataset zbiera smieci.
    for _sub in ("images", "labels"):
        _d = out / _sub
        if _d.exists():
            shutil.rmtree(_d, ignore_errors=True)
    n_train = _write_split(train, out, "train", class_map, raw, palette_map)
    n_val = _write_split(val, out, "val", class_map, raw, palette_map)
    # Syntetyczne kafelki orientacji mostka -> tylko split train (balans klas).
    n_mostek_tiles = maybe_write_mostek_tiles(train, out, raw, class_map)

    data_yaml = {
        "path": str(out.resolve()),
        "train": "images/train",
        "val": "images/val",
        "names": {idx: name for name, idx in class_map.items()},
    }
    yaml_path = out / "data.yaml"
    yaml_path.write_text(yaml.dump(data_yaml, allow_unicode=True), encoding="utf-8")

    manifest = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "classes": {name: idx for name, idx in class_map.items()},
        "val_ratio": val_ratio,
        "fixed_val_pages": sorted(fixed_val) if fixed_val else [],
        "train_pages": [r.page_id for r in train],
        "val_pages": [r.page_id for r in val],
        "train_count": n_train,
        "val_count": n_val,
        "total_bboxes": sum(len(r.bboxes) for r in recs),
        "yolo_bboxes": sum(distribution.values()),
        "contextual_excluded": contextual_excluded,
        "num_classes": len(class_map),
        "mostek_orient": mostek_log,
        "mostek_tiles": n_mostek_tiles,
        "min_count": min_count,
        "excluded_classes": {
            c: n for c, n in distribution.items()
            if c not in class_map and (bucket_rare is False or n < min_count)
        } if not bucket_rare else {},
        "class_distribution": dict(distribution.most_common()),
    }
    manifest_path = out / "export-manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    return {
        "data_yaml": str(yaml_path),
        "manifest": str(manifest_path),
        "train": n_train,
        "val": n_val,
        "classes": len(class_map),
    }


def _cli() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Eksport datasetu YOLO multi-class.")
    parser.add_argument("--min-count", type=int, default=1,
                        help="klasy ponizej progu sa wykluczane (domyslnie 1 = wszystkie)")
    parser.add_argument("--val-ratio", type=float, default=0.2)
    parser.add_argument("--bucket-rare", action="store_true",
                        help="zamiast wykluczac, wrzuc rzadkie klasy do 'inny'")
    args = parser.parse_args()
    summary = export_dataset(
        val_ratio=args.val_ratio,
        min_count=args.min_count,
        bucket_rare=args.bucket_rare,
    )
    print(
        f"Dataset: train={summary['train']} val={summary['val']} "
        f"klasy={summary['classes']} -> {summary['data_yaml']}"
    )


if __name__ == "__main__":
    _cli()
